"""location_precision: exact vs city-level placement

Adds events.location_precision ("exact" | "city", NULL when no geometry).
Existing rows with a geometry are backfilled as "exact" — they predate the
gazetteer and could only have come from a source; fail-closed for the
exposure gate either way.

Revision ID: c4a91e72d8b3
Revises: 8f3d2c41b7e9
Create Date: 2026-11-02
"""
from alembic import op
import sqlalchemy as sa

revision = 'c4a91e72d8b3'
down_revision = '8f3d2c41b7e9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('events', sa.Column('location_precision', sa.String(length=12), nullable=True))
    op.execute("UPDATE events SET location_precision = 'exact' WHERE geom IS NOT NULL")


def downgrade() -> None:
    op.drop_column('events', 'location_precision')
