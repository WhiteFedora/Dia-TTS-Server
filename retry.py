# retry.py
# Retry logic with exponential backoff for transient errors
# Implements graceful degradation for optional features

import asyncio
import time
import logging
from typing import Callable, TypeVar, Optional, Any, Coroutine
from functools import wraps
import random

from errors import DiaError, TransientError, ErrorSeverity

logger = logging.getLogger(__name__)

T = TypeVar('T')  # Generic return type


class RetryConfig:
    """Configuration for retry behavior."""
    
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay_ms: float = 100,
        max_delay_ms: float = 30000,
        backoff_factor: float = 2.0,
        jitter: bool = True,
    ):
        """
        Initialize retry configuration.
        
        Args:
            max_attempts: Maximum number of attempts
            initial_delay_ms: Initial delay between retries in milliseconds
            max_delay_ms: Maximum delay between retries in milliseconds
            backoff_factor: Multiplier for exponential backoff (usually 2.0)
            jitter: Whether to add random jitter to delays
        """
        self.max_attempts = max_attempts
        self.initial_delay_ms = initial_delay_ms
        self.max_delay_ms = max_delay_ms
        self.backoff_factor = backoff_factor
        self.jitter = jitter
    
    def get_delay_ms(self, attempt: int) -> float:
        """
        Calculate delay for given attempt number (0-indexed).
        
        Args:
            attempt: Attempt number (0 = first retry)
        
        Returns:
            Delay in milliseconds
        """
        # Exponential backoff: initial_delay * (backoff_factor ^ attempt)
        delay = self.initial_delay_ms * (self.backoff_factor ** attempt)
        delay = min(delay, self.max_delay_ms)  # Cap at max
        
        # Add jitter (±20% of delay)
        if self.jitter:
            jitter_range = delay * 0.2
            delay += random.uniform(-jitter_range, jitter_range)
        
        return max(delay, 0)  # Ensure non-negative


class RetryResult:
    """Result of a retry operation."""
    
    def __init__(
        self,
        success: bool,
        value: Optional[Any] = None,
        error: Optional[Exception] = None,
        attempts: int = 0,
        total_delay_ms: float = 0.0,
    ):
        """Initialize RetryResult."""
        self.success = success
        self.value = value
        self.error = error
        self.attempts = attempts
        self.total_delay_ms = total_delay_ms
    
    def __repr__(self) -> str:
        if self.success:
            return f"RetryResult(success, attempts={self.attempts}, delay={self.total_delay_ms:.0f}ms)"
        else:
            return f"RetryResult(failed, error={self.error.__class__.__name__}, attempts={self.attempts})"


def retry_with_backoff(
    func: Callable[..., T],
    *args,
    config: Optional[RetryConfig] = None,
    should_retry: Optional[Callable[[Exception], bool]] = None,
    **kwargs,
) -> RetryResult:
    """
    Retry a function with exponential backoff.
    
    Args:
        func: Function to retry
        args: Positional arguments for function
        config: Retry configuration
        should_retry: Optional callback to determine if exception is retryable
        kwargs: Keyword arguments for function
    
    Returns:
        RetryResult with success status and value/error
    """
    if config is None:
        config = RetryConfig()
    
    if should_retry is None:
        # Default: retry on TransientError
        should_retry = lambda e: isinstance(e, TransientError)
    
    last_error: Optional[Exception] = None
    total_delay_ms = 0.0
    
    for attempt in range(config.max_attempts):
        try:
            logger.debug(f"Attempt {attempt + 1}/{config.max_attempts} for {func.__name__}")
            result = func(*args, **kwargs)
            
            if attempt > 0:
                logger.info(
                    f"{func.__name__} succeeded after {attempt + 1} attempts "
                    f"(total delay: {total_delay_ms:.0f}ms)"
                )
            
            return RetryResult(
                success=True,
                value=result,
                attempts=attempt + 1,
                total_delay_ms=total_delay_ms,
            )
        
        except Exception as e:
            last_error = e
            
            # Check if we should retry
            if not should_retry(e):
                logger.debug(f"Exception {e.__class__.__name__} is not retryable, giving up")
                return RetryResult(
                    success=False,
                    error=e,
                    attempts=attempt + 1,
                    total_delay_ms=total_delay_ms,
                )
            
            # Check if we have more attempts
            if attempt < config.max_attempts - 1:
                delay_ms = config.get_delay_ms(attempt)
                total_delay_ms += delay_ms
                logger.warning(
                    f"{func.__name__} failed with {e.__class__.__name__}: {e}. "
                    f"Retrying in {delay_ms:.0f}ms (attempt {attempt + 2}/{config.max_attempts})"
                )
                time.sleep(delay_ms / 1000.0)  # Convert to seconds
            else:
                logger.error(
                    f"{func.__name__} failed after {attempt + 1} attempts. "
                    f"Last error: {e.__class__.__name__}: {e}"
                )
    
    return RetryResult(
        success=False,
        error=last_error,
        attempts=config.max_attempts,
        total_delay_ms=total_delay_ms,
    )


async def retry_with_backoff_async(
    coro_func: Callable[..., Coroutine[Any, Any, T]],
    *args,
    config: Optional[RetryConfig] = None,
    should_retry: Optional[Callable[[Exception], bool]] = None,
    **kwargs,
) -> RetryResult:
    """
    Async version of retry_with_backoff.
    
    Args:
        coro_func: Async function to retry
        args: Positional arguments
        config: Retry configuration
        should_retry: Optional callback to determine if retryable
        kwargs: Keyword arguments
    
    Returns:
        RetryResult
    """
    if config is None:
        config = RetryConfig()
    
    if should_retry is None:
        should_retry = lambda e: isinstance(e, TransientError)
    
    last_error: Optional[Exception] = None
    total_delay_ms = 0.0
    
    for attempt in range(config.max_attempts):
        try:
            logger.debug(f"Async attempt {attempt + 1}/{config.max_attempts} for {coro_func.__name__}")
            result = await coro_func(*args, **kwargs)
            
            if attempt > 0:
                logger.info(
                    f"{coro_func.__name__} succeeded after {attempt + 1} attempts "
                    f"(total delay: {total_delay_ms:.0f}ms)"
                )
            
            return RetryResult(
                success=True,
                value=result,
                attempts=attempt + 1,
                total_delay_ms=total_delay_ms,
            )
        
        except Exception as e:
            last_error = e
            
            if not should_retry(e):
                logger.debug(f"Exception {e.__class__.__name__} is not retryable")
                return RetryResult(
                    success=False,
                    error=e,
                    attempts=attempt + 1,
                    total_delay_ms=total_delay_ms,
                )
            
            if attempt < config.max_attempts - 1:
                delay_ms = config.get_delay_ms(attempt)
                total_delay_ms += delay_ms
                logger.warning(
                    f"{coro_func.__name__} failed: {e.__class__.__name__}. "
                    f"Retrying in {delay_ms:.0f}ms..."
                )
                await asyncio.sleep(delay_ms / 1000.0)
            else:
                logger.error(
                    f"{coro_func.__name__} failed after {attempt + 1} attempts"
                )
    
    return RetryResult(
        success=False,
        error=last_error,
        attempts=config.max_attempts,
        total_delay_ms=total_delay_ms,
    )


def retry_decorator(config: Optional[RetryConfig] = None):
    """
    Decorator for automatic retry on functions.
    
    Args:
        config: Retry configuration
    
    Example:
        @retry_decorator(RetryConfig(max_attempts=3))
        def unstable_function():
            ...
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable[..., T]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            result = retry_with_backoff(func, *args, config=config, **kwargs)
            if result.success:
                return result.value
            else:
                if result.error is not None:
                    raise result.error
                raise RuntimeError("Retry failed with unknown error")
        
        return wrapper
    
    return decorator


class GracefulDegradation:
    """Manager for graceful degradation of optional features."""
    
    def __init__(self):
        """Initialize graceful degradation manager."""
        self.disabled_features = set()
        self.feature_errors = {}
    
    def disable_feature(self, feature_name: str, reason: Optional[str] = None) -> None:
        """
        Disable an optional feature.
        
        Args:
            feature_name: Name of feature to disable
            reason: Optional reason for disablement
        """
        self.disabled_features.add(feature_name)
        if reason:
            self.feature_errors[feature_name] = reason
            logger.warning(f"Disabling feature '{feature_name}': {reason}")
        else:
            logger.warning(f"Disabling feature '{feature_name}'")
    
    def enable_feature(self, feature_name: str) -> None:
        """
        Enable a previously disabled feature.
        
        Args:
            feature_name: Name of feature to enable
        """
        self.disabled_features.discard(feature_name)
        self.feature_errors.pop(feature_name, None)
        logger.info(f"Enabling feature '{feature_name}'")
    
    def is_enabled(self, feature_name: str) -> bool:
        """Check if feature is enabled."""
        return feature_name not in self.disabled_features
    
    def get_disabled_features(self) -> set:
        """Get set of disabled features."""
        return self.disabled_features.copy()
    
    def get_feature_status(self) -> dict:
        """Get status of all features."""
        return {
            "disabled_features": self.disabled_features.copy(),
            "feature_errors": self.feature_errors.copy(),
        }


# Global graceful degradation manager
degradation_manager = GracefulDegradation()


def with_graceful_degradation(feature_name: str, fallback_value: Optional[Any] = None):
    """
    Decorator to wrap optional feature with graceful degradation.
    
    Args:
        feature_name: Name of optional feature
        fallback_value: Value to return if feature is disabled
    
    Example:
        @with_graceful_degradation("whisper_transcription", fallback_value="")
        def generate_transcript(audio):
            ...
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            if not degradation_manager.is_enabled(feature_name):
                logger.debug(f"Feature '{feature_name}' is disabled, using fallback")
                return fallback_value
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.warning(
                    f"Feature '{feature_name}' failed: {e}. Using fallback."
                )
                degradation_manager.disable_feature(feature_name, str(e))
                return fallback_value
        
        return wrapper
    
    return decorator
