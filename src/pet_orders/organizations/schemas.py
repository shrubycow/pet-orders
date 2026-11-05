from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from pet_orders.organizations.consts import OrganizationStatus


class OrganizationCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)

    @field_validator('name', mode='before')
    @classmethod
    def strip_name(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class OrganizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    status: OrganizationStatus
