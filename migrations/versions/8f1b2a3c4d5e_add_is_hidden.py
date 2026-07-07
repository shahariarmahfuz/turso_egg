"""add is_hidden

Revision ID: 8f1b2a3c4d5e
Revises: f4e69e2cc117
Create Date: 2026-07-07 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8f1b2a3c4d5e'
down_revision = 'f4e69e2cc117'
branch_labels = None
depends_on = None

def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    if 'admin' not in inspector.get_table_names():
        return
        
    existing_columns = [c['name'] for c in inspector.get_columns('admin')]
    if 'is_hidden' not in existing_columns:
        with op.batch_alter_table('admin', schema=None) as batch_op:
            batch_op.add_column(sa.Column('is_hidden', sa.Boolean(), server_default='0', nullable=False))

def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    if 'admin' not in inspector.get_table_names():
        return
        
    existing_columns = [c['name'] for c in inspector.get_columns('admin')]
    if 'is_hidden' in existing_columns:
        with op.batch_alter_table('admin', schema=None) as batch_op:
            batch_op.drop_column('is_hidden')
