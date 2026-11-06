from enum import StrEnum


class OrganizationStatus(StrEnum):
    ACTIVE = 'active'
    SUSPENDED = 'suspended'
    ARCHIVED = 'archived'


class OrganizationRole(StrEnum):
    OWNER = 'owner'
    ADMIN = 'admin'
    MEMBER = 'member'


USER_NOT_IN_ORGANIZATION = 'User does not belong to an organization'
