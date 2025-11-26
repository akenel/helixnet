"""Add POS models (Product, Transaction, LineItem)

Revision ID: 001_pos_models
Revises:
Create Date: 2025-11-26 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_pos_models'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create products table
    op.create_table(
        'products',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('barcode', sa.String(100), nullable=True),
        sa.Column('sku', sa.String(100), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('price', sa.Numeric(10, 2), nullable=False),
        sa.Column('cost', sa.Numeric(10, 2), nullable=True),
        sa.Column('stock_quantity', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('stock_alert_threshold', sa.Integer(), nullable=True),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('tags', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_age_restricted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('vending_compatible', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('vending_slot', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('barcode'),
        sa.UniqueConstraint('sku')
    )
    op.create_index('ix_products_id', 'products', ['id'])
    op.create_index('ix_products_barcode', 'products', ['barcode'])
    op.create_index('ix_products_sku', 'products', ['sku'])

    # Create transactions table
    op.create_table(
        'transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('transaction_number', sa.String(50), nullable=False),
        sa.Column('cashier_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.Enum('OPEN', 'PENDING', 'COMPLETED', 'CANCELLED', 'REFUNDED', name='transactionstatus'), nullable=False, server_default='OPEN'),
        sa.Column('payment_method', sa.Enum('CASH', 'VISA', 'DEBIT', 'TWINT', 'CRYPTO', 'OTHER', name='paymentmethod'), nullable=True),
        sa.Column('subtotal', sa.Numeric(10, 2), nullable=False, server_default='0.00'),
        sa.Column('discount_amount', sa.Numeric(10, 2), nullable=False, server_default='0.00'),
        sa.Column('tax_amount', sa.Numeric(10, 2), nullable=False, server_default='0.00'),
        sa.Column('total', sa.Numeric(10, 2), nullable=False, server_default='0.00'),
        sa.Column('amount_tendered', sa.Numeric(10, 2), nullable=True),
        sa.Column('change_given', sa.Numeric(10, 2), nullable=True),
        sa.Column('receipt_number', sa.String(100), nullable=True),
        sa.Column('receipt_pdf_url', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['cashier_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['customer_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('transaction_number')
    )
    op.create_index('ix_transactions_id', 'transactions', ['id'])
    op.create_index('ix_transactions_transaction_number', 'transactions', ['transaction_number'])

    # Create line_items table
    op.create_table(
        'line_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('transaction_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('unit_price', sa.Numeric(10, 2), nullable=False),
        sa.Column('discount_percent', sa.Numeric(5, 2), nullable=False, server_default='0.00'),
        sa.Column('discount_amount', sa.Numeric(10, 2), nullable=False, server_default='0.00'),
        sa.Column('line_total', sa.Numeric(10, 2), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_line_items_id', 'line_items', ['id'])


def downgrade() -> None:
    op.drop_index('ix_line_items_id', 'line_items')
    op.drop_table('line_items')
    op.drop_index('ix_transactions_transaction_number', 'transactions')
    op.drop_index('ix_transactions_id', 'transactions')
    op.drop_table('transactions')
    op.drop_index('ix_products_sku', 'products')
    op.drop_index('ix_products_barcode', 'products')
    op.drop_index('ix_products_id', 'products')
    op.drop_table('products')
    op.execute('DROP TYPE IF EXISTS paymentmethod')
    op.execute('DROP TYPE IF EXISTS transactionstatus')
