"""Database exception translation and failed-transaction cleanup."""

from sqlalchemy.exc import DBAPIError, IntegrityError, SQLAlchemyError

from app.errors.exceptions import (
    DatabaseUnavailable,
    DataConflict,
    PersistenceFailure,
    UserAlreadyExists,
)


def _constraint_name(error: IntegrityError) -> str | None:
    diagnostic = getattr(error.orig, "diag", None)
    return getattr(diagnostic, "constraint_name", None) or getattr(
        error.orig, "constraint_name", None
    )


def _sqlstate(error: SQLAlchemyError) -> str | None:
    original = getattr(error, "orig", None)
    return getattr(original, "sqlstate", None) or getattr(original, "pgcode", None)


def translate_database_error(error: SQLAlchemyError):
    if isinstance(error, IntegrityError):
        constraint = _constraint_name(error)
        original_message = str(error.orig).lower()
        if (constraint and "user" in constraint.lower() and "email" in constraint.lower()) or (
            "users.email" in original_message
        ):
            return UserAlreadyExists()
        sqlstate = _sqlstate(error)
        if sqlstate == "23505" or "unique constraint failed" in original_message:
            return DataConflict()

    if isinstance(error, DBAPIError):
        sqlstate = _sqlstate(error)
        if error.connection_invalidated or (sqlstate is not None and sqlstate.startswith("08")):
            return DatabaseUnavailable()
    return PersistenceFailure()


async def raise_database_error(session, error: SQLAlchemyError) -> None:
    try:
        await session.rollback()
    except SQLAlchemyError:
        # Preserve the original database failure as the cause surfaced to the API.
        pass
    raise translate_database_error(error) from error


async def commit_session(session) -> None:
    try:
        await session.commit()
    except SQLAlchemyError as error:
        await raise_database_error(session, error)


async def flush_session(session) -> None:
    try:
        await session.flush()
    except SQLAlchemyError as error:
        await raise_database_error(session, error)


async def refresh_session(session, instance) -> None:
    try:
        await session.refresh(instance)
    except SQLAlchemyError as error:
        await raise_database_error(session, error)
