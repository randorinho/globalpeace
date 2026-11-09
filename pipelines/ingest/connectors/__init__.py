from .reliefweb import fetch_reliefweb
from .rss import fetch_rss
from .ucdp import fetch_ucdp, finalize_ucdp

CONNECTORS = {
    "reliefweb": fetch_reliefweb,
    "rss": fetch_rss,
    "ucdp": fetch_ucdp,
}

# Called by the runner after a source completes with zero errors (never on
# dry runs) — for connectors with walk-once markers or similar commit points.
FINALIZERS = {
    "ucdp": finalize_ucdp,
}
