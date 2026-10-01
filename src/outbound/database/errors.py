from sqlalchemy.exc import IntegrityError

UNIQUE_VIOLATION = "23505"


def is_unique_violation(e: IntegrityError, constraint: str | None = None) -> bool:
    """Проверяет, что IntegrityError нарушение уникальности.

    Если передан constraint, дополнительно проверяет имя ограничения.
    """
    pg_error = getattr(e.orig, "__cause__", None)  # исходное исключение asyncpg

    sqlstate = getattr(pg_error, "sqlstate", None) or getattr(e.orig, "pgcode", None)
    if sqlstate != UNIQUE_VIOLATION:
        return False

    if constraint is None:
        return True

    return getattr(pg_error, "constraint_name", None) == constraint
