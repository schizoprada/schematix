# ~/schematix/src/schematix/transforms/dates.py
"""
Date and time transformation functions for parsing, formatting, and manipulation.
"""
from __future__ import annotations
import re, typing as t
from datetime import datetime, date, time, timedelta, timezone
import calendar

from schematix.core.transform import transform, Transform

# Common date format patterns
COMMONFORMATS = [
    '%Y-%m-%d',           # 2023-12-25
    '%Y/%m/%d',           # 2023/12/25
    '%m/%d/%Y',           # 12/25/2023
    '%m-%d-%Y',           # 12-25-2023
    '%d/%m/%Y',           # 25/12/2023
    '%d-%m-%Y',           # 25-12-2023
    '%Y-%m-%d %H:%M:%S',  # 2023-12-25 14:30:00
    '%Y-%m-%dT%H:%M:%S',  # 2023-12-25T14:30:00 (ISO)
    '%Y-%m-%dT%H:%M:%SZ', # 2023-12-25T14:30:00Z (ISO with Z)
    '%Y-%m-%d %H:%M',     # 2023-12-25 14:30
    '%m/%d/%Y %H:%M:%S',  # 12/25/2023 14:30:00
    '%m/%d/%Y %H:%M',     # 12/25/2023 14:30
    '%d %b %Y',           # 25 Dec 2023
    '%d %B %Y',           # 25 December 2023
    '%b %d, %Y',          # Dec 25, 2023
    '%B %d, %Y',          # December 25, 2023
    '%a %b %d %H:%M:%S %Y', # Mon Dec 25 14:30:00 2023
]

# Parsing and Conversion

class parse:
    """Date parsing transforms."""

    @transform
    @staticmethod
    def auto(value: t.Any) -> datetime:
        """
        Auto-parse date from string using common formats.

        Tries multiple common date formats until one succeeds.
        """
        if isinstance(value, datetime):
            return value
        if isinstance(value, date):
            return datetime.combine(value, time.min)

        text = str(value).strip()

        # Try ISO format with timezone info first
        isopatterns = [
            r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)',
            r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:\.\d+)?)',
        ]

        for pattern in isopatterns:
            match = re.search(pattern, text)
            if match:
                iso_text = match.group(1)
                try:
                    # Handle timezone suffixes
                    if iso_text.endswith('Z'):
                        iso_text = iso_text[:-1] + '+00:00'
                    return datetime.fromisoformat(iso_text.replace('Z', '+00:00'))
                except ValueError:
                    continue

        # Try common formats
        for fmt in COMMONFORMATS:
            try:
                return datetime.strptime(text, fmt)
            except ValueError:
                continue

        # Try parsing timestamp
        try:
            timestamp = float(text)
            return datetime.fromtimestamp(timestamp)
        except (ValueError, OSError):
            pass

        raise ValueError(f"Unable to parse date: {value}")

    @staticmethod
    def format(fmt: str) -> Transform:
        """
        Parse date using specific format.

        Args:
            fmt: strptime format string

        Returns:
            Transform that parses with specific format
        """
        @transform(name=f"parse.format('{fmt}')")
        def _parseformat(value: t.Any) -> datetime:
            if isinstance(value, datetime):
                return value
            if isinstance(value, date):
                return datetime.combine(value, time.min)
            return datetime.strptime(str(value).strip(), fmt)
        return _parseformat

    @transform
    @staticmethod
    def iso(value: t.Any) -> datetime:
        """Parse ISO format date string."""
        if isinstance(value, datetime):
            return value
        if isinstance(value, date):
            return datetime.combine(value, time.min)

        text = str(value).strip()
        # Handle Z suffix
        if text.endswith('Z'):
            text = text[:-1] + '+00:00'
        return datetime.fromisoformat(text)

    @transform
    @staticmethod
    def timestamp(value: t.Any) -> datetime:
        """Parse Unix timestamp."""
        if isinstance(value, datetime):
            return value
        timestamp = float(value)
        return datetime.fromtimestamp(timestamp)

class to:
    """Date conversion transforms."""

    @transform
    @staticmethod
    def date(value: t.Any) -> date:
        """Convert to date object."""
        if isinstance(value, date):
            return value
        if isinstance(value, datetime):
            return value.date()
        dt = parse.auto(value)
        return dt.date()

    @transform
    @staticmethod
    def time(value: t.Any) -> time:
        """Convert to time object."""
        if isinstance(value, time):
            return value
        if isinstance(value, datetime):
            return value.time()
        dt = parse.auto(value)
        return dt.time()

    @transform
    @staticmethod
    def datetime(value: t.Any) -> datetime:
        """Convert to datetime object."""
        if isinstance(value, datetime):
            return value
        if isinstance(value, date):
            return datetime.combine(value, time.min)
        return parse.auto(value)

    @transform
    @staticmethod
    def timestamp(value: t.Any) -> float:
        """Convert to Unix timestamp."""
        if isinstance(value, (int, float)):
            return float(value)
        dt = to.datetime(value)
        return dt.timestamp()

# Formatting

class format:
    """Date formatting transforms."""

    @staticmethod
    def strftime(fmt: str) -> Transform:
        """
        Format date using strftime format.

        Args:
            fmt: strftime format string

        Returns:
            Transform that formats with specific format
        """
        @transform(name=f"format.strftime('{fmt}')")
        def _strftime(value: t.Any) -> str:
            dt = to.datetime(value)
            return dt.strftime(fmt)
        return _strftime

    @transform
    @staticmethod
    def iso(value: t.Any) -> str:
        """Format as ISO string."""
        dt = to.datetime(value)
        return dt.isoformat()

    @transform
    @staticmethod
    def date(value: t.Any) -> str:
        """Format as YYYY-MM-DD."""
        dt = to.datetime(value)
        return dt.strftime('%Y-%m-%d')

    @transform
    @staticmethod
    def time(value: t.Any) -> str:
        """Format as HH:MM:SS."""
        dt = to.datetime(value)
        return dt.strftime('%H:%M:%S')

    @transform
    @staticmethod
    def datetime(value: t.Any) -> str:
        """Format as YYYY-MM-DD HH:MM:SS."""
        dt = to.datetime(value)
        return dt.strftime('%Y-%m-%d %H:%M:%S')

    @transform
    @staticmethod
    def readable(value: t.Any) -> str:
        """Format in human-readable format."""
        dt = to.datetime(value)
        return dt.strftime('%B %d, %Y at %I:%M %p')

    @transform
    @staticmethod
    def short(value: t.Any) -> str:
        """Format in short format."""
        dt = to.datetime(value)
        return dt.strftime('%m/%d/%Y')

# Date Math Operations

def add(days: int = 0, hours: int = 0, minutes: int = 0, seconds: int = 0, weeks: int = 0) -> Transform:
    """
    Add time to date.

    Args:
        days: Days to add
        hours: Hours to add
        minutes: Minutes to add
        seconds: Seconds to add
        weeks: Weeks to add

    Returns:
        Transform that adds time
    """
    delta = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds, weeks=weeks)

    @transform(name=f"add({delta})")
    def _add(value: t.Any) -> datetime:
        dt = to.datetime(value)
        return dt + delta
    return _add

def subtract(days: int = 0, hours: int = 0, minutes: int = 0, seconds: int = 0, weeks: int = 0) -> Transform:
    """
    Subtract time from date.

    Args:
        days: Days to subtract
        hours: Hours to subtract
        minutes: Minutes to subtract
        seconds: Seconds to subtract
        weeks: Weeks to subtract

    Returns:
        Transform that subtracts time
    """
    delta = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds, weeks=weeks)

    @transform(name=f"subtract({delta})")
    def _subtract(value: t.Any) -> datetime:
        dt = to.datetime(value)
        return dt - delta
    return _subtract

def difference(other: t.Any) -> Transform:
    """
    Calculate difference between dates.

    Args:
        other: Other date to compare with

    Returns:
        Transform that calculates difference as timedelta
    """
    @transform(name=f"difference({other})")
    def _difference(value: t.Any) -> timedelta:
        dt1 = to.datetime(value)
        dt2 = to.datetime(other)
        return dt1 - dt2
    return _difference

# Date Components

@transform
def year(value: t.Any) -> int:
    """Extract year."""
    dt = to.datetime(value)
    return dt.year

@transform
def month(value: t.Any) -> int:
    """Extract month (1-12)."""
    dt = to.datetime(value)
    return dt.month

@transform
def day(value: t.Any) -> int:
    """Extract day of month."""
    dt = to.datetime(value)
    return dt.day

@transform
def hour(value: t.Any) -> int:
    """Extract hour (0-23)."""
    dt = to.datetime(value)
    return dt.hour

@transform
def minute(value: t.Any) -> int:
    """Extract minute (0-59)."""
    dt = to.datetime(value)
    return dt.minute

@transform
def second(value: t.Any) -> int:
    """Extract second (0-59)."""
    dt = to.datetime(value)
    return dt.second

@transform
def weekday(value: t.Any) -> int:
    """Extract weekday (0=Monday, 6=Sunday)."""
    dt = to.datetime(value)
    return dt.weekday()

@transform
def isoweekday(value: t.Any) -> int:
    """Extract ISO weekday (1=Monday, 7=Sunday)."""
    dt = to.datetime(value)
    return dt.isoweekday()

@transform
def dayofyear(value: t.Any) -> int:
    """Extract day of year (1-366)."""
    dt = to.datetime(value)
    return dt.timetuple().tm_yday

@transform
def week(value: t.Any) -> int:
    """Extract ISO week number."""
    dt = to.datetime(value)
    return dt.isocalendar()[1]

@transform
def quarter(value: t.Any) -> int:
    """Extract quarter (1-4)."""
    dt = to.datetime(value)
    return (dt.month - 1) // 3 + 1

# Date Boundaries

@transform
def startofday(value: t.Any) -> datetime:
    """Get start of day (00:00:00)."""
    dt = to.datetime(value)
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)

@transform
def endofday(value: t.Any) -> datetime:
    """Get end of day (23:59:59.999999)."""
    dt = to.datetime(value)
    return dt.replace(hour=23, minute=59, second=59, microsecond=999999)

@transform
def startofweek(value: t.Any) -> datetime:
    """Get start of week (Monday 00:00:00)."""
    dt = to.datetime(value)
    sincemonday = dt.weekday()
    start = dt - timedelta(days=sincemonday)
    return start.replace(hour=0, minute=0, second=0, microsecond=0)

@transform
def endofweek(value: t.Any) -> datetime:
    """Get end of week (Sunday 23:59:59.999999)."""
    dt = to.datetime(value)
    untilsunday = 6 - dt.weekday()
    end = dt + timedelta(days=untilsunday)
    return end.replace(hour=23, minute=59, second=59, microsecond=999999)

@transform
def startofmonth(value: t.Any) -> datetime:
    """Get start of month (1st day 00:00:00)."""
    dt = to.datetime(value)
    return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

@transform
def endofmonth(value: t.Any) -> datetime:
    """Get end of month (last day 23:59:59.999999)."""
    dt = to.datetime(value)
    lastday = calendar.monthrange(dt.year, dt.month)[1]
    return dt.replace(day=lastday, hour=23, minute=59, second=59, microsecond=999999)

@transform
def startofyear(value: t.Any) -> datetime:
    """Get start of year (Jan 1 00:00:00)."""
    dt = to.datetime(value)
    return dt.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

@transform
def endofyear(value: t.Any) -> datetime:
    """Get end of year (Dec 31 23:59:59.999999)."""
    dt = to.datetime(value)
    return dt.replace(month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)

# Timezone Operations

@transform
def utc(value: t.Any) -> datetime:
    """Convert to UTC timezone."""
    dt = to.datetime(value)
    if dt.tzinfo is None:
        # Assume naive datetime is UTC
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def totimezone(tz: t.Union[str, timezone]) -> Transform:
    """
    Convert to specific timezone.

    Args:
        tz: Timezone (string offset like '+05:00' or timezone object)

    Returns:
        Transform that converts to timezone
    """
    @transform(name=f"totimezone({tz})")
    def _totimezone(value: t.Any) -> datetime:
        dt = to.datetime(value)

        if isinstance(tz, str):
            # Parse timezone offset like '+05:00' or '-08:00'
            if tz.startswith(('+', '-')):
                sign = 1 if tz[0] == '+' else -1
                parts = tz[1:].split(':')
                hours = int(parts[0])
                minutes = int(parts[1]) if len(parts) > 1 else 0
                offset = timedelta(hours=hours, minutes=minutes) * sign
                targettz = timezone(offset)
            else:
                raise ValueError(f"Invalid timezone format: {tz}")
        else:
            targettz = tz

        if dt.tzinfo is None:
            # Assume naive datetime is UTC
            dt = dt.replace(tzinfo=timezone.utc)

        return dt.astimezone(targettz)
    return _totimezone

@transform
def naive(value: t.Any) -> datetime:
    """Remove timezone info (make naive)."""
    dt = to.datetime(value)
    return dt.replace(tzinfo=None)

# Relative Time

@transform
def age(value: t.Any) -> timedelta:
    """Calculate age (time since date)."""
    dt = to.datetime(value)
    now = datetime.now()
    return now - dt

@transform
def agehours(value: t.Any) -> float:
    """Calculate age in hours."""
    delta = age(value)
    return delta.total_seconds() / 3600

@transform
def agedays(value: t.Any) -> float:
    """Calculate age in days."""
    delta = age(value)
    return delta.total_seconds() / 86400

def since(reference: t.Any) -> Transform:
    """
    Calculate time since reference date.

    Args:
        reference: Reference date to compare with

    Returns:
        Transform that calculates time since reference
    """
    @transform(name=f"since({reference})")
    def _since(value: t.Any) -> timedelta:
        dt = to.datetime(value)
        ref = to.datetime(reference)
        return dt - ref
    return _since

def until(target: t.Any) -> Transform:
    """
    Calculate time until target date.

    Args:
        target: Target date

    Returns:
        Transform that calculates time until target
    """
    @transform(name=f"until({target})")
    def _until(value: t.Any) -> timedelta:
        dt = to.datetime(value)
        tgt = to.datetime(target)
        return tgt - dt
    return _until

# Validation and Predicates

def isbefore(other: t.Any) -> Transform:
    """
    Check if date is before another date.

    Args:
        other: Date to compare with

    Returns:
        Transform that checks if before
    """
    @transform(name=f"isbefore({other})")
    def _isbefore(value: t.Any) -> bool:
        dt1 = to.datetime(value)
        dt2 = to.datetime(other)
        return dt1 < dt2
    return _isbefore

def isafter(other: t.Any) -> Transform:
    """
    Check if date is after another date.

    Args:
        other: Date to compare with

    Returns:
        Transform that checks if after
    """
    @transform(name=f"isafter({other})")
    def _isafter(value: t.Any) -> bool:
        dt1 = to.datetime(value)
        dt2 = to.datetime(other)
        return dt1 > dt2
    return _isafter

def isbetween(start: t.Any, end: t.Any, inclusive: bool = True) -> Transform:
    """
    Check if date is between two dates.

    Args:
        start: Start date
        end: End date
        inclusive: Whether boundaries are inclusive

    Returns:
        Transform that checks if between dates
    """
    @transform(name=f"isbetween({start}, {end})")
    def _isbetween(value: t.Any) -> bool:
        dt = to.datetime(value)
        start_dt = to.datetime(start)
        end_dt = to.datetime(end)

        if inclusive:
            return start_dt <= dt <= end_dt
        else:
            return start_dt < dt < end_dt
    return _isbetween

@transform
def isweekend(value: t.Any) -> bool:
    """Check if date is weekend (Saturday or Sunday)."""
    dt = to.datetime(value)
    return dt.weekday() >= 5

@transform
def isweekday(value: t.Any) -> bool:
    """Check if date is weekday (Monday-Friday)."""
    dt = to.datetime(value)
    return dt.weekday() < 5

@transform
def isleapyear(value: t.Any) -> bool:
    """Check if date's year is a leap year."""
    dt = to.datetime(value)
    return calendar.isleap(dt.year)

# Special Date Generation

@transform
def now() -> datetime:
    """Get current datetime."""
    return datetime.now()

@transform
def today() -> date:
    """Get current date."""
    return date.today()

@transform
def utcnow() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)
