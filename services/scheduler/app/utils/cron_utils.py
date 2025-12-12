"""
Utility functions for creating croniter objects with proper second-level support.
"""

from datetime import datetime
from typing import Optional

from croniter import croniter


def create_croniter(
    cron_expr: str,
    base_time: Optional[datetime] = None,
    ret_type: Optional[type] = None,
) -> croniter:
    """
    Create a croniter object with automatic detection of second-level cron expressions.

    This function detects if the cron expression has 6 fields (with seconds at the beginning)
    and automatically sets the `second_at_beginning` parameter accordingly.

    Args:
        cron_expr: Cron expression string
        base_time: Base time for the cron calculation (defaults to current UTC time)
        ret_type: Optional return type for croniter (e.g., float for timestamps)

    Returns:
        croniter object configured with appropriate second_at_beginning setting

    Example:
        >>> from datetime import datetime
        >>> cron = create_croniter("*/5 * * * * *", datetime.utcnow())
        >>> next_run = cron.get_next(datetime)
    """
    if base_time is None:
        from datetime import datetime as dt

        base_time = dt.utcnow()

    # Check if the schedule has seconds at the beginning (i.e., 6 fields)
    schedule_fields = cron_expr.strip().split()
    has_seconds = len(schedule_fields) == 6  # True if seconds are present

    # Create croniter with appropriate parameters
    if ret_type is not None:
        return croniter(cron_expr, base_time, ret_type=ret_type, second_at_beginning=has_seconds)
    else:
        return croniter(cron_expr, base_time, second_at_beginning=has_seconds)
