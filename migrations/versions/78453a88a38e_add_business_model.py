"""Add Business Model

Revision ID: 78453a88a38e
Revises: 
Create Date: 2026-07-03 03:35:31.079098

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '78453a88a38e'
down_revision = '000000000000'
branch_labels = None
depends_on = None


def _table_has_column(inspector, table_name, column_name):
    """Check if a column already exists in a table."""
    columns = [c['name'] for c in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    # List of tables that need business_id added
    tables_needing_business_id = [
        'admin', 'bank_transactions', 'banks', 'cash_ledgers', 'cash_out',
        'customer_collections', 'customer_ledgers', 'customers',
        'expense_heads', 'expenses', 'products', 'purchase_items',
        'purchase_return_items', 'purchase_returns', 'purchases',
        'sale_items', 'sale_return_items', 'sale_returns', 'sales',
        'supplier_ledgers', 'supplier_payments', 'suppliers',
    ]

    for table_name in tables_needing_business_id:
        if table_name not in existing_tables:
            # Table doesn't exist yet; db.create_all() will handle it
            # with the business_id column already defined in the model.
            continue
        if _table_has_column(inspector, table_name, 'business_id'):
            # Column already exists (e.g. db.create_all() ran first).
            continue
        with op.batch_alter_table(table_name, schema=None) as batch_op:
            batch_op.add_column(sa.Column('business_id', sa.Integer(), nullable=True))
            batch_op.create_foreign_key(
                f'fk_{table_name}_business_id',
                'businesses', ['business_id'], ['id'],
            )


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    tables_to_revert = [
        'suppliers', 'supplier_payments', 'supplier_ledgers', 'sales',
        'sale_returns', 'sale_return_items', 'sale_items', 'purchases',
        'purchase_returns', 'purchase_return_items', 'purchase_items',
        'products', 'expenses', 'expense_heads', 'customers',
        'customer_ledgers', 'customer_collections', 'cash_out',
        'cash_ledgers', 'banks', 'bank_transactions', 'admin',
    ]

    for table_name in tables_to_revert:
        if table_name not in existing_tables:
            continue
        if not _table_has_column(inspector, table_name, 'business_id'):
            continue
        with op.batch_alter_table(table_name, schema=None) as batch_op:
            batch_op.drop_constraint(
                f'fk_{table_name}_business_id', type_='foreignkey',
            )
            batch_op.drop_column('business_id')
