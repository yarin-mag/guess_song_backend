"""
Custom exceptions for the application.
"""

class AppException(Exception):
    """Base class for all application exceptions."""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class UserNotFoundException(AppException):
    """Raised when a user is not found."""
    def __init__(self, message: str = "User not found", status_code: int = 404):
        super().__init__(message, status_code)

class SubscriptionNotFoundException(AppException):
    """Raised when a subscription is not found."""
    def __init__(self, message: str = "Subscription not found", status_code: int = 404):
        super().__init__(message, status_code)

class NoUnusedSongsException(AppException):
    """Raised when there are no unused songs."""
    def __init__(self, message: str = "No unused songs left", status_code: int = 404):
        super().__init__(message, status_code)

class SongNotFoundException(AppException):
    """Raised when a song is not found."""
    def __init__(self, message: str = "Song not found", status_code: int = 404):
        super().__init__(message, status_code)

class InternalJWTExpiredException(AppException):
    """Raised when the internal JWT has expired."""
    def __init__(self, message: str = "Internal JWT expired", status_code: int = 401):
        super().__init__(message, status_code)

class InvalidInternalJWTException(AppException):
    """Raised when the internal JWT is invalid."""
    def __init__(self, message: str = "Invalid internal JWT", status_code: int = 401):
        super().__init__(message, status_code)

class NoGuessesLeftException(AppException):
    """Raised when a user has no guesses left for the day."""
    def __init__(self, message: str = "No guesses left for today", status_code: int = 403):
        super().__init__(message, status_code)
