# ~/schematix/src/schematix/decorators/field.py
"""
Field decorators for functional API.
"""
from __future__ import annotations
import inspect, typing as t

from schematix.core.bases.field import BaseField
from schematix.core.field import (
    Field, SourceField, TargetField,
    FallbackField, CombinedField,
    NestedField, AccumulatedField,
    BoundField
)

F = t.TypeVar('F', bound=BaseField)

def _instantiate(cls: t.Type, to: t.Type[F]) -> F:
    """
    Create a field instance from class attributes using the target field type.

    Extracts all attributes matching the target field's __constructs__ and
    creates an instance with those attributes as constructor arguments.

    Args:
        cls: Class containing field configuration as attributes
        to: Target field class to instantiate

    Returns:
        Instance of the target field class configured from cls attributes
    """
    def getrequired(of: t.Type[F]) -> t.List[str]:
        sig = inspect.signature(of.__init__)
        return [
            name for name, param in sig.parameters.items()
            if (param.default is param.empty) and (name != 'self')
        ]

    def getmissing(required: t.List[str], config: t.Dict[str, t.Any]) -> t.List[str]:
        return [r for r in required if r not in config]

    config = {}

    for construct in to.__constructs__:
        if hasattr(cls, construct):
            config[construct] = getattr(cls, construct)

    try:

        instance = to(**config)
    except TypeError as e:
        required = getrequired(to)
        missing = getmissing(required, config)
        if missing:
            raise ValueError(f"{to.__name__} decorator requires {missing} attributes on {cls.__name__}")
        else:
            raise ValueError(f"{to.__name__} decorator error on {cls.__name__}: {e}")


    # REMOVED: conflicts with SchemaMeta.__new__
    #if 'name' not in config:
        #instance.name = cls.__name__.lower()

    return instance

def _field(cls: t.Type) -> Field:
    """
    Decorator to convert a class definition into a Field instance.

    Usage:
        @field
        class UserID:
            source = 'user_id'
            required = True
            transform = int

    Args:
        cls: Class with field configuration as attributes

    Returns:
        Field instance configured from class attributes
    """
    return _instantiate(cls, Field)

def _source(cls: t.Type) -> SourceField:
    """
    Decorator to convert a class definition into a SourceField instance.

    Usage:
        @field.source
        class EmailField:
            source = 'email'
            fallbacks = ['contact_email', 'user_email']
            required = True
    """
    return _instantiate(cls, SourceField)

def _target(cls: t.Type) -> TargetField:
    """
    Decorator to convert a class definition into a TargetField instance.

    Usage:
        @field.target
        class FormattedName:
            target = 'display_name'
            formatter = str.title
            additionaltargets = ['full_name']
    """
    return _instantiate(cls, TargetField)

def _fallback(cls: t.Type) -> FallbackField:
    """
    Decorator to convert a class definition into a FallbackField instance.

    Usage:
        @field.fallback
        class EmailFallback:
            primary = Field(source='email')
            fallback = Field(source='contact_email')
            name = 'email_with_fallback'  # optional

    Args:
        cls: Class with FallbackField configuration as attributes

    Returns:
        FallbackField instance configured from class attributes
    """
    return _instantiate(cls, FallbackField)

def _combined(cls: t.Type) -> CombinedField:
    """
    Decorator to convert a class definition into a CombinedField instance.

    Usage:
        @field.combined
        class UserFields:
            fields = [
                Field(name='id', source='user_id'),
                Field(name='email', source='email_addr')
            ]
            name = 'user_data'  # optional

    Args:
        cls: Class with CombinedField configuration as attributes

    Returns:
        CombinedField instance configured from class attributes
    """
    return _instantiate(cls, CombinedField)

def _nested(cls: t.Type) -> NestedField:
    """
    Decorator to convert a class definition into a NestedField instance.

    Usage:
        @field.nested
        class ProfileName:
            field = Field(source='name')
            nestedpath = 'user.profile'
            name = 'nested_name'  # optional

    Args:
        cls: Class with NestedField configuration as attributes

    Returns:
        NestedField instance configured from class attributes
    """
    return _instantiate(cls, NestedField)

def _accumulated(cls: t.Type) -> AccumulatedField:
    """
    Decorator to convert a class definition into an AccumulatedField instance.

    Usage:
        @field.accumulated
        class FullName:
            fields = [
                Field(source='first_name'),
                Field(source='last_name')
            ]
            separator = ' '  # optional, defaults to ' '
            name = 'full_name'  # optional

    Args:
        cls: Class with AccumulatedField configuration as attributes

    Returns:
        AccumulatedField instance configured from class attributes
    """
    return _instantiate(cls, AccumulatedField)

def _bound(cls: t.Type) -> BoundField:
    """..."""
    def getrequired() -> t.List[str]:
        sig = inspect.signature(BoundField.__init__)
        return [
            name for name, param in sig.parameters.items()
            if (param.default is param.empty) and (name != 'self')
        ]

    def getmissing(required: t.List[str], config: t.Dict[str, t.Any]) -> t.List[str]:
        return [r for r in required if r not in config]

    config = {}

    for construct in BoundField.__constructs__:
        if hasattr(cls, construct):
            config[construct] = getattr(cls, construct)

    try:

        instance = BoundField(**config)
    except TypeError as e:
        required = getrequired()
        missing = getmissing(required, config)
        if missing:
            raise ValueError(f"{BoundField.__name__} decorator requires {missing} attributes on {cls.__name__}")
        else:
            raise ValueError(f"{BoundField.__name__} decorator error on {cls.__name__}: {e}")


    # REMOVED: conflicts with SchemaMeta.__new__
    #if 'name' not in config:
        #instance.name = cls.__name__.lower()

    return instance

class Decorator:
    """
    Field decorator class that provides access to all field type decorators.

    Supports both direct decoration (@field) and attribute-based decoration
    (@field.source, @field.target, etc.) for creating different field types.

    Usage:
        @field
        class BasicField:
            source = 'data_field'

        @field.source
        class SourceField:
            source = 'primary'
            fallbacks = ['backup']

        @field.accumulated
        class CombinedField:
            fields = [field1, field2]
    """

    def __init__(self) -> None:
        """Initialize the field decorator."""
        pass

    def __call__(self, cls: t.Type) -> Field:
        """
        Main field decorator for creating basic Field instances.

        Args:
            cls: Class with Field configuration as attributes

        Returns:
            Field instance configured from class attributes
        """
        return _field(cls)

    @property
    def source(self) -> t.Callable[[t.Type], SourceField]:
        """
        Decorator for creating SourceField instances with enhanced extraction.

        Returns:
            Decorator function that creates SourceField from class definition
        """
        return _source

    @property
    def target(self) -> t.Callable[[t.Type], TargetField]:
        """
        Decorator for creating TargetField instances with enhanced assignment.

        Returns:
            Decorator function that creates TargetField from class definition
        """
        return _target

    @property
    def fallback(self) -> t.Callable[[t.Type], FallbackField]:
        """
        Decorator for creating FallbackField instances with primary/fallback logic.

        Returns:
            Decorator function that creates FallbackField from class definition
        """
        return _fallback

    @property
    def combined(self) -> t.Callable[[t.Type], CombinedField]:
        """
        Decorator for creating CombinedField instances that merge multiple fields.

        Returns:
            Decorator function that creates CombinedField from class definition
        """
        return _combined

    @property
    def nested(self) -> t.Callable[[t.Type], NestedField]:
        """
        Decorator for creating NestedField instances that apply to nested data paths.

        Returns:
            Decorator function that creates NestedField from class definition
        """
        return _nested

    @property
    def accumulated(self) -> t.Callable[[t.Type], AccumulatedField]:
        """
        Decorator for creating AccumulatedField instances that combine values.

        Returns:
            Decorator function that creates AccumulatedField from class definition
        """
        return _accumulated

    @property
    def bound(self) -> t.Callable[[t.Type], BoundField]:
        """..."""
        return _bound

field = Decorator()
