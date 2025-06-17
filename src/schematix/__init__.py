# ~/schematix/src/schematix/__init__.py
"""
Schematix: A Python library for declarative data mapping and transformation.

Schematix provides an object-oriented approach to data transformation that emphasizes
reusability and composability. Define target schemas once and bind them to different
data sources with source-specific extraction and transformation logic.
"""

__version__ = "0.4.6"
__author__ = "Joel Yisrael"
__email__ = "schizoprada@gmail.com"
__license__ = "MIT"
__url__ = "https://github.com/schizoprada/schematix"

# Version info tuple for programmatic access
VERSION = tuple(map(int, __version__.split('.')))

from .core import (
    FieldMeta, SchemaMeta, BaseField, BaseSchema,
    Field, FallbackField, CombinedField,
    NestedField, AccumulatedField, BoundField,
    SourceField, TargetField, FieldBindingFactory,
    Schema

)
from .decorators import (
    field, schema
)

from . import transforms

tr = transforms
x = transforms

__all__ = [
    "__version__",
    "__author__",
    "__email__",
    "__license__",
    "__url__",
    "VERSION",
    'FieldMeta',
    'SchemaMeta',
    'BaseField',
    'BaseSchema',
    'Field',
    'FallbackField',
    'CombinedField',
    'NestedField',
    'AccumulatedField',
    'BoundField',
    'SourceField',
    'TargetField',
    'FieldBindingFactory',
    'Schema',
    'field',
    'schema',
    'transforms',
    'tr',
    'x'
]
