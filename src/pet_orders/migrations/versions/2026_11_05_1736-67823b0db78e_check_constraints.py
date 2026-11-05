"""check constraints

Revision ID: 67823b0db78e
Revises: 7af2964e9f2f
Create Date: 2026-11-05 17:36:11.707716

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '67823b0db78e'
down_revision: Union[str, Sequence[str], None] = '7af2964e9f2f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_check_constraint(op.f('ck_users_organization_role'), 'users', '(organization_id IS NULL) = (role IS NULL)')
    op.create_check_constraint(op.f('ck_products_price_non_negative'), 'products', 'price >= 0')
    op.create_check_constraint(op.f('ck_products_stock_non_negative'), 'products', 'stock >= 0')


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(op.f('ck_products_stock_non_negative'), 'products', type_='check')
    op.drop_constraint(op.f('ck_products_price_non_negative'), 'products', type_='check')
    op.drop_constraint(op.f('ck_users_organization_role'), 'users', type_='check')
