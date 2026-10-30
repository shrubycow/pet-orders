from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Enum, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from pet_orders.core.db.db import Base
from pet_orders.core.db.utils import DatetimeMixin
from pet_orders.orders.consts import CurrencyEnum


class Product(DatetimeMixin, Base):
    __tablename__ = 'products'

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
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
