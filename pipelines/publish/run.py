"""Snapshot publisher — dark-origin phase 1 (docs/DARK_ORIGIN.md).

Publishes every public API payload to the R2 bucket the edge worker serves,
so visitor reads never have to reach the origin. Strictly outbound: the
publisher queries the origin on localhost and PUTs to R2.

    python -m publish.run              # incremental publish
    python -m publish.run --dry-run    # plan only, write nothing
    python -m publish.run --verify     # byte-compare origin payloads vs R2

Upload backends, in preference order:
  1. S3 API via boto3 — R2_ENDPOINT, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY
     (and optional R2_BUCKET) in infra/.env. The server-ready path.
  2. wrangler CLI (one call per object) — hosts with an authenticated
     wrangler but no S3 keys. Slow but fine at current object counts.
Neither available: log and exit 0 — the pipeline must not fail while the
edge cutover is pending (same stance as scripts/backup.sh without rclone).

Incremental: .state/snapshots.json maps key -> sha256 of the last upload;
only changed keys are PUT. Keys that leave the produced set are deleted
(publish/remove symmetry) — but never after a partial production run, so a
flaky origin endpoint can't wipe healthy snapshots.
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).parent.parent))
from common import API_URL, api_headers  # noqa: E402

STATE = Path(__file__).parent.parent / ".state" / "snapshots.json"
BUCKET = os.environ.get("R2_BUCKET", "gpai-public")
GATEWAY_DIR = Path(__file__).parent.parent.parent / "edge" / "gateway"
JSON_CT = "application/json"

# key -> (origin path, content type). The edge worker's snapshotKey() mapping
# (edge/gateway/src/index.ts) must mirror this table.
STATIC_SNAPSHOTS: list[tuple[str, str, str]] = [
    ("public/events.json", "/public/events?limit=2000", JSON_CT),
    ("public/events.geojson", "/public/events.geojson", "application/geo+json"),
    ("public/events.csv", "/public/events.csv", "text/csv; charset=utf-8"),
    ("public/arms-transfers.json", "/public/arms-transfers?limit=1000", JSON_CT),
    ("public/hra/position.json", "/public/hra/position", JSON_CT),
    ("public/hra/positions.json", "/public/hra/positions", JSON_CT),
    ("public/solutions.json", "/public/solutions", JSON_CT),
    ("public/solutions/history.json", "/public/solutions/history", JSON_CT),
]


# ---- upload backends -------------------------------------------------------

class S3Backend:
    name = "s3"

    def __init__(self) -> None:
        import boto3  # dependency present, imported lazily to keep --dry-run light

        self.client = boto3.client(
            "s3",
            endpoint_url=os.environ["R2_ENDPOINT"],
            aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
            region_name="auto",
        )

    def put(self, key: str, body: bytes, content_type: str) -> None:
        self.client.put_object(Bucket=BUCKET, Key=key, Body=body, ContentType=content_type)

    def delete(self, key: str) -> None:
        self.client.delete_object(Bucket=BUCKET, Key=key)

    def get(self, key: str) -> bytes | None:
        try:
            return self.client.get_object(Bucket=BUCKET, Key=key)["Body"].read()
        except self.client.exceptions.NoSuchKey:
            return None


class WranglerBackend:
    name = "wrangler"

    def _run(self, *args: str, check: bool = True) -> subprocess.CompletedProcess:
        proc = subprocess.run(
            ["npx", "wrangler", *args], cwd=GATEWAY_DIR,
            capture_output=True, text=True, timeout=120,
        )
        if check and proc.returncode != 0:
            raise RuntimeError(f"wrangler {' '.join(args[:3])}: {proc.stderr.strip()[-300:]}")
        return proc

    def put(self, key: str, body: bytes, content_type: str) -> None:
        with tempfile.NamedTemporaryFile(suffix=Path(key).suffix) as tmp:
            tmp.write(body)
            tmp.flush()
            self._run("r2", "object", "put", f"{BUCKET}/{key}",
                      "--file", tmp.name, "--content-type", content_type, "--remote")

    def delete(self, key: str) -> None:
        self._run("r2", "object", "delete", f"{BUCKET}/{key}", "--remote")

    def get(self, key: str) -> bytes | None:
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "obj"
            proc = self._run("r2", "object", "get", f"{BUCKET}/{key}",
                             "--file", str(out), "--remote", check=False)
            return out.read_bytes() if proc.returncode == 0 and out.exists() else None


def pick_backend():
    # Kill switch: edge sync (snapshots + contributions drain) belongs to the
    # PRODUCTION origin alone. GPAI_EDGE_SYNC_DISABLED=1 on any other copy
    # (e.g. the reviewer laptop) makes both stages no-ops.
    if os.environ.get("GPAI_EDGE_SYNC_DISABLED", "") not in ("", "0"):
        return None
    if all(os.environ.get(v) for v in ("R2_ENDPOINT", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY")):
        return S3Backend()
    if shutil.which("npx") and (GATEWAY_DIR / "wrangler.jsonc").exists():
        return WranglerBackend()
    return None


# ---- payload production ----------------------------------------------------

def produce() -> tuple[dict[str, tuple[bytes, str]], bool]:
    """Fetch every public payload from the origin. Returns (key -> (bytes,
    content type), complete) — complete is False when any endpoint failed, in
    which case deletions are skipped so healthy snapshots survive flakiness."""
    out: dict[str, tuple[bytes, str]] = {}
    complete = True

    def get(path: str) -> bytes:
        resp = httpx.get(f"{API_URL}{path}", headers=api_headers(), timeout=120)
        resp.raise_for_status()
        return resp.content

    for key, path, ct in STATIC_SNAPSHOTS:
        try:
            out[key] = (get(path), ct)
        except Exception as exc:  # noqa: BLE001 — one flaky endpoint must not kill the publish
            complete = False
            print(f"  SKIP {key}: {exc}", file=sys.stderr)

    events = json.loads(out["public/events.json"][0]) if "public/events.json" in out else []
    for ev in events:
        eid = ev["event_id"]
        try:
            out[f"public/trails/{eid}.json"] = (get(f"/public/events/{eid}/trail"), JSON_CT)
        except Exception as exc:  # noqa: BLE001
            complete = False
            print(f"  SKIP trail {eid}: {exc}", file=sys.stderr)

    # Per-country arms transfers (Country pages query ?country=XX). Only
    # countries with transfers get a key; in phase 3 the worker answers
    # misses with an empty payload instead of falling back to the origin.
    from ingest.countries import ALL_ISO2  # noqa: E402

    for iso2 in sorted(ALL_ISO2):
        try:
            body = get(f"/public/arms-transfers?country={iso2}&limit=200")
            if json.loads(body).get("count"):
                out[f"public/arms-transfers/{iso2}.json"] = (body, JSON_CT)
        except Exception as exc:  # noqa: BLE001
            complete = False
            print(f"  SKIP arms-transfers/{iso2}: {exc}", file=sys.stderr)
            break  # graph down fails all countries alike — don't log 200 lines

    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "events": len(events),
        "keys": len(out) + 1,
        "complete": complete,
    }
    out["public/meta.json"] = (json.dumps(meta, separators=(",", ":")).encode(), JSON_CT)
    return out, complete


# ---- planning (pure; unit-tested) ------------------------------------------

def digest(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def plan(
    produced: dict[str, str], manifest: dict[str, str], complete: bool,
) -> tuple[list[str], list[str]]:
    """(keys to upload, keys to delete). Deletes only keys we once published
    (they're in the manifest), only under public/, and only after a complete
    production run."""
    to_put = [k for k, h in produced.items() if manifest.get(k) != h]
    to_delete = (
        [k for k in manifest if k not in produced and k.startswith("public/")]
        if complete else []
    )
    return to_put, to_delete


def load_manifest() -> dict[str, str]:
    try:
        return json.loads(STATE.read_text())
    except FileNotFoundError:
        return {}


def save_manifest(manifest: dict[str, str]) -> None:
    STATE.parent.mkdir(exist_ok=True)
    STATE.write_text(json.dumps(manifest, indent=0, sort_keys=True))


# ---- entrypoints -----------------------------------------------------------

def publish(dry_run: bool) -> int:
    backend = pick_backend()
    if backend is None and not dry_run:
        print("→ publish skipped: no R2 credentials and no wrangler (see docs/DARK_ORIGIN.md)")
        return 0
    produced, complete = produce()
    manifest = load_manifest()
    hashes = {k: digest(body) for k, (body, _) in produced.items()}
    to_put, to_delete = plan(hashes, manifest, complete)
    if dry_run:
        for k in to_put:
            print(f"  would put    {k}")
        for k in to_delete:
            print(f"  would delete {k}")
        print(json.dumps({"put": len(to_put), "delete": len(to_delete),
                          "unchanged": len(produced) - len(to_put), "complete": complete}))
        return 0
    stats = {"put": 0, "deleted": 0, "unchanged": len(produced) - len(to_put), "error": 0}
    for key in to_put:
        body, ct = produced[key]
        try:
            backend.put(key, body, ct)
            manifest[key] = hashes[key]
            stats["put"] += 1
        except Exception as exc:  # noqa: BLE001 — publish the rest; manifest stays honest
            stats["error"] += 1
            print(f"  ERROR put {key}: {exc}", file=sys.stderr)
    for key in to_delete:
        try:
            backend.delete(key)
            manifest.pop(key, None)
            stats["deleted"] += 1
        except Exception as exc:  # noqa: BLE001
            stats["error"] += 1
            print(f"  ERROR delete {key}: {exc}", file=sys.stderr)
    save_manifest(manifest)
    print(json.dumps({"backend": backend.name, **stats, "complete": complete}))
    return 1 if stats["error"] else 0


def verify() -> int:
    """Phase-1 acceptance: re-fetch every origin payload and byte-compare it
    with the stored object (JSON-value compare as fallback, since list order
    can shift between the publish and verify fetches)."""
    backend = pick_backend()
    if backend is None:
        print("verify needs an R2 backend (credentials or wrangler)")
        return 1
    produced, complete = produce()
    mismatched = missing = ok = 0
    for key, (body, _ct) in sorted(produced.items()):
        if key == "public/meta.json":
            continue  # carries the publish timestamp — never byte-equal
        stored = backend.get(key)
        if stored is None:
            missing += 1
            print(f"  MISSING  {key}")
            continue
        if stored == body:
            ok += 1
            continue
        try:
            if json.loads(stored) == json.loads(body):
                ok += 1
                continue
        except ValueError:
            pass
        mismatched += 1
        print(f"  MISMATCH {key}")
    print(json.dumps({"ok": ok, "missing": missing, "mismatched": mismatched,
                      "complete": complete}))
    return 0 if mismatched == 0 and missing == 0 else 1


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args()
    raise SystemExit(verify() if args.verify else publish(args.dry_run))


if __name__ == "__main__":
    main()
