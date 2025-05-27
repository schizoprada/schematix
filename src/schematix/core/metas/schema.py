# ~/schematix/src/schematix/core/metas/schema.py
"""
Metaclass for Schema classes that handles field discovery and organization.
"""
from __future__ import annotations
import abc, inspect, typing as t

class SchemaMeta(abc.ABCMeta):
    """
    Metaclass for Schema classes that automatically discovers and organizes field definitions.

    This metaclass:
    - Discovers all Field instances defined as class attributes
    - Creates a _fields registry on the schema class
    - Handles inheritance by merging fields from parent schemas
    - Sets automatic field names if not explicitly defined
    - Validates field definitions
    """

    def __new__(mcs, name: str, bases: tuple, namespace: dict, **kwargs) -> t.Type:
        # handle inheritance - collect fields from parent classes
        inherited = {}
        for base in bases:
            if hasattr(base, '_fields'):
                inherited.update(base._fields)

        # discover fields in current class
        current = {}
        for attrname, attrval in list(namespace.items()):
            if mcs._isfield(attrval):
                if (not hasattr(attrval, 'name')) or (attrval.name is None):
                    # set if not explicitly set
                    attrval.name = attrname
                # Store field and remove from namespace (fields shouldn't be instance attributes)
                current[attrname] = attrval
                del namespace[attrname]
        # Merge inherited and current fields (current takes precedence)
        allfields = {**inherited, **current}
        # Add fields registry to namespace
        namespace['_fields'] = allfields
        namespace['_fieldnames'] = list(allfields.keys())

        # Create the class
        cls = super().__new__(mcs, name, bases, namespace)

        # Validate fields after class creation
        mcs._validatefields(cls, allfields)
        return cls

    @staticmethod
    def _isfield(obj: t.Any) -> bool:
        """..."""
        conditions = (
            hasattr(obj, 'name'),
            hasattr(obj, 'required'),
            hasattr(obj, 'default'),
            callable(getattr(obj, 'extract', None)),
            callable(getattr(obj, 'assign', None)),
        )
        return all(conditions)

    @staticmethod
    def _validatefields(schemacls: t.Type, fields: t.Dict[str, t.Any]) -> None:
        """..."""

        # check for name conflicts
        names = [field.name for field in fields.values()]
        if (len(names) != len(set(names))):
            duplicates = [name for name in names if names.count(name) > 1]
            raise ValueError(f"({schemacls.__name__}) duplicate field names: {duplicates}")

        for name, field in fields.items():
            try:
                if not hasattr(field, 'name'):
                    raise AttributeError(f"({schemacls.__name__}) field missing 'name' attribute")

                if (field.name != name):
                    raise ValueError(f"({schemacls.__name__}) field name mismatch: attribute '{name}' has field.name='{field.name}'")

            except Exception as e:
                raise ValueError(f"({schemacls.__name__}) invlaid field '{name}': {str(e)}")


    def getfields(cls) -> t.Dict[str, t.Any]:
        """Return a copy of the fields dictionary."""
        return cls._fields.copy()

    def getfieldnames(cls) -> list:
        """Return a list of field names."""
        return cls._fieldnames.copy()

    def hasfield(cls, name: str) -> bool:
        """Check if schema has a field with the given name."""
        return (name in cls._fields)
