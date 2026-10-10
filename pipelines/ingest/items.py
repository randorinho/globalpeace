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
    extra: dict = field(default_factory=dict)
