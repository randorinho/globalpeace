"""primary_source_url: server-side ingest dedupe

Adds events.primary_source_url (first source URL), backfills it from the
source_urls JSON array, clears it on all but the earliest event per URL
(duplicates stay visible, they just lose the dedupe claim), then enforces
uniqueness. NULLs are allowed and repeatable (events without a source URL).

Revision ID: 8f3d2c41b7e9
Revises: 051ac43f513d
Create Date: 2026-10-31
"""
from alembic import op
import sqlalchemy as sa

revision = '8f3d2c41b7e9'
down_revision = '051ac43f513d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('events', sa.Column('primary_source_url', sa.String(length=1000), nullable=True))
    op.execute(
        "UPDATE events SET primary_source_url = source_urls::jsonb ->> 0 "
        "WHERE source_urls IS NOT NULL AND jsonb_array_length(source_urls::jsonb) > 0"
    )
    op.execute(
        """
        WITH ranked AS (
            SELECT event_id,
                   row_number() OVER (
                       PARTITION BY primary_source_url
                       ORDER BY date_time, event_id
                   ) AS rn
            FROM events
            WHERE primary_source_url IS NOT NULL
        )
        UPDATE events SET primary_source_url = NULL
        WHERE event_id IN (SELECT event_id FROM ranked WHERE rn > 1)
        """
    )
    op.create_unique_constraint('uq_events_primary_source_url', 'events', ['primary_source_url'])


def downgrade() -> None:
    op.drop_constraint('uq_events_primary_source_url', 'events', type_='unique')
    op.drop_column('events', 'primary_source_url')
