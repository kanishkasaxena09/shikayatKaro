"""Virtual clock system for Project Shikayat Karo.

Allows deterministic time-travel for testing and live demonstrations.
All modules in the system must query get_current_time() instead of datetime.now().
"""

from datetime import datetime, timedelta, timezone

# Stored offset in seconds
_TIME_OFFSET_SECONDS: float = 0.0


def get_current_time() -> datetime:
    """Returns the current virtual time (naive UTC datetime)."""
    base_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    return base_utc + timedelta(seconds=_TIME_OFFSET_SECONDS)


def advance_time(hours: float) -> datetime:
    """Advances the virtual clock by the given number of hours.
    
    Returns:
        The new virtual current time.
    """
    global _TIME_OFFSET_SECONDS
    _TIME_OFFSET_SECONDS += float(hours) * 3600.0
    return get_current_time()


def reset_time() -> datetime:
    """Resets the virtual clock offset to zero (real-world UTC).
    
    Returns:
        The reset virtual current time.
    """
    global _TIME_OFFSET_SECONDS
    _TIME_OFFSET_SECONDS = 0.0
    return get_current_time()


def get_offset_hours() -> float:
    """Returns the current virtual clock offset in hours."""
    return _TIME_OFFSET_SECONDS / 3600.0
