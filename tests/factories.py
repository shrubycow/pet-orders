from decimal import Decimal

from pet_orders.orders.consts import CurrencyEnum
from pet_orders.orders.models import Product
from pet_orders.organizations.consts import OrganizationRole
from pet_orders.organizations.models import Organization
from pet_orders.users.models import User

USER_EMAIL = 'user@example.com'
USER_PASSWORD = 'password'


def make_organization(name: str = 'Acme') -> Organization:
    return Organization(name=name)


def add_user_to_organization(
    user: User,
    organization: Organization,
    role: OrganizationRole = OrganizationRole.MEMBER,
) -> None:
    user.organization = organization
    user.role = role


def make_user(
    email: str = USER_EMAIL,
    organization: Organization | None = None,
    role: OrganizationRole | None = None,
) -> User:
    return User(email=email, password='hash', organization=organization, role=role)


def make_product(organization: Organization | None, **overrides: object) -> Product:
    fields: dict[str, object] = {
        'sku': 'PRD-000001',
        'name': 'Dog food',
        'description': 'Dry food for adult dogs',
        'price': Decimal('10.5000'),
        'currency': CurrencyEnum.USD,
        **overrides,
    }
    return Product(organization=organization, **fields)
