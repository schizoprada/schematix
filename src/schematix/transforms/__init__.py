# ~/schematix/src/schematix/transforms/__init__.py
from . import (
    text, numbers, collections, dates, validation, common
)

txt = text
num = numbers
col = collections
dt = dates
val = validation
com = common

__all__ = [
    'text',
    'numbers',
    'collections',
    'dates',
    'validation',
    'common',
    'txt',
    'num',
    'col',
    'dt',
    'val',
    'com'
]

"""
TODO: Transform API Consistency (05/29/2025)
--------------------------------------------

Current transform calling patterns are inconsistent and confusing:
1. @transform decorated functions → use directly (no parentheses)
   Example: text.strip, numbers.abs, col.first

2. Factory functions that return Transforms → use with ()
   Example: text.replace("old", "new"), numbers.add(5), col.filter(predicate)

3. @staticmethod @transform methods → call with () to get Transform instance
   Example: numbers.to.int(), dates.parse.auto(), common.clean.text()

This inconsistency causes:
- Developer confusion about when to use () vs not
- Runtime errors from incorrect calling patterns
- Complex pipeline composition logic
- Difficulty in API documentation

PROPOSED SOLUTIONS:
A) Standardize all transforms to factory pattern: text.strip() returns Transform
B) Create wrapper classes that handle calling patterns automatically
C) Use explicit .get() method: text.strip.get() vs text.replace("x","y").get()
D) Separate modules for factories vs direct transforms

PRIORITY: Medium - API works but could be more intuitive
IMPACT: Breaking change would require version bump to 1.0.0
"""
