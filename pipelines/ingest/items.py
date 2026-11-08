"""RawItem: what every connector yields, before normalisation."""
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class RawItem:
    source_id: str
    title: str
    url: str
    published: datetime
    summary: str = ""
    language: str = "en"
    country: str | None = None  # ISO2 if the source provides it structurally
    event_type: str | None = None  # set when the source types events structurally (bypasses classify)
    location: tuple[float, float] | None = None  # (lat, lon) if structural, settlement-level only
    extra: dict = field(default_factory=dict)
