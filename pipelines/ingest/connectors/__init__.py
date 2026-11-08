from .reliefweb import fetch_reliefweb
from .rss import fetch_rss
from .ucdp import fetch_ucdp

CONNECTORS = {
    "reliefweb": fetch_reliefweb,
    "rss": fetch_rss,
    "ucdp": fetch_ucdp,
}
