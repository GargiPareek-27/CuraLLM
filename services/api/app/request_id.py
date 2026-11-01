"""Request-id handling. Standard library only."""
import re
import uuid

_VALID_ID = re.compile(r"[A-Za-z0-9\-]{1,64}")


def resolve_request_id(incoming: str | None) -> str:
    """Keep a client-supplied id only if it is short and made of safe characters."""
    if incoming and _VALID_ID.fullmatch(incoming):
        return incoming
    return uuid.uuid4().hex
