# Official postgres image (ships the pgdg apt repo) + PostGIS + pgvector.
# Multi-arch, so it runs natively on Apple Silicon and amd64 servers.
FROM postgres:17-bookworm
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      postgresql-17-postgis-3 \
      postgresql-17-pgvector \
 && rm -rf /var/lib/apt/lists/*
