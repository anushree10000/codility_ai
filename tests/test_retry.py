import pytest
from app.utils.retry import calculate_retry_delay

def test_fixed_retry():
    assert calculate_retry_delay("fixed", 1, 10, 100, jitter=False) == 10
    assert calculate_retry_delay("fixed", 5, 10, 100, jitter=False) == 10

def test_linear_retry():
    assert calculate_retry_delay("linear", 1, 10, 100, jitter=False) == 10
    assert calculate_retry_delay("linear", 3, 10, 100, jitter=False) == 30
    assert calculate_retry_delay("linear", 15, 10, 100, jitter=False) == 100 # Capped by max_delay

def test_exponential_retry():
    assert calculate_retry_delay("exponential", 1, 10, 1000, jitter=False) == 10
    assert calculate_retry_delay("exponential", 2, 10, 1000, jitter=False) == 20
    assert calculate_retry_delay("exponential", 3, 10, 1000, jitter=False) == 40
    assert calculate_retry_delay("exponential", 10, 10, 1000, jitter=False) == 1000 # Capped

def test_jitter():
    # Jitter is random, but should be within range
    delay = calculate_retry_delay("exponential", 2, 10, 1000, jitter=True)
    # base 20, jitter ±25% -> 15 to 25
    assert 15 <= delay <= 25
