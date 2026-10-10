"""Load transfers into the actor graph (Neo4j).

(:Country {name, iso2?}) -[:SUPPLIED {...}]-> (:Country)

Every edge carries source attribution, information_type and confidence per
docs/DATA_MODEL.md. Re-loading wipes prior edges of the same source so the
graph mirrors the latest register export.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone

from neo4j import GraphDatabase

from .loader import Transfer

NEO4J_URL = os.environ.get("GPAI_NEO4J_URL", "bolt://localhost:7687")
NEO4J_AUTH = (os.environ.get("GPAI_NEO4J_USER", "neo4j"),
              os.environ.get("GPAI_NEO4J_PASSWORD", "gpai-dev-password"))

ISO2 = {
    "sudan": "SD", "chad": "TD", "south sudan": "SS",
    "dr congo": "CD", "democratic republic of the congo": "CD", "haiti": "HT",
}


def load(transfers: list[Transfer], source: str = "SIPRI Arms Transfers Database",
         wipe_source: bool = True) -> int:
    loaded_at = datetime.now(timezone.utc).isoformat()
    with GraphDatabase.driver(NEO4J_URL, auth=NEO4J_AUTH) as driver:
        driver.verify_connectivity()
        with driver.session() as session:
            if wipe_source:
                session.run("MATCH ()-[t:SUPPLIED {source: $source}]->() DELETE t",
                            source=source)
            for t in transfers:
                session.run(
                    """
                    MERGE (s:Country {name: $supplier})
                      ON CREATE SET s.iso2 = $s_iso2
                    MERGE (r:Country {name: $recipient})
                      ON CREATE SET r.iso2 = $r_iso2
                    CREATE (s)-[:SUPPLIED {
                      designation: $designation, description: $description,
                      category: $category, order_year: $order_year,
                      delivery_year: $delivery_year,
                      numbers_delivered: $numbers_delivered, tiv_total: $tiv_total,
                      status: $status, information_type: 'observed_fact',
                      confidence: $confidence, source: $source, loaded_at: $loaded_at
                    }]->(r)
                    """,
                    supplier=t.supplier, recipient=t.recipient,
                    s_iso2=ISO2.get(t.supplier.lower()), r_iso2=ISO2.get(t.recipient.lower()),
                    designation=t.designation, description=t.description,
                    category=t.category, order_year=t.order_year,
                    delivery_year=t.delivery_year, numbers_delivered=t.numbers_delivered,
                    tiv_total=t.tiv_total, status=t.status,
                    confidence=0.6 if t.estimated else 0.8,
                    source=source, loaded_at=loaded_at,
                )
            n = session.run("MATCH ()-[t:SUPPLIED {source: $source}]->() RETURN count(t) AS n",
                            source=source).single()["n"]
    return n
