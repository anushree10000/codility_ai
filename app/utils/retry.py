import random

from app.core.constants import RetryStrategy


def calculate_retry_delay(
    strategy: RetryStrategy,
    attempt: int,
    base_delay: float,
    max_delay: float,
    jitter: bool = True,
) -> float:
    if strategy == RetryStrategy.fixed:
        delay = base_delay
    elif strategy == RetryStrategy.linear:
        delay = base_delay * attempt
    elif strategy == RetryStrategy.exponential:
        delay = base_delay * (2 ** (attempt - 1))
    else:
        delay = base_delay

    if jitter:
        delay *= random.uniform(0.75, 1.25)

    return min(delay, max_delay)
