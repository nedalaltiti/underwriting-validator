"""
Error handling utilities for UWBot.

This module provides standardized error handling with severity levels,
error codes, and structured error responses.
"""

from enum import Enum
from typing import Optional, Dict, Any


class ErrorSeverity(Enum):
    """Enum representing error severity levels."""
    
    INFO = "INFO"  # Informational, not critical
    WARNING = "WARNING"  # Warning, potentially problematic
    ERROR = "ERROR"  # Error, operation failed
    CRITICAL = "CRITICAL"  # Critical error, system integrity affected


class ErrorCode(Enum):
    """Enum of error codes by domain."""
    
    # General errors (1000-1999)
    UNKNOWN_ERROR = 1000
    CONFIGURATION_ERROR = 1001
    DEPENDENCY_ERROR = 1002
    INITIALIZATION_ERROR = 1003
    
    # Authentication/authorization errors (2000-2999)
    AUTH_FAILED = 2000
    UNAUTHORIZED = 2001
    TOKEN_EXPIRED = 2002
    INVALID_CREDENTIALS = 2003
    
    # LLM errors (5000-5999)
    LLM_UNAVAILABLE = 5000
    PROMPT_TOO_LONG = 5001
    RESPONSE_ERROR = 5002
    CONTENT_FILTERED = 5003
    TOKEN_LIMIT_EXCEEDED = 5004
    
    # Database errors (6000-6999)
    DATABASE_ERROR = 6000
    CONNECTION_ERROR = 6001
    QUERY_ERROR = 6002
    TRANSACTION_ERROR = 6003


class BaseError(Exception):
    """Base exception class for UWBot with structured error information."""
    
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        user_message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        cause: Optional[Exception] = None,
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.user_message = user_message or message
        self.details = details or {}
        self.severity = severity
        self.cause = cause
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for JSON serialization."""
        return {
            "error": {
                "code": self.code.value,
                "message": self.message,
                "user_message": self.user_message,
                "severity": self.severity.value,
                "details": self.details,
            }
        }


class ConfigError(BaseError):
    """Configuration-related errors."""
    
    def __init__(
        self,
        message: str,
        user_message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        cause: Optional[Exception] = None,
    ):
        super().__init__(
            code=ErrorCode.CONFIGURATION_ERROR,
            message=message,
            user_message=user_message,
            details=details,
            severity=severity,
            cause=cause,
        )


class AuthError(BaseError):
    """Authentication and authorization errors."""
    
    def __init__(
        self,
        code: ErrorCode = ErrorCode.AUTH_FAILED,
        message: str = "Authentication failed",
        user_message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        cause: Optional[Exception] = None,
    ):
        super().__init__(
            code=code,
            message=message,
            user_message=user_message,
            details=details,
            severity=severity,
            cause=cause,
        )


class LLMError(BaseError):
    """LLM-related errors."""
    
    def __init__(
        self,
        code: ErrorCode = ErrorCode.LLM_UNAVAILABLE,
        message: str = "LLM operation failed",
        user_message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        cause: Optional[Exception] = None,
    ):
        super().__init__(
            code=code,
            message=message,
            user_message=user_message,
            details=details,
            severity=severity,
            cause=cause,
        )


class DatabaseError(BaseError):
    """Database-related errors."""
    
    def __init__(
        self,
        code: ErrorCode = ErrorCode.DATABASE_ERROR,
        message: str = "Database operation failed",
        user_message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        cause: Optional[Exception] = None,
    ):
        super().__init__(
            code=code,
            message=message,
            user_message=user_message,
            details=details,
            severity=severity,
            cause=cause,
        ) 