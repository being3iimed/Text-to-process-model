"""Error handling utilities."""

import httpx
from config.settings import ERROR_RATE_LIMIT, ERROR_RATE_LIMIT_MSG


class APIError(Exception):
    """Base exception for API errors."""

    pass


class RateLimitError(APIError):
    """Raised when API rate limit is exceeded."""

    pass


def handle_http_error(error: httpx.HTTPStatusError) -> None:
    """
    Handle HTTP errors with appropriate messages.

    Args:
        error: httpx.HTTPStatusError

    Raises:
        RateLimitError: If rate limited
        httpx.HTTPStatusError: For other HTTP errors
    """
    if error.response.status_code == 429:
        print("\n" + "=" * 60)
        print(ERROR_RATE_LIMIT)
        print("=" * 60)
        print(ERROR_RATE_LIMIT_MSG)
        print("=" * 60)
        raise RateLimitError("API rate limit exceeded")
    else:
        print(f"\nHTTP Error {error.response.status_code}: {error}")
        raise


def handle_unexpected_error(error: Exception) -> None:
    """
    Handle unexpected errors.

    Args:
        error: Exception

    Raises:
        Exception: Re-raises the error
    """
    print(f"\nUnexpected error: {type(error).__name__}: {error}")
    raise
