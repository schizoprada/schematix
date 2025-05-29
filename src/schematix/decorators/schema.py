# ~/schematix/src/schematix/decorators/schema.py
"""
Schema decorators for functional API.
"""
from __future__ import annotations
import typing as t

from schematix.core.schema import Schema

def schema(cls: t.Type) -> t.Type[Schema]:
    """
    Decorator to convert a regular class into a Schema class.

    Usage:
        @schema
        class UserSchema:
            id = Field(source='user_id')
            email = Field(source='email_addr', required=True)

    Args:
        cls: Class to convert to Schema

    Returns:
        Schema class with all field definitions preserved
    """
    attrs = {}
    for name, value in cls.__dict__.items():
        if not name.startswith("__"):
            attrs[name] = value

    schemacls = type(cls.__name__, (Schema,), attrs)

    if cls.__doc__:
        schemacls.__doc__ = cls.__doc__
    if hasattr(cls, '__module__'):
        schemacls.__module__ = cls.__module__

    return schemacls
