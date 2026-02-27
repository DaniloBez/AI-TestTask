import logging
import openai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception
from typing import Callable

logger = logging.getLogger(__name__)

def is_rate_limit_error(exception: BaseException) -> bool:
    """
    Checks if the given exception is a rate limit error.

    Args:
        exception (BaseException): The exception to check.

    Returns:
        bool: True if the exception is a rate limit error, False otherwise.
    """
    error_str = str(exception)
    return (
        isinstance(exception, openai.RateLimitError) or
        "429" in error_str or
        "rate_limit_exceeded" in error_str.lower()
    )

def retry_on_ratelimit(count_of_retries: int = 5) -> Callable:
    """
    Creates a retry decorator specifically for rate limit exceptions.

    Args:
        count_of_retries (int, optional): The maximum number of retry attempts. Defaults to 5.

    Returns:
        Callable: A tenacity retry decorator configuration.
    """
    return retry(
        stop=stop_after_attempt(count_of_retries),
        wait=wait_exponential(multiplier=5, max=60, exp_base=2),
        retry=retry_if_exception(is_rate_limit_error),
        before_sleep=lambda retry_state: logger.warning(
            f"Rate limit hit (429). Retrying in {retry_state.next_action.sleep:.1f}s... "
            f"Attempt {retry_state.attempt_number}/{count_of_retries}"
        ),
        reraise=True
    )