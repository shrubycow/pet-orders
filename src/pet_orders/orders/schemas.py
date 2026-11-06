from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from pet_orders.orders.consts import CurrencyEnum


class ProductCreateRequest(BaseModel):
    sku: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    price: Decimal = Field(ge=0, max_digits=20, decimal_places=4)
    currency: CurrencyEnum
    stock: int = Field(default=0, ge=0)
    is_active: bool = True

    @field_validator('sku', 'name', 'description', mode='before')
    @classmethod
    def strip_text(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    sku: str
    name: str
    description: str
    price: Decimal
    currency: CurrencyEnum
    stock: int
    is_active: bool
