from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Enum, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from pet_orders.core.db.db import Base
from pet_orders.core.db.utils import DatetimeMixin
from pet_orders.organizations.consts import OrganizationStatus

if TYPE_CHECKING:
    from pet_orders.orders.models import Product
    from pet_orders.users.models import User


class Organization(DatetimeMixin, Base):
    __tablename__ = 'organizations'

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    status: Mapped[OrganizationStatus] = mapped_column(
        Enum(
            OrganizationStatus,
            native_enum=False,
            length=32,
            values_callable=lambda status: [item.value for item in status],
        ),
        nullable=False,
        default=OrganizationStatus.ACTIVE,
    )
    users: Mapped[list['User']] = relationship(
        back_populates='organization',
        passive_deletes='all',
        lazy='raise',
    )
    products: Mapped[list['Product']] = relationship(
        back_populates='organization',
        passive_deletes='all',
        lazy='raise',
    )
