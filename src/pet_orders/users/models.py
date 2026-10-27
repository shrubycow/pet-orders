from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import Enum, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from pet_orders.core.db.db import Base
from pet_orders.core.db.utils import DatetimeMixin


class UserStatus(StrEnum):
    ACTIVE = 'active'
    INACTIVE = 'inactive'


class User(DatetimeMixin, Base):
    __tablename__ = 'users'

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password: Mapped[str] = mapped_column(String(255))
    status: Mapped[UserStatus] = mapped_column(
        Enum(
            UserStatus,
            native_enum=False,
            length=32,
            values_callable=lambda status: [item.value for item in status],
        ),
        default=UserStatus.INACTIVE,
    )
