import logging
import openai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

retry_on_ratelimit = retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=5, max=60, exp_base=2),
    retry=retry_if_exception_type(openai.RateLimitError),
    before_sleep=lambda retry_state: logger.warning(
        f"Rate limit hit (429). Retrying in {retry_state.next_action.sleep}s... "
        f"Attempt {retry_state.attempt_number}"
    )
)