from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Index, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.expression import text

from pet_orders.core.db.db import Base
from pet_orders.core.db.utils import DatetimeMixin
from pet_orders.organizations.consts import OrganizationRole

if TYPE_CHECKING:
    from pet_orders.organizations.models import Organization


class UserStatus(StrEnum):
    ACTIVE = 'active'
    INACTIVE = 'inactive'


class User(DatetimeMixin, Base):
    __tablename__ = 'users'
    __table_args__ = (
        CheckConstraint(
            '(organization_id IS NULL) = (role IS NULL)',
            name='organization_role',
        ),
        Index(
            'ix_users_organization_owner',
            'organization_id',
            unique=True,
            postgresql_where=text("role = 'owner'"),
        ),
    )

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
    organization_id: Mapped[UUID | None] = mapped_column(
        ForeignKey('organizations.id', ondelete='RESTRICT'), nullable=True, index=True
    )
    role: Mapped[OrganizationRole | None] = mapped_column(
        Enum(
            OrganizationRole,
            native_enum=False,
            length=32,
            values_callable=lambda role: [item.value for item in role],
        ),
        nullable=True,
    )
    organization: Mapped['Organization | None'] = relationship(
        back_populates='users',
        lazy='raise',
    )
