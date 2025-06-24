"""Create mobile_sites table

Revision ID: 63ac31838f8f
Revises: 
Create Date: 2025-06-21 14:05:09.365132

"""
import uuid

import sqlalchemy as sa
from geoalchemy2 import Geometry
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = '63ac31838f8f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create mobile_sites table with PostGIS geometry
    op.create_table('mobile_sites',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('operator', sa.String(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('geom', Geometry('POINT', srid=4326), nullable=False),  # WGS84 for GPS coordinates
        sa.Column('has_2g', sa.Boolean(), nullable=False, default=False),
        sa.Column('has_3g', sa.Boolean(), nullable=False, default=False),
        sa.Column('has_4g', sa.Boolean(), nullable=False, default=False),
    )

    # Create spatial index on geometry column (only if it doesn't exist)
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    existing_indexes = [idx['name'] for idx in inspector.get_indexes('mobile_sites')]

    if 'idx_mobile_sites_geom' not in existing_indexes:
        op.create_index('idx_mobile_sites_geom', 'mobile_sites', ['geom'], postgresql_using='gist')


def downgrade() -> None:
    # Drop index
    op.drop_index(op.f('idx_mobile_sites_geom'), table_name='mobile_sites')

    # Drop table
    op.drop_table('mobile_sites')
