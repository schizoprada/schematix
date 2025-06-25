# ~/schematix/src/schematix/core/bases/field.py
"""
Base field classes and interfaces.
"""
from __future__ import annotations
import abc, typing as t

from schematix.core.metas import FieldMeta
if t.TYPE_CHECKING:
    from schematix.core.field import (
        Field, FallbackField, CombinedField,
        NestedField, AccumulatedField, BoundField
    )


class BaseField(abc.ABC, metaclass=FieldMeta):
    """
    Abstract base class for all field types.

    Defines the core interface that all fields must implement:
    - extract(): Extract and transform data from source
    - validate(): Validate extracted values
    - Core attributes: name, required, default, transform
    """
    __constructs__: set[str] = {
        'name', 'required', 'default', 'transform', 'source', 'target',
        'type', 'choices', 'mapping', 'mapper', 'keysaschoices', 'valuesaschoices',
        'transient', 'conditional', 'dependencies', 'conditions'
    }
    __defaults__: dict[str, t.Any] = {
        "name": None,
        "required": False,
        "default": None,
        "transform": None,
        "source": None,
        "target": None,
        "type": None,
        "choices": None,
        "mapping": None,
        "mapper": None,
        "keysaschoices": True,
        "valuesaschoices": False,
        "transient": False,
        "conditional": False,
        "dependencies": None,
        "conditions": None,
    }


    def __init__(
        self,
        name: t.Optional[str] = None,
        required: bool = False,
        default: t.Any = None,
        transform: t.Optional[t.Callable] = None,
        source: t.Optional[str] = None,
        target: t.Optional[str] = None,
        # new params 0.4.5
        type: t.Optional[t.Type] = None,
        choices: t.Optional[t.List[t.Any]] = None,
        mapping: t.Optional[t.Dict] = None,
        mapper: t.Optional[t.Callable] = None,
        keysaschoices: bool = True,
        valuesaschoices: bool = False,
        transient: bool = False,
        conditional: bool = False,
        dependencies: t.Optional[t.List[str]] = None,
        conditions: t.Optional[t.Dict[str, t.Callable]] = None,
        **kwargs
    ) -> None:
        self.name = name
        self.required = required
        self.default = default
        self.transform = transform
        self.source = source
        self.target = target

        # 0.4.5
        self.type = type
        self.choices = choices
        self.mapping = mapping
        self.mapper = mapper
        self.keysaschoices = keysaschoices
        self.valuesaschoices = valuesaschoices
        self.transient = transient
        self.conditional = conditional
        self.dependencies = dependencies
        self.conditions = conditions

        self._kwargs = kwargs # store additional kwargs for subclass
        self._initializedwith: dict[str, t.Any] = {
            "name": name,
            "required": required,
            "default": default,
            "transform": transform,
            "source": source,
            "target": target,
            "type": type,
            "choices": choices,
            "mapping": mapping,
            "mapper": mapper,
            "keysaschoices": keysaschoices,
            "valuesaschoices": valuesaschoices,
            "transient": transient,
            "conditional": conditional,
            "dependencies": dependencies,
            "conditions": conditions,
        }


    @abc.abstractmethod
    def extract(self, data: t.Any, computed: t.Optional[t.Dict[str, t.Any]] = None) -> t.Any:
        """
        Extract and transform a value from source data.

        Args:
            data: Source data object (dict, dataclass, etc.)

        Returns:
            Extracted and transformed value

        Raises:
            ValueError: If required field is missing or validation fails
        """
        pass


    @abc.abstractmethod
    def assign(self, targetobj: t.Any, value: t.Any) -> None:
        """
        Assign a value to the target location.

        Args:
            targetobj: Target object to assign to
            value: Value to assign

        Raises:
            ValueError: If assignment fails
        """
        pass

    def validate(self, value: t.Any) -> t.Any:
        """
        Validate an extracted value.

        Default implementation just returns the value.
        Subclasses can override for type-specific validation.

        Args:
            value: Value to validate

        Returns:
            Validated value (may be transformed)

        Raises:
            ValueError: If validation fails
        """
        return value

    def _getnestedvalue(self, data: t.Any, pathparts: t.List[str]) -> t.Any:
        """
        Extract value from nested data structure.

        Args:
            data: Source data object
            pathparts: List of path components (e.g., ['user', 'profile', 'name'])

        Returns:
            Nested value or default if path doesn't exist
        """
        current = data

        for part in pathparts:
            if hasattr(current, 'get') and callable(current.get):
                current = current.get(part)
            elif hasattr(current, part):
                current = getattr(current, part)
            else:
                return self.default

            if current is None:
                return self.default

        return current

    def _getsourcevalue(self, data: t.Any) -> t.Any:
        """
        Extract raw value from source data before transformation.

        Handles different data types (dict, dataclass, etc.) and nested paths.

        Args:
            data: Source data object

        Returns:
            Raw extracted value or default if not found
        """
        if self.source is None:
            return self.default

        # Handle nested paths (e.g., "user.profile.name")
        if ('.' in self.source):
            return self._getnestedvalue(data, self.source.split('.'))

        # Handle different data types
        if hasattr(data, 'get') and callable(data.get):
            # dict-like
            return data.get(self.source, self.default)

        elif hasattr(data, self.source):
            # objects with attributes
            return getattr(data, self.source, self.default)
        else:
            return self.default

    def _applytype(self, value: t.Any) -> t.Any:
        """Apply type conversion if type is specified."""
        if (self.type is None) or (value is None):
            return value

        try:
            return self.type(value)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Cannot convert '{value}' to {self.type.__name__}: {e}")

    def _applymapping(self, value: t.Any) -> t.Any:
        """Apply value mapping using mapper function."""
        if value is None:
            return None

        if not self.mapping:
            return value

        # handle unhashable types by mapping each element
        if isinstance(value, (list, tuple, set)):
            try:
                return [self._applymapping(item) for item in value]
            except Exception as e:
                if self.default is not None:
                    return self.default
                raise ValueError(f"Mapping failed for {type(value)} value '{value}': {e}")

        # direct lookup
        if value in self.mapping:
            return self.mapping[value]

        # if no mapper, return default or raise
        if not self.mapper:
            if self.default is not None:
                return self.default
            raise ValueError(f"No mapping found for value '{value}' and no mapper function provided")

        try:
            return self.mapper(value, self.mapping)
        except Exception as e:
            if self.default is not None:
                return self.default
            raise ValueError(f"Mapping failed for value '{value}': {e}")


    def _validatechoices(self, value: t.Any) -> t.Any:
        """Validate value against allowed choices."""
        if not self.choices:
            return value

        if value not in self.choices:
            raise ValueError(f"Value '{value}' not in allowed choices: {self.choices}")

        return value


    def _applytransform(self, value: t.Any) -> t.Any:
        """
        Apply transformation function to value if defined.

        Args:
            value: Value to transform

        Returns:
            Transformed value or original if no transform
        """
        if (self.transform is not None) and (value is not None):
            # maybe we should allow for transforms on None
            return self.transform(value)
        return value

    def _checkrequired(self, value: t.Any) -> None:
        """
        Check if required field has a value.

        Args:
            value: Value to check

        Raises:
            ValueError: If required field is None/missing
        """
        if self.required and (value is None):
            raise ValueError(f"({self.name}) required field is missing or None")

    def _applynestedtargetvalue(self, targetobj: t.Any, value: t.Any, pathparts: t.List[str]) -> None:
        """
        Set value in nested target structure, creating intermediate objects as needed.

        Args:
            targetobj: Target object to modify
            pathparts: List of path components (e.g., ['user', 'profile', 'name'])
            value: Value to set
        """
        current = targetobj

        for part in pathparts[:-1]:
            if hasattr(current, '__setitem__') and hasattr(current, '__getitem__'):
                if part not in current:
                    current[part] = {}
                current = current[part]
            elif hasattr(current, part):
                current = getattr(current, part)
            else:
                raise ValueError(f"Cannot navigate to nested target: {'.'.join(pathparts)}")

        key = pathparts[-1]
        if hasattr(current, '__setitem__'):
            current[key] = value
        else:
            setattr(current, key, value)

    def _applytargetvalue(self, targetobj: t.Any, value: t.Any) -> None:
        """
        Set value in target object at the target path.

        Handles different target types (dict, dataclass, etc.) and nested paths.

        Args:
            targetobj: Target object to modify
            value: Value to set
        """
        if self.target is None:
            raise ValueError(f"Field '{self.name}' has no target defined")

        if ('.' in self.target):
            return self._applynestedtargetvalue(targetobj, value, self.target.split('.'))
        else:
            if hasattr(targetobj, '__setitem__'):
                targetobj[self.target] = value
            else:
                try:
                    setattr(targetobj, self.target, value)
                except Exception as e:
                    raise ValueError(f"Cannot set target '{self.target}' on {type(targetobj)}: {str(e)}")

    def __repr__(self) -> str:
        """Compact version that keeps output on single line."""
        attrs = []

        # Always show name
        attrs.append(f"name={self.name!r}")

        # Core attributes
        if self.source is not None:
            attrs.append(f"source={self.source!r}")
        if self.target is not None:
            attrs.append(f"target={self.target!r}")
        if self.required:
            attrs.append("required=True")
        if self.default is not None:
            attrs.append(f"default={self.default!r}")

        # Enhanced features (show only if configured)
        if self.transform is not None:
            transformname = getattr(self.transform, '__name__', 'func')
            attrs.append(f"transform={transformname}")

        if self.type is not None:
            attrs.append(f"type={self.type.__name__}")

        if self.choices:
            choicecount = len(self.choices)
            if choicecount <= 3:
                attrs.append(f"choices={self.choices}")
            else:
                attrs.append(f"choices=[...{choicecount} items]")

        if self.mapping:
            attrs.append(f"mapping={{...{len(self.mapping)} items}}")

        if self.transient:
            attrs.append("transient=True")

        if self.conditional:
            attrs.append("conditional=True")

        return f"{self.__class__.__name__}({', '.join(attrs)})"

    ## Operator Overloads ##
    def __rshift__(self, other: 'BaseField') -> 'BoundField':
        """
        Pipeline operator: source >> target

        Args:
            other: Target field

        Returns:
            BoundField with source->target mapping
        """
        from schematix.core.field import BoundField
        return BoundField(sourcefield=self, targetfield=other)

    def __or__(self, other: 'BaseField') -> 'FallbackField':
        """
        Fallback operator: primary | fallback

        Args:
            other: Fallback field

        Returns:
            FallbackField that tries primary first, then fallback
        """
        from schematix.core.field import FallbackField
        return FallbackField(primary=self, fallback=other)

    def __and__(self, other: 'BaseField') -> 'CombinedField':
        """
        Combine operator: field1 & field2

        Args:
            other: Field to combine with

        Returns:
            CombinedField that applies both fields
        """
        from schematix.core.field import CombinedField
        return CombinedField(fields=[self, other])

    def __matmul__(self, path: str) -> 'NestedField':
        """
        Nested operator: field @ "nested.path"

        Args:
            path: Dot-separated nested path

        Returns:
            NestedField that applies field to nested location
        """
        from schematix.core.field import NestedField
        return NestedField(field=self, nestedpath=path)

    def __add__(self, other: 'BaseField') -> 'AccumulatedField':
        """
        Accumulate operator: field1 + field2

        Args:
            other: Field to accumulate with

        Returns:
            AccumulatedField that combines values from both fields
        """
        from schematix.core.field import AccumulatedField
        return AccumulatedField(fields=[self, other])

    ## Operator Method Chains ##
    def pipeline(self, target: 'BaseField') -> 'BoundField':
        """Method chaining equivalent of >> operator."""
        return self.__rshift__(target)

    def fallback(self, backup: 'BaseField') -> 'FallbackField':
        """Method chaining equivalent of | operator."""
        return self.__or__(backup)

    def combine(self, other: 'BaseField') -> 'CombinedField':
        """Method chaining equivalent of & operator."""
        return self.__and__(other)

    def nested(self, path: str) -> 'NestedField':
        """Method chaining equivalent of @ operator."""
        return self.__matmul__(path)

    def accumulate(self, other: 'BaseField') -> 'AccumulatedField':
        """Method chaining equivalent of + operator."""
        return self.__add__(other)
