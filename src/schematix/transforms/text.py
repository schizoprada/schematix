# ~/schematix/src/schematix/transforms/text.py
"""
Text transformation functions for string manipulation and formatting.
"""
from __future__ import annotations
import re, unicodedata, typing as t

from schematix.core.transform import transform, Transform

# Basic String Operations

@transform
def strip(value: t.Any) -> str:
    """Remove leading and trailing whitespace."""
    return str(value).strip()

@transform
def upper(value: t.Any) -> str:
    """Convert to uppercase."""
    return str(value).upper()

@transform
def lower(value: t.Any) -> str:
    """Convert to lowercase."""
    return str(value).lower()

@transform
def title(value: t.Any) -> str:
    """Convert to title case."""
    return str(value).title()

@transform
def capitalize(value: t.Any) -> str:
    """Capitalize first letter only."""
    return str(value).capitalize()

@transform
def swapcase(value: t.Any) -> str:
    """Swap case of all letters."""
    return str(value).swapcase()

# String Replacement and Cleaning

def replace(old: str, new: str, count: int = -1) -> Transform:
    """
    Replace occurrences of old substring with new substring.

    Args:
        old: Substring to replace
        new: Replacement substring
        count: Maximum number of replacements (-1 for all)

    Returns:
        Transform that performs the replacement
    """
    @transform(name=f"replace('{old}' -> '{new}')")
    def _replace(value: t.Any) -> str:
        return str(value).replace(old, new, count)
    return _replace

def removeprefix(prefix: str) -> Transform:
    """
    Remove prefix from start of string if present.

    Args:
        prefix: Prefix to remove

    Returns:
        Transform that removes the prefix
    """
    @transform(name=f"removeprefix('{prefix}')")
    def _removeprefix(value: t.Any) -> str:
        s = str(value)
        return s.removeprefix(prefix) if hasattr(s, 'removeprefix') else s[len(prefix):] if s.startswith(prefix) else s
    return _removeprefix

def removesuffix(suffix: str) -> Transform:
    """
    Remove suffix from end of string if present.

    Args:
        suffix: Suffix to remove

    Returns:
        Transform that removes the suffix
    """
    @transform(name=f"removesuffix('{suffix}')")
    def _removesuffix(value: t.Any) -> str:
        s = str(value)
        return s.removesuffix(suffix) if hasattr(s, 'removesuffix') else s[:-len(suffix)] if s.endswith(suffix) else s
    return _removesuffix

def lstrip(chars: t.Optional[str] = None) -> Transform:
    """
    Remove characters from left side of string.

    Args:
        chars: Characters to remove (default: whitespace)

    Returns:
        Transform that strips left side
    """
    @transform(name=f"lstrip({chars!r})")
    def _lstrip(value: t.Any) -> str:
        return str(value).lstrip(chars)
    return _lstrip

def rstrip(chars: t.Optional[str] = None) -> Transform:
    """
    Remove characters from right side of string.

    Args:
        chars: Characters to remove (default: whitespace)

    Returns:
        Transform that strips right side
    """
    @transform(name=f"rstrip({chars!r})")
    def _rstrip(value: t.Any) -> str:
        return str(value).rstrip(chars)
    return _rstrip

# Regular Expression Operations

def regexextract(pattern: str, group: int = 0, flags: int = 0) -> Transform:
    """
    Extract text using regular expression.

    Args:
        pattern: Regular expression pattern
        group: Group number to extract (0 for full match)
        flags: Regex flags (re.IGNORECASE, etc.)

    Returns:
        Transform that extracts matching text
    """
    compiled = re.compile(pattern, flags)

    @transform(name=f"regexextract('{pattern}')")
    def _regexextract(value: t.Any) -> str:
        match = compiled.search(str(value))
        if match:
            return match.group(group)
        return ""
    return _regexextract

def regexreplace(pattern: str, replacement: str, count: int = 0, flags: int = 0) -> Transform:
    """
    Replace text using regular expression.

    Args:
        pattern: Regular expression pattern
        replacement: Replacement string
        count: Maximum replacements (0 for all)
        flags: Regex flags

    Returns:
        Transform that performs regex replacement
    """
    compiled = re.compile(pattern, flags)

    @transform(name=f"regexreplace('{pattern}' -> '{replacement}')")
    def _regexreplace(value: t.Any) -> str:
        return compiled.sub(replacement, str(value), count=count)
    return _regexreplace

def regexfindall(pattern: str, flags: int = 0) -> Transform:
    """
    Find all matches of a regular expression.

    Args:
        pattern: Regular expression pattern
        flags: Regex flags

    Returns:
        Transform that returns list of all matches
    """
    compiled = re.compile(pattern, flags)

    @transform(name=f"regexfindall('{pattern}')")
    def _regexfindall(value: t.Any) -> t.List[str]:
        return compiled.findall(str(value))
    return _regexfindall

# String Formatting and Length Operations

def truncate(length: int, suffix: str = "...") -> Transform:
    """
    Truncate string to maximum length.

    Args:
        length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Transform that truncates the string
    """
    @transform(name=f"truncate({length})")
    def _truncate(value: t.Any) -> str:
        s = str(value)
        if len(s) <= length:
            return s
        return s[:length - len(suffix)] + suffix
    return _truncate

def padleft(width: int, fillchar: str = " ") -> Transform:
    """
    Pad string on left to specified width.

    Args:
        width: Total width
        fillchar: Character to pad with

    Returns:
        Transform that pads the string
    """
    @transform(name=f"padleft({width})")
    def _padleft(value: t.Any) -> str:
        return str(value).rjust(width, fillchar)
    return _padleft

def padright(width: int, fillchar: str = " ") -> Transform:
    """
    Pad string on right to specified width.

    Args:
        width: Total width
        fillchar: Character to pad with

    Returns:
        Transform that pads the string
    """
    @transform(name=f"padright({width})")
    def _padright(value: t.Any) -> str:
        return str(value).ljust(width, fillchar)
    return _padright

def center(width: int, fillchar: str = " ") -> Transform:
    """
    Center string within specified width.

    Args:
        width: Total width
        fillchar: Character to pad with

    Returns:
        Transform that centers the string
    """
    @transform(name=f"center({width})")
    def _center(value: t.Any) -> str:
        return str(value).center(width, fillchar)
    return _center

def zfill(width: int) -> Transform:
    """
    Pad numeric string with zeros on left.

    Args:
        width: Total width

    Returns:
        Transform that zero-fills the string
    """
    @transform(name=f"zfill({width})")
    def _zfill(value: t.Any) -> str:
        return str(value).zfill(width)
    return _zfill

# String Splitting and Joining

def split(sep: t.Optional[str] = None, maxsplit: int = -1) -> Transform:
    """
    Split string into list.

    Args:
        sep: Separator (default: any whitespace)
        maxsplit: Maximum splits

    Returns:
        Transform that splits the string
    """
    @transform(name=f"split({sep!r})")
    def _split(value: t.Any) -> t.List[str]:
        return str(value).split(sep, maxsplit)
    return _split

def rsplit(sep: t.Optional[str] = None, maxsplit: int = -1) -> Transform:
    """
    Split string from right into list.

    Args:
        sep: Separator (default: any whitespace)
        maxsplit: Maximum splits

    Returns:
        Transform that splits the string from right
    """
    @transform(name=f"rsplit({sep!r})")
    def _rsplit(value: t.Any) -> t.List[str]:
        return str(value).rsplit(sep, maxsplit)
    return _rsplit

def splitlines(keepends: bool = False) -> Transform:
    """
    Split string at line boundaries.

    Args:
        keepends: Whether to keep line ending characters

    Returns:
        Transform that splits into lines
    """
    @transform(name=f"splitlines({keepends})")
    def _splitlines(value: t.Any) -> t.List[str]:
        return str(value).splitlines(keepends)
    return _splitlines

def join(sep: str) -> Transform:
    """
    Join sequence of strings with separator.

    Args:
        sep: Separator string

    Returns:
        Transform that joins strings
    """
    @transform(name=f"join('{sep}')")
    def _join(value: t.Any) -> str:
        if isinstance(value, str):
            # If it's already a string, return as-is
            return value
        try:
            # Try to join as sequence
            return sep.join(str(item) for item in value)
        except TypeError:
            # Not iterable, convert to string
            return str(value)
    return _join

# Specialized Text Operations

@transform
def slug(value: t.Any) -> str:
    """
    Convert text to URL-friendly slug.

    Converts to lowercase, replaces spaces/special chars with hyphens,
    removes consecutive hyphens and leading/trailing hyphens.
    """
    # Convert to string and normalize unicode
    text = str(value)
    text = unicodedata.normalize('NFKD', text)

    # Convert to ASCII, ignoring non-ASCII chars
    text = text.encode('ascii', 'ignore').decode('ascii')

    # Convert to lowercase
    text = text.lower()

    # Replace non-alphanumeric with hyphens
    text = re.sub(r'[^a-z0-9]+', '-', text)

    # Remove leading/trailing hyphens and collapse multiple hyphens
    text = re.sub(r'^-+|-+$', '', text)
    text = re.sub(r'-+', '-', text)

    return text

@transform
def normalizewhitespace(value: t.Any) -> str:
    """
    Normalize whitespace by collapsing multiple spaces into single spaces.
    """
    return re.sub(r'\s+', ' ', str(value).strip())

@transform
def reverse(value: t.Any) -> str:
    """Reverse the string."""
    return str(value)[::-1]

def startswith(prefix: str) -> Transform:
    """
    Check if string starts with prefix.

    Args:
        prefix: Prefix to check for

    Returns:
        Transform that returns boolean
    """
    @transform(name=f"startswith('{prefix}')")
    def _startswith(value: t.Any) -> bool:
        return str(value).startswith(prefix)
    return _startswith

def endswith(suffix: str) -> Transform:
    """
    Check if string ends with suffix.

    Args:
        suffix: Suffix to check for

    Returns:
        Transform that returns boolean
    """
    @transform(name=f"endswith('{suffix}')")
    def _endswith(value: t.Any) -> bool:
        return str(value).endswith(suffix)
    return _endswith

def contains(substring: str, casesensitive: bool = True) -> Transform:
    """
    Check if string contains substring.

    Args:
        substring: Substring to search for
        casesensitive: Whether search is case sensitive

    Returns:
        Transform that returns boolean
    """
    @transform(name=f"contains('{substring}')")
    def _contains(value: t.Any) -> bool:
        text = str(value)
        search = substring
        if not casesensitive:
            text = text.lower()
            search = search.lower()
        return search in text
    return _contains

class encode:
    @transform
    @staticmethod
    def base64(value: t.Any) -> str:
        """Encode string as base64."""
        import base64
        return base64.b64encode(str(value).encode('utf-8')).decode('ascii')

    @transform
    @staticmethod
    def url(value: t.Any) -> str:
        """URL encode string."""
        import urllib.parse
        return urllib.parse.quote(str(value))


class decode:
    @transform
    @staticmethod
    def base64(value: t.Any) -> str:
        """Decode base64 string."""
        import base64
        return base64.b64decode(str(value)).decode('utf-8')

    @transform
    @staticmethod
    def url(value: t.Any) -> str:
        """URL decode string."""
        import urllib.parse
        return urllib.parse.unquote(str(value))

class html:
    @transform
    @staticmethod
    def escape(value: t.Any) -> str:
        """Escape HTML special characters."""
        import html
        return html.escape(str(value))

    @transform
    @staticmethod
    def unescape(value: t.Any) -> str:
        """Unescape HTML entities."""
        import html
        return html.unescape(str(value))
