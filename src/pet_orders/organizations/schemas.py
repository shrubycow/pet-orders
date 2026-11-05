from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from pet_orders.organizations.consts import OrganizationStatus


class OrganizationCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class OrganizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    status: OrganizationStatus
