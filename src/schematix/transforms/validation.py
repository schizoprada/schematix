# ~/schematix/src/schematix/transforms/validation.py
"""
Validation transformation functions for data validation and cleaning.
"""
from __future__ import annotations
import re, typing as t, urllib.parse

from schematix.core.transform import transform, Transform

# Regex patterns for common validations
PATTERNS = {
    'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
    'phoneus': r'^\+?1?[-.\s]?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})',
    'phoneintl': r'^\+?[1-9]\d{1,14}',
    'url': r'^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?',
    'ipv4': r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)',
    'ipv6': r'^(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}',
    'mac': r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})',
    'uuid': r'^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}',
    'creditcard': r'^(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3[0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})',
    'ssn': r'^\d{3}-?\d{2}-?\d{4}',
    'zipcode': r'^\d{5}(?:-\d{4})?',
    'alphanumeric': r'^[a-zA-Z0-9]+',
    'alpha': r'^[a-zA-Z]+',
    'numeric': r'^\d+',
    'hexcolor': r'^#(?:[0-9a-fA-F]{3}){1,2}',
}

# Basic Validation

class isa:
    """Basic type and format validation transforms."""

    @transform
    @staticmethod
    def email(value: t.Any) -> bool:
        """Validate email format."""
        text = str(value).strip().lower()
        return bool(re.match(PATTERNS['email'], text))

    @transform
    @staticmethod
    def url(value: t.Any) -> bool:
        """Validate URL format."""
        text = str(value).strip()
        return bool(re.match(PATTERNS['url'], text))

    @transform
    @staticmethod
    def phoneus(value: t.Any) -> bool:
        """Validate US phone number format."""
        text = str(value).strip()
        return bool(re.match(PATTERNS['phoneus'], text))

    @transform
    @staticmethod
    def phoneintl(value: t.Any) -> bool:
        """Validate international phone number format."""
        text = str(value).strip()
        return bool(re.match(PATTERNS['phoneintl'], text))

    @transform
    @staticmethod
    def ipv4(value: t.Any) -> bool:
        """Validate IPv4 address format."""
        text = str(value).strip()
        return bool(re.match(PATTERNS['ipv4'], text))

    @transform
    @staticmethod
    def ipv6(value: t.Any) -> bool:
        """Validate IPv6 address format."""
        text = str(value).strip()
        return bool(re.match(PATTERNS['ipv6'], text))

    @transform
    @staticmethod
    def mac(value: t.Any) -> bool:
        """Validate MAC address format."""
        text = str(value).strip()
        return bool(re.match(PATTERNS['mac'], text))

    @transform
    @staticmethod
    def uuid(value: t.Any) -> bool:
        """Validate UUID format."""
        text = str(value).strip().lower()
        return bool(re.match(PATTERNS['uuid'], text))

    @transform
    @staticmethod
    def creditcard(value: t.Any) -> bool:
        """Validate credit card number format."""
        text = re.sub(r'[\s-]', '', str(value))
        return bool(re.match(PATTERNS['creditcard'], text))

    @transform
    @staticmethod
    def ssn(value: t.Any) -> bool:
        """Validate Social Security Number format."""
        text = str(value).strip()
        return bool(re.match(PATTERNS['ssn'], text))

    @transform
    @staticmethod
    def zipcode(value: t.Any) -> bool:
        """Validate US ZIP code format."""
        text = str(value).strip()
        return bool(re.match(PATTERNS['zipcode'], text))

    @transform
    @staticmethod
    def alphanumeric(value: t.Any) -> bool:
        """Check if contains only letters and numbers."""
        text = str(value).strip()
        return bool(re.match(PATTERNS['alphanumeric'], text))

    @transform
    @staticmethod
    def alpha(value: t.Any) -> bool:
        """Check if contains only letters."""
        text = str(value).strip()
        return bool(re.match(PATTERNS['alpha'], text))

    @transform
    @staticmethod
    def numeric(value: t.Any) -> bool:
        """Check if contains only digits."""
        text = str(value).strip()
        return bool(re.match(PATTERNS['numeric'], text))

    @transform
    @staticmethod
    def hexcolor(value: t.Any) -> bool:
        """Validate hex color format."""
        text = str(value).strip()
        return bool(re.match(PATTERNS['hexcolor'], text))

# String Content Validation

class has:
    """Content validation transforms."""

    @staticmethod
    def length(minlen: int, maxlen: t.Optional[int] = None) -> Transform:
        """
        Validate string length.

        Args:
            minlen: Minimum length
            maxlen: Maximum length (optional)

        Returns:
            Transform that validates length
        """
        @transform(name=f"has.length({minlen}, {maxlen})")
        def _haslength(value: t.Any) -> bool:
            text = str(value)
            if maxlen is None:
                return len(text) >= minlen
            return minlen <= len(text) <= maxlen
        return _haslength

    @staticmethod
    def pattern(regex: str, flags: int = 0) -> Transform:
        """
        Validate against custom regex pattern.

        Args:
            regex: Regular expression pattern
            flags: Regex flags

        Returns:
            Transform that validates pattern
        """
        compiled = re.compile(regex, flags)

        @transform(name=f"has.pattern('{regex}')")
        def _haspattern(value: t.Any) -> bool:
            return bool(compiled.search(str(value)))
        return _haspattern

    @staticmethod
    def substring(substr: str, casesensitive: bool = True) -> Transform:
        """
        Check if contains substring.

        Args:
            substr: Substring to search for
            casesensitive: Whether search is case sensitive

        Returns:
            Transform that checks for substring
        """
        @transform(name=f"has.substring('{substr}')")
        def _hassubstring(value: t.Any) -> bool:
            text = str(value)
            search = substr
            if not casesensitive:
                text = text.lower()
                search = search.lower()
            return search in text
        return _hassubstring

    @transform
    @staticmethod
    def uppercase(value: t.Any) -> bool:
        """Check if string has any uppercase letters."""
        text = str(value)
        return any(c.isupper() for c in text)

    @transform
    @staticmethod
    def lowercase(value: t.Any) -> bool:
        """Check if string has any lowercase letters."""
        text = str(value)
        return any(c.islower() for c in text)

    @transform
    @staticmethod
    def digits(value: t.Any) -> bool:
        """Check if string contains digits."""
        text = str(value)
        return any(c.isdigit() for c in text)

    @transform
    @staticmethod
    def specialchars(value: t.Any) -> bool:
        """Check if string contains special characters."""
        text = str(value)
        return any(not c.isalnum() and not c.isspace() for c in text)

# Numeric Validation

class inrange:
    """Numeric range validation transforms."""

    @staticmethod
    def int(minval: int, maxval: int, inclusive: bool = True) -> Transform:
        """
        Validate integer is in range.

        Args:
            minval: Minimum value
            maxval: Maximum value
            inclusive: Whether bounds are inclusive

        Returns:
            Transform that validates integer range
        """
        @transform(name=f"inrange.int({minval}, {maxval})")
        def _inrangeint(value: t.Any) -> bool:
            try:
                num = int(value)
                if inclusive:
                    return minval <= num <= maxval
                else:
                    return minval < num < maxval
            except (ValueError, TypeError):
                return False
        return _inrangeint

    @staticmethod
    def float(minval: float, maxval: float, inclusive: bool = True) -> Transform:
        """
        Validate float is in range.

        Args:
            minval: Minimum value
            maxval: Maximum value
            inclusive: Whether bounds are inclusive

        Returns:
            Transform that validates float range
        """
        @transform(name=f"inrange.float({minval}, {maxval})")
        def _inrangefloat(value: t.Any) -> bool:
            try:
                num = float(value)
                if inclusive:
                    return minval <= num <= maxval
                else:
                    return minval < num < maxval
            except (ValueError, TypeError):
                return False
        return _inrangefloat

# Type Validation

class canbe:
    """Type conversion validation transforms."""

    @transform
    @staticmethod
    def int(value: t.Any) -> bool:
        """Check if value can be converted to int."""
        try:
            int(value)
            return True
        except (ValueError, TypeError):
            return False

    @transform
    @staticmethod
    def float(value: t.Any) -> bool:
        """Check if value can be converted to float."""
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False

    @transform
    @staticmethod
    def bool(value: t.Any) -> bool:
        """Check if value can be converted to bool."""
        if isinstance(value, bool):
            return True
        if isinstance(value, str):
            return value.lower() in ('true', 'false', '1', '0', 'yes', 'no', 'on', 'off')
        return isinstance(value, (int, float))

# Content Checks

@transform
def notempty(value: t.Any) -> bool:
    """Check if value is not empty."""
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    try:
        return len(value) > 0
    except TypeError:
        return True

@transform
def notnull(value: t.Any) -> bool:
    """Check if value is not None."""
    return value is not None

@transform
def isblank(value: t.Any) -> bool:
    """Check if string is blank (empty or whitespace only)."""
    if value is None:
        return True
    return not bool(str(value).strip())

# List/Collection Validation

class collection:
    """Collection validation transforms."""

    @staticmethod
    def minlength(minlen: int) -> Transform:
        """
        Validate collection has minimum length.

        Args:
            minlen: Minimum length

        Returns:
            Transform that validates minimum length
        """
        @transform(name=f"collection.minlength({minlen})")
        def _minlength(value: t.Any) -> bool:
            try:
                return len(value) >= minlen
            except TypeError:
                return False
        return _minlength

    @staticmethod
    def maxlength(maxlen: int) -> Transform:
        """
        Validate collection has maximum length.

        Args:
            maxlen: Maximum length

        Returns:
            Transform that validates maximum length
        """
        @transform(name=f"collection.maxlength({maxlen})")
        def _maxlength(value: t.Any) -> bool:
            try:
                return len(value) <= maxlen
            except TypeError:
                return False
        return _maxlength

    @staticmethod
    def contains(item: t.Any) -> Transform:
        """
        Check if collection contains item.

        Args:
            item: Item to search for

        Returns:
            Transform that checks for item
        """
        @transform(name=f"collection.contains({item!r})")
        def _contains(value: t.Any) -> bool:
            try:
                return item in value
            except TypeError:
                return False
        return _contains

    @staticmethod
    def allitems(predicate: t.Callable[[t.Any], bool]) -> Transform:
        """
        Check if all items in collection match predicate.

        Args:
            predicate: Function to test each item

        Returns:
            Transform that validates all items
        """
        @transform(name=f"collection.allitems({predicate.__name__ if hasattr(predicate, '__name__') else 'predicate'})")
        def _allitems(value: t.Any) -> bool:
            try:
                return all(predicate(item) for item in value)
            except TypeError:
                return predicate(value)
        return _allitems

    @staticmethod
    def anyitem(predicate: t.Callable[[t.Any], bool]) -> Transform:
        """
        Check if any item in collection matches predicate.

        Args:
            predicate: Function to test each item

        Returns:
            Transform that validates any item
        """
        @transform(name=f"collection.anyitem({predicate.__name__ if hasattr(predicate, '__name__') else 'predicate'})")
        def _anyitem(value: t.Any) -> bool:
            try:
                return any(predicate(item) for item in value)
            except TypeError:
                return predicate(value)
        return _anyitem

# Cleaning/Sanitization

class clean:
    """Data cleaning transforms."""

    @transform
    @staticmethod
    def email(value: t.Any) -> str:
        """Clean and normalize email address."""
        email = str(value).strip().lower()
        # Remove extra spaces and normalize
        email = re.sub(r'\s+', '', email)
        return email

    @transform
    @staticmethod
    def phone(value: t.Any) -> str:
        """Clean phone number (remove formatting)."""
        phone = str(value).strip()
        # Remove all non-digit characters except +
        cleaned = re.sub(r'[^\d+]', '', phone)
        return cleaned

    @transform
    @staticmethod
    def url(value: t.Any) -> str:
        """Clean and normalize URL."""
        url = str(value).strip()
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        return url.lower()

    @transform
    @staticmethod
    def whitespace(value: t.Any) -> str:
        """Clean excess whitespace."""
        text = str(value)
        # Replace multiple whitespace with single space
        return re.sub(r'\s+', ' ', text).strip()

    @transform
    @staticmethod
    def alphanumeric(value: t.Any) -> str:
        """Keep only alphanumeric characters."""
        text = str(value)
        return re.sub(r'[^a-zA-Z0-9]', '', text)

    @staticmethod
    def removepattern(pattern: str, replacement: str = '') -> Transform:
        """
        Remove pattern from string.

        Args:
            pattern: Regex pattern to remove
            replacement: Replacement string

        Returns:
            Transform that removes pattern
        """
        compiled = re.compile(pattern)

        @transform(name=f"clean.removepattern('{pattern}')")
        def _removepattern(value: t.Any) -> str:
            return compiled.sub(replacement, str(value))
        return _removepattern

# Require/Assert Transforms

def require(condition: t.Callable[[t.Any], bool], message: str = "Validation failed") -> Transform:
    """
    Require condition to be true, raise error if not.

    Args:
        condition: Condition function that must return True
        message: Error message if condition fails

    Returns:
        Transform that enforces condition
    """
    @transform(name=f"require({condition.__name__ if hasattr(condition, '__name__') else 'condition'})")
    def _require(value: t.Any) -> t.Any:
        if not condition(value):
            raise ValueError(f"{message}: {value}")
        return value
    return _require


class requires:
    @staticmethod
    def email(message: str = "Invalid email format") -> Transform:
        """Require valid email format."""
        return require(isa.email, message)

    @staticmethod
    def notempty(message: str = "Value cannot be empty") -> Transform:
        """Require non-empty value."""
        return require(notempty, message)

    @staticmethod
    def length(minlen: int, maxlen: t.Optional[int] = None, message: t.Optional[str] = None) -> Transform:
        """Require specific length range."""
        if message is None:
            if maxlen is None:
                message = f"Length must be at least {minlen}"
            else:
                message = f"Length must be between {minlen} and {maxlen}"

        condition = has.length(minlen, maxlen)
        return require(condition, message)
