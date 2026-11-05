from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    Enum,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from pet_orders.core.db.db import Base
from pet_orders.core.db.utils import DatetimeMixin
from pet_orders.orders.consts import CurrencyEnum

if TYPE_CHECKING:
    from pet_orders.organizations.models import Organization


class Product(DatetimeMixin, Base):
    __tablename__ = 'products'
    __table_args__ = (
        UniqueConstraint('organization_id', 'sku'),
        CheckConstraint('price >= 0', name='price_non_negative'),
        CheckConstraint('stock >= 0', name='stock_non_negative'),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey('organizations.id', ondelete='RESTRICT'), nullable=False
    )
    sku: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    currency: Mapped[CurrencyEnum] = mapped_column(
        Enum(
            CurrencyEnum,
            native_enum=False,
            length=3,
            values_callable=lambda currency: [item.value for item in currency],
        ),
        nullable=False,
    )
    stock: Mapped[int] = mapped_column(nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
    organization: Mapped['Organization'] = relationship(
        back_populates='products',
        lazy='raise',
    )
