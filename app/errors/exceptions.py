"""Transport-independent errors raised by application and domain layers."""

from typing import Any


class AppError(Exception):
    code = "APPLICATION_ERROR"
    message = "An application error occurred"

    def __init__(
        self,
        code: str | None = None,
        message: str | None = None,
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        self.code = code or type(self).code
        self.message = message or type(self).message
        self.details = details or []
        super().__init__(self.message)


class BadRequestError(AppError):
    code = "BAD_REQUEST"
    message = "The request could not be processed"


class InvalidInputError(AppError):
    code = "INVALID_INPUT"
    message = "The request contains invalid data"


class NotFoundError(AppError):
    code = "RESOURCE_NOT_FOUND"
    message = "The requested resource was not found"


class ConflictError(AppError):
    code = "CONFLICT"
    message = "The request conflicts with the current state"


class AuthenticationError(AppError):
    code = "AUTHENTICATION_FAILED"
    message = "Authentication failed"


class PermissionDenied(AppError):
    code = "PERMISSION_DENIED"
    message = "You do not have permission to perform this action"


class PersistenceFailure(AppError):
    code = "DATABASE_ERROR"
    message = "A database operation failed"


class DatabaseUnavailable(PersistenceFailure):
    code = "DATABASE_UNAVAILABLE"
    message = "The database is temporarily unavailable"
    retryable = True


class UserAlreadyExists(ConflictError):
    code = "USER_ALREADY_EXISTS"
    message = "A user with this email already exists"


class DataConflict(ConflictError):
    code = "DATA_CONFLICT"
    message = "A record with these values already exists"


class AccountLocked(AuthenticationError):
    code = "ACCOUNT_LOCKED"
    message = "The account is temporarily locked"


class InvalidCredentials(AuthenticationError):
    code = "INVALID_CREDENTIALS"
    message = "Invalid credentials"


class EmailVerificationRequired(AuthenticationError):
    code = "EMAIL_VERIFICATION_REQUIRED"
    message = "Email verification is required"


class InvalidAccessToken(AuthenticationError):
    code = "INVALID_ACCESS_TOKEN"
    message = "Invalid authentication token"


class AuthenticationRequired(AuthenticationError):
    code = "AUTHENTICATION_REQUIRED"
    message = "Authentication is required"


class SessionRevoked(AuthenticationError):
    code = "SESSION_REVOKED"
    message = "The session is no longer active"


class InvalidRefreshToken(AuthenticationError):
    code = "INVALID_REFRESH_TOKEN"
    message = "Invalid refresh token"


class RefreshTokenReplay(InvalidRefreshToken):
    code = "REFRESH_TOKEN_REPLAY"
    message = "Refresh token reuse was detected"


class InvalidVerificationCode(BadRequestError):
    code = "INVALID_VERIFICATION_CODE"
    message = "The verification code is invalid or expired"


class FeatureNotAvailable(NotFoundError):
    code = "FEATURE_NOT_AVAILABLE"
    message = "This feature is not enabled"


class SessionManagementDisabled(ConflictError):
    code = "SESSION_MANAGEMENT_DISABLED"
    message = "Session management is disabled"


class CurrentSessionUnavailable(ConflictError):
    code = "CURRENT_SESSION_UNAVAILABLE"
    message = "The current session is unavailable"


class SessionNotFound(NotFoundError):
    code = "SESSION_NOT_FOUND"
    message = "The session was not found"


class UserOrRoleNotFound(NotFoundError):
    code = "USER_OR_ROLE_NOT_FOUND"
    message = "The user or role was not found"


class UserNotFound(NotFoundError):
    code = "USER_NOT_FOUND"
    message = "The user was not found"


class SourceNotFound(NotFoundError):
    code = "SOURCE_NOT_FOUND"
    message = "The source was not found"


class UnsupportedSourceKind(InvalidInputError):
    code = "UNSUPPORTED_SOURCE_KIND"
    message = "The configured source type is not supported"


class IngestionAlreadyRunning(ConflictError):
    code = "INGESTION_ALREADY_RUNNING"
    message = "An ingestion run is already in progress for this source"


class RunNotFound(NotFoundError):
    code = "RUN_NOT_FOUND"
    message = "The ingestion run was not found"


class JobNotFound(NotFoundError):
    code = "JOB_NOT_FOUND"
    message = "The job was not found"


class MatchNotFound(NotFoundError):
    code = "MATCH_NOT_FOUND"
    message = "The match was not found"


class ActivePreferenceNotFound(NotFoundError):
    code = "ACTIVE_PREFERENCES_NOT_FOUND"
    message = "No active preference profile was found"


class NotificationDeliveryNotFound(NotFoundError):
    code = "NOTIFICATION_DELIVERY_NOT_FOUND"
    message = "The notification delivery was not found"


class InvalidUserIdentifier(BadRequestError):
    code = "INVALID_USER_ID"
    message = "X-User-ID must be a UUID"
