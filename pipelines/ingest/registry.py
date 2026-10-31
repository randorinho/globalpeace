from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class SourceConfig:
    id: str
    kind: str
    confidence: float
    country: str | None = None
    rw_country: str | None = None
    url: str | None = None
    limit: int = 20


@dataclass
class Registry:
    sources: list[SourceConfig]

    def get(self, source_id: str) -> SourceConfig:
        for s in self.sources:
            if s.id == source_id:
                return s
        raise KeyError(f"unknown source: {source_id}")


def load_registry(path: Path | None = None) -> Registry:
    path = path or Path(__file__).parent / "sources.yaml"
    raw = yaml.safe_load(path.read_text())
    return Registry(sources=[SourceConfig(**s) for s in raw["sources"]])
