# errors.py
# Custom error hierarchy for Dia TTS Server
# Enables proper error categorization, retry logic, and graceful degradation

import logging
from typing import Optional
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorSeverity(str, Enum):
    """Severity levels for errors."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorCategory(str, Enum):
    """Categories of errors for proper handling."""
    TRANSIENT = "transient"  # Temporary, retry may succeed
    PERMANENT = "permanent"  # Permanent, retry won't help
    RESOURCE = "resource"    # Resource exhaustion, may recover with cleanup
    CONFIGURATION = "configuration"  # Config/setup error
    VALIDATION = "validation"  # Input validation error


class DiaError(Exception):
    """Base exception class for all Dia TTS errors."""
    
    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.PERMANENT,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        recoverable: bool = False,
        retry_count: int = 0,
        original_exception: Optional[Exception] = None,
    ):
        """
        Initialize DiaError.
        
        Args:
            message: Error message
            category: Error category for routing
            severity: Error severity level
            recoverable: Whether error can be recovered from
            retry_count: Number of retries already attempted
            original_exception: Original exception that caused this error
        """
        self.message = message
        self.category = category
        self.severity = severity
        self.recoverable = recoverable
        self.retry_count = retry_count
        self.original_exception = original_exception
        
        super().__init__(message)
    
    def __str__(self) -> str:
        """Return formatted error string."""
        base = f"[{self.category.value}] {self.message}"
        if self.retry_count > 0:
            base += f" (retried {self.retry_count} times)"
        return base
    
    def __repr__(self) -> str:
        """Return detailed representation."""
        return f"{self.__class__.__name__}({self.message!r}, category={self.category.value}, recoverable={self.recoverable})"
    
    def is_transient(self) -> bool:
        """Check if error is transient and might be retried."""
        return self.category == ErrorCategory.TRANSIENT
    
    def is_recoverable(self) -> bool:
        """Check if error can be recovered from."""
        return self.recoverable or self.is_transient()
    
    def log(self) -> None:
        """Log error at appropriate level based on severity."""
        if self.severity == ErrorSeverity.CRITICAL:
            logger.critical(str(self))
        elif self.severity == ErrorSeverity.ERROR:
            logger.error(str(self), exc_info=self.original_exception)
        elif self.severity == ErrorSeverity.WARNING:
            logger.warning(str(self))
        else:
            logger.info(str(self))


class TransientError(DiaError):
    """Transient errors that may succeed on retry (e.g., temporary network issues)."""
    
    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.WARNING,
        retry_count: int = 0,
        original_exception: Optional[Exception] = None,
    ):
        """Initialize TransientError."""
        super().__init__(
            message=message,
            category=ErrorCategory.TRANSIENT,
            severity=severity,
            recoverable=True,
            retry_count=retry_count,
            original_exception=original_exception,
        )


class PermanentError(DiaError):
    """Permanent errors that won't succeed on retry (e.g., invalid config)."""
    
    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        original_exception: Optional[Exception] = None,
    ):
        """Initialize PermanentError."""
        super().__init__(
            message=message,
            category=ErrorCategory.PERMANENT,
            severity=severity,
            recoverable=False,
            original_exception=original_exception,
        )


class ResourceError(DiaError):
    """Resource exhaustion errors (e.g., GPU OOM, disk full)."""
    
    def __init__(
        self,
        message: str,
        resource_type: str = "unknown",
        available: Optional[float] = None,
        required: Optional[float] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        original_exception: Optional[Exception] = None,
    ):
        """
        Initialize ResourceError.
        
        Args:
            message: Error message
            resource_type: Type of resource ("memory", "disk", "gpu_memory", etc.)
            available: Available resource amount
            required: Required resource amount
            severity: Error severity
            original_exception: Original exception
        """
        self.resource_type = resource_type
        self.available = available
        self.required = required
        
        # Build detailed message
        detailed_msg = f"{message} ({resource_type})"
        if available is not None and required is not None:
            detailed_msg += f": need {required}, have {available}"
        
        super().__init__(
            message=detailed_msg,
            category=ErrorCategory.RESOURCE,
            severity=severity,
            recoverable=True,  # May recover after cleanup
            original_exception=original_exception,
        )


class ValidationError(DiaError):
    """Input validation errors."""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[str] = None,
        original_exception: Optional[Exception] = None,
    ):
        """
        Initialize ValidationError.
        
        Args:
            message: Error message
            field: Name of field that failed validation
            value: Invalid value provided
            original_exception: Original exception
        """
        self.field = field
        self.value = value
        
        detailed_msg = message
        if field:
            detailed_msg = f"Validation failed for '{field}': {message}"
        if value is not None:
            detailed_msg += f" (got: {value!r})"
        
        super().__init__(
            message=detailed_msg,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.WARNING,
            recoverable=False,
            original_exception=original_exception,
        )


class ConfigurationError(DiaError):
    """Configuration/setup errors."""
    
    def __init__(
        self,
        message: str,
        setting: Optional[str] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        original_exception: Optional[Exception] = None,
    ):
        """Initialize ConfigurationError."""
        self.setting = setting
        
        detailed_msg = message
        if setting:
            detailed_msg = f"Configuration error for '{setting}': {message}"
        
        super().__init__(
            message=detailed_msg,
            category=ErrorCategory.CONFIGURATION,
            severity=severity,
            recoverable=False,
            original_exception=original_exception,
        )


class ModelLoadError(PermanentError):
    """Error loading model weights or configuration."""
    pass


class DeviceError(PermanentError):
    """Error related to device selection or management."""
    pass


class AudioProcessingError(TransientError):
    """Error processing audio (may recover)."""
    pass


class CloningError(PermanentError):
    """Error in voice cloning process."""
    pass


class GenerationError(TransientError):
    """Error during speech generation (may recover with retry)."""
    pass


class APIError(DiaError):
    """Error in API handling."""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        original_exception: Optional[Exception] = None,
    ):
        """Initialize APIError."""
        self.status_code = status_code
        
        # Map status codes to severity
        if 400 <= status_code < 500:
            severity = ErrorSeverity.WARNING
            category = ErrorCategory.VALIDATION if 400 <= status_code < 422 else ErrorCategory.PERMANENT
        else:
            severity = ErrorSeverity.ERROR
            category = ErrorCategory.RESOURCE if status_code == 503 else ErrorCategory.TRANSIENT
        
        super().__init__(
            message=message,
            category=category,
            severity=severity,
            recoverable=(500 <= status_code <= 504),  # 5xx errors may be transient
            original_exception=original_exception,
        )
