# ~/schematix/src/schematix/transforms/common.py
"""
Common transformation patterns combining text, numbers, dates, collections, and validation.
These are the most frequently used transforms in real-world data processing.
"""
from __future__ import annotations
import typing as t

from schematix.core.transform import transform, Transform, pipeline
from schematix.transforms import text, numbers, dates, collections as col, validation as val

# Text Processing
class clean:
    """Common cleaning transforms."""

    @transform
    @staticmethod
    def text(value: t.Any) -> str:
        """Clean text: strip, normalize whitespace."""
        return pipeline(
            text.strip,
            text.normalizewhitespace
        )(value)

    @transform
    @staticmethod
    def name(value: t.Any) -> str:
        """Clean person/company name: strip, normalize, title case."""
        return pipeline(
            text.strip,
            text.normalizewhitespace,
            text.title
        )(value)

    @transform
    @staticmethod
    def email(value: t.Any) -> str:
        """Clean and validate email: normalize, validate."""
        return pipeline(
            val.clean.email,
            val.requires.email()
        )(value)

    @transform
    @staticmethod
    def phone(value: t.Any) -> str:
        """Clean phone number: remove formatting."""
        return pipeline(
            val.clean.phone,
            val.requires.notempty("Phone number cannot be empty")
        )(value)

    @transform
    @staticmethod
    def price(value: t.Any) -> float:
        """Clean price string to float: '$1,234.56' -> 1234.56"""
        return pipeline(
            text.regexreplace(r'[^0-9.-]', ''),
            numbers.to.float
        )(value)

    @transform
    @staticmethod
    def url(value: t.Any) -> str:
        """Clean and normalize URL."""
        return pipeline(
            val.clean.url,
            val.requires.notempty("URL cannot be empty")
        )(value)

    class safe:
        @transform
        @staticmethod
        def email(default: str = "") -> Transform:
            """Safely clean email with fallback."""
            @transform(name=f"clean.safeemail({default!r})")
            def _safeemail(value: t.Any) -> str:
                try:
                    return clean.email(value)
                except ValueError:
                    return default
            return _safeemail

class format:
    """Common formatting transforms."""

    @transform
    @staticmethod
    def titlecase(value: t.Any) -> str:
        """Clean and title case text."""
        return pipeline(
            text.strip,
            text.title
        )(value)

    @transform
    @staticmethod
    def slug(value: t.Any) -> str:
        """Convert text to URL slug."""
        return pipeline(
            text.strip,
            text.slug
        )(value)

    @transform
    @staticmethod
    def phone(value: t.Any) -> str:
        """Format US phone as (XXX) XXX-XXXX."""
        cleaned = val.clean.phone()(value)
        if cleaned.startswith('+1'):
            cleaned = cleaned[2:]
        elif cleaned.startswith('1') and len(cleaned) == 11:
            cleaned = cleaned[1:]

        if len(cleaned) == 10:
            return f"({cleaned[:3]}) {cleaned[3:6]}-{cleaned[6:]}"
        return cleaned

    @transform
    @staticmethod
    def currency(value: t.Any) -> str:
        """Convert to currency format: $1,234.56"""
        return pipeline(
            numbers.to.float,
            numbers.format.currency()
        )(value)

    @transform
    @staticmethod
    def percentage(value: t.Any) -> str:
        """Convert to percentage format: 45.6%"""
        return pipeline(
            numbers.to.float,
            numbers.format.percent()
        )(value)

class parse:
    """Common parsing transforms."""

    @transform
    @staticmethod
    def date(value: t.Any) -> str:
        """Parse date and format as YYYY-MM-DD."""
        return pipeline(
            dates.parse.auto,
            dates.format.date
        )(value)

    @transform
    @staticmethod
    def datetime(value: t.Any) -> str:
        """Parse datetime and format as YYYY-MM-DD HH:MM:SS."""
        return pipeline(
            dates.parse.auto,
            dates.format.datetime
        )(value)

    @transform
    @staticmethod
    def readabledate(value: t.Any) -> str:
        """Parse date in readable format: December 25, 2023"""
        return pipeline(
            dates.parse.auto,
            dates.format.readable
        )(value)

    @transform
    @staticmethod
    def number(value: t.Any) -> float:
        """Safely parse number with fallback to 0."""
        return numbers.safeto.float(0.0)(value)

    @transform
    @staticmethod
    def integer(value: t.Any) -> int:
        """Safely parse integer with fallback to 0."""
        return numbers.safeto.int(0)(value)

# Safe Operations
class safe:
    """Safe transforms that don't raise errors."""

    @staticmethod
    def get(key: t.Any, default: t.Any = None) -> Transform:
        """Safely get value from dict/object."""
        return col.get(key, default)

    @staticmethod
    def first(default: t.Any = None) -> Transform:
        """Safely get first item with fallback."""
        @transform(name=f"safe.first({default!r})")
        def _safefirst(value: t.Any) -> t.Any:
            try:
                result = col.first(value)
                return result if result is not None else default
            except:
                return default
        return _safefirst

    @staticmethod
    def last(default: t.Any = None) -> Transform:
        """Safely get last item with fallback."""
        @transform(name=f"safe.last({default!r})")
        def _safelast(value: t.Any) -> t.Any:
            try:
                result = col.last()(value)
                return result if result is not None else default
            except:
                return default
        return _safelast

    @staticmethod
    def length(default: int = 0) -> Transform:
        """Safely get length with fallback."""
        @transform(name=f"safe.length({default})")
        def _safelength(value: t.Any) -> int:
            try:
                return col.length()(value)
            except:
                return default
        return _safelength

# Common Data Processing Patterns
class extract:
    """Common data extraction patterns."""

    @transform
    @staticmethod
    def emails(value: t.Any) -> t.List[str]:
        """Extract all email addresses from text."""
        return text.regexfindall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')(value)

    @transform
    @staticmethod
    def urls(value: t.Any) -> t.List[str]:
        """Extract all URLs from text."""
        return text.regexfindall(r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?')(value)

    @transform
    @staticmethod
    def numbers(value: t.Any) -> t.List[str]:
        """Extract all numbers from text."""
        return text.regexfindall(r'\d+(?:\.\d+)?')(value)

    @transform
    @staticmethod
    def phones(value: t.Any) -> t.List[str]:
        """Extract US phone numbers from text."""
        return text.regexfindall(r'\+?1?[-.\s]?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})')(value)

class lists:
    """Common list processing patterns."""

    @transform
    @staticmethod
    def cleanedemails(value: t.Any) -> t.List[str]:
        """Clean list of emails, remove invalid ones."""
        emailsafetransform = clean.safe.email("")
        return pipeline(
            col.map(emailsafetransform),
            col.filter(lambda x: x != ""),
            col.unique
        )(value)

    @transform
    @staticmethod
    def cleanednames(value: t.Any) -> t.List[str]:
        """Clean list of names."""
        return pipeline(
            col.map(clean.name),
            col.filter(val.notempty),
            col.unique
        )(value)

    @transform
    @staticmethod
    def sortalpha(value: t.Any) -> t.List[t.Any]:
        """Sort list alphabetically."""
        return col.sort()(value)

    @transform
    @staticmethod
    def dedupe(value: t.Any) -> t.List[t.Any]:
        """Remove duplicates from list."""
        return col.unique()(value)

# Validation Shortcuts
class validate:
    """Common validation patterns."""

    @transform
    @staticmethod
    def email(value: t.Any) -> t.Any:
        """Validate email format."""
        requirement = val.requires.email()
        return requirement(value)

    @transform
    @staticmethod
    def notempty(value: t.Any) -> t.Any:
        """Validate not empty."""
        requirement = val.requires.notempty()
        return requirement(value)

    @staticmethod
    def length(minlen: int, maxlen: t.Optional[int] = None) -> Transform:
        """Validate length range."""
        return val.requires.length(minlen, maxlen)

    @staticmethod
    def inrange(minval: t.Union[int, float], maxval: t.Union[int, float]) -> Transform:
        """Validate number in range."""
        return val.inrange.float(minval, maxval)

# Common Pipelines

class pipelines:
    """Pre-built transformation pipelines for common use cases."""

    @transform
    @staticmethod
    def userdata(value: t.Any) -> t.Dict[str, t.Any]:
        """Process user data dict: clean name, email, phone."""
        data = dict(value) if isinstance(value, dict) else {}

        result = {}
        if 'name' in data:
            result['name'] = clean.name(data['name'])
        if 'email' in data:
            emailsafetransform = clean.safe.email("")
            result['email'] = emailsafetransform(data['email'])
        if 'phone' in data:
            result['phone'] = clean.phone(data['phone'])

        return result

    @transform
    @staticmethod
    def contactinfo(value: t.Any) -> t.Dict[str, t.Any]:
        """Process contact info: clean and validate all fields."""
        data = dict(value) if isinstance(value, dict) else {}

        result = {}
        for field in ['name', 'email', 'phone', 'company']:
            if field in data:
                if field == 'email':
                    result[field] = clean.safeemail()(data[field])
                elif field in ['name', 'company']:
                    result[field] = clean.name()(data[field])
                elif field == 'phone':
                    try:
                        result[field] = clean.phone()(data[field])
                    except:
                        result[field] = ""
                else:
                    result[field] = clean.text()(data[field])

        return result

    @transform
    @staticmethod
    def productdata(value: t.Any) -> t.Dict[str, t.Any]:
        """Process product data: clean name, price, description."""
        data = dict(value) if isinstance(value, dict) else {}

        result = {}
        if 'name' in data:
            result['name'] = clean.name()(data['name'])
        if 'price' in data:
            try:
                result['price'] = clean.price()(data['price'])
            except:
                result['price'] = 0.0
        if 'description' in data:
            result['description'] = clean.text()(data['description'])

        return result

# Utility Transforms

@transform
def identity(value: t.Any) -> t.Any:
    """Identity transform - returns value unchanged."""
    return value

@transform
def debug(value: t.Any) -> t.Any:
    """Debug transform - prints value and returns it."""
    print(f"DEBUG: {value!r}")
    return value

def constant(const_value: t.Any) -> Transform:
    """Transform that always returns the same constant value."""
    @transform(name=f"constant({const_value!r})")
    def _constant(value: t.Any) -> t.Any:
        return const_value
    return _constant

def default(default_value: t.Any) -> Transform:
    """Transform that returns default if input is None/empty."""
    @transform(name=f"default({default_value!r})")
    def _default(value: t.Any) -> t.Any:
        if value is None:
            return default_value
        if isinstance(value, str) and not value.strip():
            return default_value
        try:
            if len(value) == 0:
                return default_value
        except TypeError:
            pass
        return value
    return _default
