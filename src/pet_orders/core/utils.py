from datetime import UTC, datetime


def now() -> datetime:
    return datetime.now(UTC)


def from_timestamp(timestamp: int) -> datetime:
    return datetime.fromtimestamp(timestamp, UTC)
