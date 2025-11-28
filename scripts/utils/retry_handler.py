"""
Retry Handler Module
Provides retry logic with exponential backoff for API calls
"""

import time
import logging
from typing import Callable, Any, Optional, Type, Tuple
from functools import wraps

logger = logging.getLogger(__name__)


class RetryError(Exception):
    """Exception raised when all retry attempts are exhausted"""
    pass


class RetryHandler:
    """
    Handles retry logic with exponential backoff
    """

    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 2.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        exceptions: Tuple[Type[Exception], ...] = (Exception,),
    ):
        """
        Initialize retry handler

        Args:
            max_attempts: Maximum number of retry attempts
            initial_delay: Initial delay between retries (seconds)
            max_delay: Maximum delay between retries (seconds)
            exponential_base: Base for exponential backoff calculation
            exceptions: Tuple of exception types to catch and retry
        """
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.exceptions = exceptions

    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for given attempt using exponential backoff

        Args:
            attempt: Current attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        delay = self.initial_delay * (self.exponential_base ** attempt)
        return min(delay, self.max_delay)

    def execute(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute function with retry logic

        Args:
            func: Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            Function result

        Raises:
            RetryError: If all retry attempts are exhausted
        """
        last_exception = None

        for attempt in range(self.max_attempts):
            try:
                result = func(*args, **kwargs)
                if attempt > 0:
                    logger.info(f"Successfully executed after {attempt + 1} attempts")
                return result

            except self.exceptions as e:
                last_exception = e

                if attempt < self.max_attempts - 1:
                    delay = self.calculate_delay(attempt)
                    logger.warning(
                        f"Attempt {attempt + 1}/{self.max_attempts} failed: {str(e)}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(
                        f"All {self.max_attempts} attempts failed for {func.__name__}"
                    )

        raise RetryError(
            f"Failed after {self.max_attempts} attempts. Last error: {last_exception}"
        ) from last_exception


def retry(
    max_attempts: int = 3,
    initial_delay: float = 2.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
):
    """
    Decorator for retrying functions with exponential backoff

    Args:
        max_attempts: Maximum number of retry attempts
        initial_delay: Initial delay between retries (seconds)
        max_delay: Maximum delay between retries (seconds)
        exponential_base: Base for exponential backoff calculation
        exceptions: Tuple of exception types to catch and retry

    Returns:
        Decorated function

    Example:
        @retry(max_attempts=5, initial_delay=1.0, exceptions=(ConnectionError, TimeoutError))
        def fetch_data():
            # Function that might fail
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            handler = RetryHandler(
                max_attempts=max_attempts,
                initial_delay=initial_delay,
                max_delay=max_delay,
                exponential_base=exponential_base,
                exceptions=exceptions,
            )
            return handler.execute(func, *args, **kwargs)
        return wrapper
    return decorator


class RateLimiter:
    """
    Rate limiter for API calls
    """

    def __init__(
        self,
        requests_per_minute: int = 20,
        delay_between_requests: float = 3.0,
    ):
        """
        Initialize rate limiter

        Args:
            requests_per_minute: Maximum requests per minute
            delay_between_requests: Minimum delay between requests (seconds)
        """
        self.requests_per_minute = requests_per_minute
        self.delay_between_requests = delay_between_requests
        self.last_request_time: Optional[float] = None
        self.request_times: list[float] = []

    def wait_if_needed(self):
        """
        Wait if necessary to comply with rate limits
        """
        current_time = time.time()

        # Clean old request times (older than 1 minute)
        cutoff_time = current_time - 60
        self.request_times = [t for t in self.request_times if t > cutoff_time]

        # Check if we've hit the per-minute limit
        if len(self.request_times) >= self.requests_per_minute:
            # Wait until the oldest request is more than 1 minute old
            oldest_request = self.request_times[0]
            wait_time = 60 - (current_time - oldest_request)
            if wait_time > 0:
                logger.info(
                    f"Rate limit reached ({self.requests_per_minute} req/min). "
                    f"Waiting {wait_time:.1f}s..."
                )
                time.sleep(wait_time)
                current_time = time.time()

        # Check minimum delay between requests
        if self.last_request_time is not None:
            time_since_last = current_time - self.last_request_time
            if time_since_last < self.delay_between_requests:
                wait_time = self.delay_between_requests - time_since_last
                logger.debug(f"Waiting {wait_time:.1f}s before next request")
                time.sleep(wait_time)
                current_time = time.time()

        # Record this request
        self.last_request_time = current_time
        self.request_times.append(current_time)

    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with rate limiting

        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result
        """
        self.wait_if_needed()
        return func(*args, **kwargs)


def rate_limited(
    requests_per_minute: int = 20,
    delay_between_requests: float = 3.0,
):
    """
    Decorator for rate-limited functions

    Args:
        requests_per_minute: Maximum requests per minute
        delay_between_requests: Minimum delay between requests (seconds)

    Returns:
        Decorated function

    Example:
        @rate_limited(requests_per_minute=30, delay_between_requests=2.0)
        def fetch_data():
            # Function that calls external API
            pass
    """
    limiter = RateLimiter(
        requests_per_minute=requests_per_minute,
        delay_between_requests=delay_between_requests,
    )

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            return limiter.execute(func, *args, **kwargs)
        return wrapper
    return decorator


def retry_with_rate_limit(
    max_attempts: int = 3,
    initial_delay: float = 2.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    requests_per_minute: int = 20,
    delay_between_requests: float = 3.0,
):
    """
    Combined decorator for retry logic with rate limiting

    Args:
        max_attempts: Maximum number of retry attempts
        initial_delay: Initial delay between retries (seconds)
        max_delay: Maximum delay between retries (seconds)
        exponential_base: Base for exponential backoff calculation
        exceptions: Tuple of exception types to catch and retry
        requests_per_minute: Maximum requests per minute
        delay_between_requests: Minimum delay between requests (seconds)

    Returns:
        Decorated function

    Example:
        @retry_with_rate_limit(
            max_attempts=5,
            requests_per_minute=30,
            exceptions=(ConnectionError, TimeoutError)
        )
        def fetch_data():
            # Robust API call with retry and rate limiting
            pass
    """
    def decorator(func: Callable) -> Callable:
        # Apply rate limiting first, then retry logic
        rate_limited_func = rate_limited(
            requests_per_minute=requests_per_minute,
            delay_between_requests=delay_between_requests,
        )(func)

        retry_func = retry(
            max_attempts=max_attempts,
            initial_delay=initial_delay,
            max_delay=max_delay,
            exponential_base=exponential_base,
            exceptions=exceptions,
        )(rate_limited_func)

        return retry_func
    return decorator


class CircuitBreaker:
    """
    Circuit breaker pattern for failing fast when service is unavailable
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Type[Exception] = Exception,
    ):
        """
        Initialize circuit breaker

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Time to wait before attempting recovery (seconds)
            expected_exception: Exception type to count as failures
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = 'closed'  # closed, open, half-open

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection

        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            Exception: If circuit is open or function fails
        """
        if self.state == 'open':
            # Check if we should attempt recovery
            if time.time() - self.last_failure_time > self.recovery_timeout:
                logger.info("Circuit breaker entering half-open state")
                self.state = 'half-open'
            else:
                raise Exception(
                    f"Circuit breaker is OPEN. Service unavailable. "
                    f"Will retry after {self.recovery_timeout}s"
                )

        try:
            result = func(*args, **kwargs)

            # Success - reset if in half-open state
            if self.state == 'half-open':
                logger.info("Circuit breaker closing after successful call")
                self.state = 'closed'
                self.failure_count = 0

            return result

        except self.expected_exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()

            logger.warning(
                f"Circuit breaker failure {self.failure_count}/{self.failure_threshold}: {e}"
            )

            # Open circuit if threshold reached
            if self.failure_count >= self.failure_threshold:
                self.state = 'open'
                logger.error(
                    f"Circuit breaker OPENED after {self.failure_count} failures. "
                    f"Will attempt recovery after {self.recovery_timeout}s"
                )

            raise
