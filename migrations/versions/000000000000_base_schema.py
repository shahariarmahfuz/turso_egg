"""Base schema creation

Revision ID: 000000000000
Revises: 
Create Date: 2026-07-07 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from flask import current_app
from models import db

# revision identifiers, used by Alembic.
revision = '000000000000'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()
    
    # If the database is completely empty (no businesses table), we create all tables.
    if 'businesses' not in existing_tables:
        db.metadata.create_all(bind=bind)


def downgrade():
    pass
