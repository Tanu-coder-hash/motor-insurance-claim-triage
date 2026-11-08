
from contextvars import ContextVar
from uuid import uuid4

correlation_id_var: ContextVar[str] = ContextVar(
    "correlation_id",
    default="",
)


def generate_correlation_id() -> str:
    """Generate a unique correlation ID."""
    return str(uuid4())


def set_correlation_id(correlation_id: str | None = None) -> str:
    """Set an existing correlation ID or generate a new one."""
    value = correlation_id or generate_correlation_id()
    correlation_id_var.set(value)
    return value


def get_correlation_id() -> str:
    """Get the current correlation ID."""
    return correlation_id_var.get()


def clear_correlation_id() -> None:
    """Clear the current correlation ID."""
    correlation_id_var.set("")
