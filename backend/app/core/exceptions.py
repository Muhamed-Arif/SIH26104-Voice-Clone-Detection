from typing import Any, Dict, Optional


class AppException(Exception):
    """Base exception for application domain errors."""
    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


class EntityNotFoundException(AppException):
    def __init__(self, entity: str, identifier: Any):
        super().__init__(
            message=f"{entity} with id '{identifier}' was not found.",
            code="ENTITY_NOT_FOUND",
            status_code=404,
            details={"entity": entity, "identifier": str(identifier)},
        )


class InvalidAudioChunkException(AppException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="INVALID_AUDIO_CHUNK",
            status_code=422,
            details=details,
        )


class AuthenticationException(AppException):
    def __init__(self, message: str = "Could not validate credentials"):
        super().__init__(
            message=message,
            code="AUTHENTICATION_FAILED",
            status_code=401,
        )


class AuthorizationException(AppException):
    def __init__(self, message: str = "Operation not permitted"):
        super().__init__(
            message=message,
            code="PERMISSION_DENIED",
            status_code=403,
        )


class RateLimitExceededException(AppException):
    def __init__(self, message: str = "Rate limit exceeded. Please slow down."):
        super().__init__(
            message=message,
            code="RATE_LIMIT_EXCEEDED",
            status_code=429,
        )


class MLServiceException(AppException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="ML_SERVICE_UNAVAILABLE",
            status_code=503,
            details=details,
        )
