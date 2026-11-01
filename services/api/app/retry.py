"""Retry timing. Standard library only."""


def backoff_delay(attempt: int, base: float = 0.2, cap: float = 2.0) -> float:
    """Exponential backoff for a zero-based attempt number, capped at `cap` seconds."""
    if attempt < 0:
        raise ValueError("attempt must be >= 0")
    return min(cap, base * (2**attempt))
