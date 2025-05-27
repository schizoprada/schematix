# ~/schematix/src/schematix/core/bases/schema.py
"""
Base schema classes and interfaces.
"""
from __future__ import annotations
import abc, typing as t

from schematix.core.metas import SchemaMeta
if t.TYPE_CHECKING:
    from schematix.core.bases.field import BaseField
    from schematix.core.schema import BoundSchema

class BaseSchema(abc.ABC, metaclass=SchemaMeta):
    """
    Abstract base class for all schema types.

    Uses SchemaMeta to automatically discover and organize field definitions.
    Provides the core interface for data transformation operations.

    The metaclass populates:
    - _fields: Dict[str, BaseField] - Registry of all fields
    - _fieldnames: List[str] - List of field names
    """
    _fields: t.Dict[str, BaseField] # for type hints
    _fieldnames: t.List[str] # for type hints
    def __init__(self, **kwargs) -> None:
        """
        Initialize schema instance.

        Args:
            **kwargs: Additional configuration options
        """
        self._config = kwargs

        # lowercase aliases
        self.getfields = self.GetFields
        self.getfieldnames = self.GetFieldNames
        self.hasfield = self.HasField

    @classmethod
    def GetFields(cls) -> t.Dict[str, BaseField]:
        """Return a copy of the fields dictionary."""
        return cls._fields.copy()

    @classmethod
    def GetFieldNames(cls) -> t.List[str]:
        """Return a list of field names."""
        return cls._fieldnames.copy()

    @classmethod
    def HasField(cls, name: str) -> bool:
        """Check if schema has a field with the given name."""
        return (name in cls._fields)

    @abc.abstractmethod
    def transform(self, data: t.Any) -> t.Any:
        """
        Transform source data using this schema's field definitions.

        Args:
            data: Source data to transform

        Returns:
            Transformed data in target format
        """
        pass

    @abc.abstractmethod
    def bind(self, mapping: t.Dict[str, t.Any]) -> 'BoundSchema':
        """
        Create a bound schema with source-specific field mappings.

        Args:
            mapping: Dict mapping field names to source paths/transforms

        Returns:
            BoundSchema instance configured for specific data source
        """
        pass

    def validate(self, data: t.Any) -> t.Dict[str, BaseField]:
        """
        Validate data against this schema without transformation.

        Args:
            data: Data to validate

        Returns:
            Dict of fieldname -> validationerrors (empty if valid)
        """
        errors = {}

        for name, field in self._fields.items():
            try:
                field.extract(data)
            except Exception as e:
                errors[name] = str(e)

        return errors

    def __repr__(self) -> str:
        fieldnames = ', '.join(self._fieldnames)
        return f"{self.__class__.__name__}(fields=[{fieldnames}])"
