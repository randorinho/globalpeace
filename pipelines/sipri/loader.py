"""Parse a SIPRI Trade Register CSV export.

Export headers have varied across portal versions (Seller/Supplier,
Buyer/Recipient, ...), and files may carry preamble lines before the header
row — the parser is tolerant of both.
"""
from __future__ import annotations

import csv
import io
from dataclasses import dataclass

HEADER_ALIASES = {
    "supplier": ("supplier", "seller"),
    "recipient": ("recipient", "buyer"),
    "designation": ("designation",),
    "description": ("description", "weapon description"),
    "category": ("armament category", "category"),
    "order_year": ("order date", "year of order", "order year"),
    "delivery_year": ("delivery year", "year(s) of delivery", "delivery year(s)"),
    "numbers_delivered": ("numbers delivered", "number delivered", "no. delivered"),
    "tiv_total": ("sipri tiv of delivered weapons", "sipri tiv for total order", "tiv delivered"),
    "status": ("status",),
}
ESTIMATE_MARKERS = ("order date is estimate", "numbers delivered is estimate",
                    "delivery year is estimate")


@dataclass
class Transfer:
    supplier: str
    recipient: str
    designation: str
    description: str
    category: str
    order_year: str
    delivery_year: str
    numbers_delivered: str
    tiv_total: str
    status: str
    estimated: bool


def _find_header(lines: list[str]) -> int:
    for i, line in enumerate(lines[:30]):
        low = line.lower()
        if ("supplier" in low or "seller" in low) and ("recipient" in low or "buyer" in low):
            return i
    raise ValueError("no SIPRI trade-register header row found (expected supplier/recipient columns)")


def _col(row: dict, key: str) -> str:
    aliases = HEADER_ALIASES[key]
    for k, v in row.items():
        if k and k.strip().lower() in aliases:
            return (v or "").strip()
    return ""


def parse(text: str) -> list[Transfer]:
    lines = text.splitlines()
    start = _find_header(lines)
    reader = csv.DictReader(io.StringIO("\n".join(lines[start:])))
    transfers: list[Transfer] = []
    for row in reader:
        supplier, recipient = _col(row, "supplier"), _col(row, "recipient")
        if not supplier or not recipient:
            continue
        lowered = {(k or "").strip().lower(): (v or "").strip().lower() for k, v in row.items()}
        estimated = any(lowered.get(k, "") in ("1", "yes", "true", "*") for k in ESTIMATE_MARKERS)
        transfers.append(Transfer(
            supplier=supplier, recipient=recipient,
            designation=_col(row, "designation"), description=_col(row, "description"),
            category=_col(row, "category"), order_year=_col(row, "order_year"),
            delivery_year=_col(row, "delivery_year"),
            numbers_delivered=_col(row, "numbers_delivered"),
            tiv_total=_col(row, "tiv_total"), status=_col(row, "status"),
            estimated=estimated,
        ))
    return transfers
