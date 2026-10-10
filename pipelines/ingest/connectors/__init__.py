from .reliefweb import fetch_reliefweb
from .rss import fetch_rss

CONNECTORS = {
    "reliefweb": fetch_reliefweb,
    "rss": fetch_rss,
}
