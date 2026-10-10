# pipelines

Ingestion connectors (RSS/Atom, REST/GraphQL APIs, files, webhooks), normalisation, machine translation, and verification stages.

Planned stack: Python, Kafka or Redis Streams, orchestrated with Airflow/Dagster/Prefect. Each connector is independent and event-driven.
