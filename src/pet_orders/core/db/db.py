from sqlalchemy import MetaData, event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, ORMExecuteState, Session

from pet_orders.settings import settings

engine = create_async_engine(settings.database_url)
session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

convention = {
    'ix': 'ix_%(column_0_N_label)s',
    'uq': 'uq_%(table_name)s_%(column_0_N_name)s',
    'ck': 'ck_%(table_name)s_%(constraint_name)s',
    'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
    'pk': 'pk_%(table_name)s',
}


class DeletionForbidden(Exception):
    pass


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=convention)


@event.listens_for(Base, 'before_delete', propagate=True)
def _forbid_delete(mapper, connection, target) -> None:
    raise DeletionForbidden(f'{type(target).__name__} cannot be deleted')


@event.listens_for(Session, 'do_orm_execute')
def _forbid_bulk_delete(state: ORMExecuteState) -> None:
    if not state.is_delete:
        return
    mappers = state.all_mappers
    if any(issubclass(mapper.class_, Base) for mapper in mappers):
        raise DeletionForbidden(f'{mappers[0].class_.__name__} cannot be deleted')
