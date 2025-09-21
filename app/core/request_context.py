import uuid
from typing import Optional
from contextvars import ContextVar

request_id_context: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


def get_request_id() -> Optional[str]:
    return request_id_context.get()


def generate_request_id() -> str:
    uuid_str = str(uuid.uuid4())
    request_id_context.set(uuid_str)
    return uuid_str
