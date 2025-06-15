# ~/schematix/src/schematix/core/field.py
"""..."""
from __future__ import annotations
import typing as t

from schematix.core.bases.field import BaseField

## BaseField Derivatives ##
class Field(BaseField):
    """
    Concrete implementation of BaseField for general use.

    This is the main field class that users will typically use directly.
    Specialized field types can inherit from BaseField or this class.
    """

    def _evaluateconditions(self, computed: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]:
        """Evaluate all conditions given computed field values."""
        if not self.dependencies:
            raise ValueError(f"Conditional Field '{self.name}' has no dependencies")
        if not self.conditions:
            raise ValueError(f"Conditional Field '{self.name}' has no conditions")

        result = {}

        depvals = [] # dependency values
        for dep in self.dependencies:
            if dep not in computed:
                raise ValueError(f"Dependency '{dep}' not available for field '{self.name}'")
            depvals.append(computed[dep])

        for condition, evaluator in self.conditions.items():
            try:
                result[condition] = evaluator(*depvals)
            except Exception as e:
                raise ValueError(f"Condition '{condition}' failed for field '{self.name}': {e}")

        return result

    def _extractwithoverrides(self, data: t.Any, overrides: t.Dict[str, t.Any]) -> t.Any:
        """Extract with temporary property overrides."""
        originals = {}
        for prop in ['required', 'default', 'transform', 'choices', 'type', 'mapping']:
            originals[prop] = getattr(self, prop)

        try:
            for prop, value in overrides.items():
                if (prop != 'value') and hasattr(self, prop):
                    setattr(self, prop, value)
            # Normal extraction pipeline
            raw = self._getsourcevalue(data)
            transformed = self._applytransform(raw)
            typed = self._applytype(transformed)
            mapped = self._applymapping(typed)
            choicesvalidated = self._validatechoices(mapped)
            validated = self.validate(choicesvalidated)
            self._checkrequired(validated)
            return validated

        finally:
            # restore originals
            for prop, value in originals.items():
                setattr(self, prop, value)


    def extract(self, data: t.Any, computed: t.Optional[t.Dict[str, t.Any]] = None) -> t.Any:
        """
        Standard field extraction implementation.

        Order: source → transform → type → mapping → choices → validate → required

        Args:
            data: Source data object

        Returns:
            Extracted, transformed, and validated value
        """
        # handle conditional
        if self.conditional:
            if computed is None:
                raise ValueError(f"Conditional field '{self.name}' requires computed (fields)")
            evaluated = self._evaluateconditions(computed)

            if 'value' in evaluated:
                return evaluated['value']

            return self._extractwithoverrides(data, evaluated)

        raw = self._getsourcevalue(data)
        transformed = self._applytransform(raw)
        typed = self._applytype(transformed)
        mapped = self._applymapping(typed)
        choicesvalidated = self._validatechoices(mapped)
        validated = self.validate(choicesvalidated)
        self._checkrequired(validated)
        return validated


    def assign(self, targetobj: t.Any, value: t.Any) -> None:
        """
        Standard field assignment implementation.

        Assigns value to the target location in target_obj.

        Args:
            targetobj: Object to assign value to
            value: Value to assign
        """
        validated = self.validate(value)
        self._applytargetvalue(targetobj, validated)

class FallbackField(BaseField):
    """
    Field that tries primary field first, falls back to secondary if it fails.

    Result of the | operator: primary_field | fallback_field
    """
    __constructs__ = (Field.__constructs__ | {'primary', 'fallback'})

    def __init__(
        self,
        primary: BaseField,
        fallback: BaseField,
        name: t.Optional[str] = None
    ):
        """
        Initialize fallback field.

        Args:
            primary: Primary field to try first
            fallback: Fallback field to use if primary fails
            name: Override name for this field
        """
        super().__init__(
            name=name or primary.name,
            required=primary.required,  # Use primary field's required setting
            default=fallback.default,   # Use fallback's default as ultimate fallback
        )
        self.primary = primary
        self.fallback = fallback

    def extract(self, data: t.Any, computed: t.Optional[t.Dict[str, t.Any]] = None) -> t.Any:
        """
        Try extracting from primary field, fallback to secondary if it fails.

        Args:
            data: Source data object

        Returns:
            Value from primary field, or fallback field if primary fails
        """
        try:
            value = self.primary.extract(data)
            # Consider None as a failure if primary is not required
            if value is None and not self.primary.required:
                return self.fallback.extract(data)
            return value
        except Exception:
            # Primary failed, try fallback
            return self.fallback.extract(data)

    def assign(self, targetobj: t.Any, value: t.Any) -> None:
        """
        Assign using primary field's target configuration.

        Args:
            targetobj: Object to assign to
            value: Value to assign
        """
        # Use primary field for assignment logic
        # Could potentially fallback to secondary field's target, but that gets complex
        self.primary.assign(targetobj, value)

    def __repr__(self) -> str:
        return f"FallbackField({self.primary!r} | {self.fallback!r})"

class CombinedField(BaseField):
    """
    Field that applies multiple fields to the same data and collects results.

    Result of the & operator: field1 & field2 & field3
    """
    __constructs__ = (Field.__constructs__ | {'fields'})

    def __init__(
        self,
        fields: t.List[BaseField],
        name: t.Optional[str] = None
    ):
        """
        Initialize combined field.

        Args:
            fields: List of fields to apply
            name: Override name for this field
        """
        if not fields:
            raise ValueError("CombinedField requires at least one field")

        if not isinstance(fields, (list, tuple, set)):
            raise ValueError("'fields' param must be list, tuple, or set")

        fields = list(fields)
        # Use first field's settings as defaults
        firstfield = fields[0]
        super().__init__(
            name=name,
            required=any(f.required for f in fields),  # Required if any field is required
            default={},  # Default to empty dict for merging
        )
        self.fields = fields

    def extract(self, data: t.Any, computed: t.Optional[t.Dict[str, t.Any]] = None) -> t.Dict[str, t.Any]:
        """
        Apply all fields to data and merge results.

        Args:
            data: Source data object

        Returns:
            Dict containing results from all fields
        """
        result = {}
        errors = []

        for field in self.fields:
            try:
                value = field.extract(data)
                if hasattr(field, 'name') and field.name:
                    if (value is not None) or field.required:
                        # Single field result
                        result[field.name] = value
                else:
                    # If field doesn't have a name, skip or use index
                    if isinstance(value, dict):
                        result.update(value)
                    else:
                        result[f"field{len(result)}"] = value

            except Exception as e:
                if field.required:
                    errors.append(f"Required field '{field.name}' failed: {e}")
                # Non-required fields that fail are just skipped

        if errors:
            raise ValueError(f"CombinedField extraction failed: {'; '.join(errors)}")

        return result

    def assign(self, targetobj: t.Any, value: t.Any) -> None:
        """
        Apply all fields' assignment logic to target object.

        Args:
            targetobj: Object to assign to
            value: Value to assign (should be dict or single value)
        """
        if isinstance(value, dict):
            # If value is a dict, try to assign each field its corresponding value
            for field in self.fields:
                if hasattr(field, 'name') and field.name in value:
                    field.assign(targetobj, value[field.name])
        else:
            # If single value, assign to all fields (probably not common)
            for field in self.fields:
                field.assign(targetobj, value)

    def addfield(self, field: BaseField) -> 'CombinedField':
        """
        Add another field to this combination.

        Args:
            field: Field to add

        Returns:
            New CombinedField with added field
        """
        return CombinedField(
            fields=self.fields + [field],
            name=self.name
        )

    def __repr__(self) -> str:
        fieldnames = [f.name or str(f) for f in self.fields]
        return f"CombinedField([{', '.join(fieldnames)}])"

    def __and__(self, other: 'BaseField') -> 'CombinedField':
        if isinstance(other, CombinedField):
            return CombinedField(
                fields=(self.fields + other.fields),
            )
        else:
            return CombinedField(
                fields=(self.fields + [other])
            )

class NestedField(BaseField):
    """
    Field that applies another field to a nested path in the data structure.

    Result of the @ operator: field @ "nested.path"
    """
    __constructs__ = (Field.__constructs__ | {'field', 'nestedpath'})

    def __init__(
        self,
        field: BaseField,
        nestedpath: str,
        name: t.Optional[str] = None
    ):
        """
        Initialize nested field.

        Args:
            field: Field to apply to nested data
            nestedpath: Dot-separated path to nested location
            name: Override name for this field
        """
        super().__init__(
            name=name,
            required=field.required,
            default=field.default,
            source=field.source,
            target=field.target,
            transform=field.transform
        )
        self.field = field
        self.nestedpath = nestedpath

    def extract(self, data: t.Any, computed: t.Optional[t.Dict[str, t.Any]] = None) -> t.Any:
        """
        Navigate to nested path, then apply field extraction.

        Args:
            data: Source data object

        Returns:
            Value extracted from nested location
        """
        # Navigate to nested location
        nesteddata = self._getnesteddata(data, self.nestedpath)

        if nesteddata is None:
            if self.required:
                raise ValueError(f"Required nested path '{self.nestedpath}' not found")
            return self.default

        # Apply field extraction to nested data
        return self.field.extract(nesteddata)

    def assign(self, targetobj: t.Any, value: t.Any) -> None:
        """
        Navigate to nested path in target, then apply field assignment.

        Args:
            targetobj: Object to assign to
            value: Value to assign
        """
        # Navigate to or create nested location in target
        nestedtarget = self._getorcreatenested(targetobj, self.nestedpath)

        # Apply field assignment to nested target
        self.field.assign(nestedtarget, value)

    def _getnesteddata(self, data: t.Any, path: str) -> t.Any:
        """
        Navigate to nested data location.

        Args:
            data: Source data object
            path: Dot-separated path

        Returns:
            Nested data or None if path doesn't exist
        """
        current = data
        pathparts = path.split('.')

        for part in pathparts:
            if hasattr(current, 'get') and callable(current.get):
                current = current.get(part)
            elif hasattr(current, part):
                current = getattr(current, part)
            else:
                return None

            if current is None:
                return None

        return current

    def _getorcreatenested(self, targetobj: t.Any, path: str) -> t.Any:
        """
        Navigate to or create nested location in target object.

        Args:
            targetobj: Target object
            path: Dot-separated path

        Returns:
            Nested target object (created if necessary)
        """
        current = targetobj
        pathparts = path.split('.')

        for part in pathparts:
            if hasattr(current, '__setitem__') and hasattr(current, '__getitem__'):
                # Dict-like object
                if part not in current:
                    current[part] = {}
                current = current[part]
            elif hasattr(current, part):
                # Object with attributes
                current = getattr(current, part)
            else:
                # Try to create attribute (might fail for some object types)
                try:
                    setattr(current, part, {})
                    current = getattr(current, part)
                except (AttributeError, TypeError):
                    raise ValueError(f"Cannot create nested path '{path}' in {type(targetobj)}")

        return current

    def withpath(self, newpath: str) -> 'NestedField':
        """
        Create new NestedField with different path.

        Args:
            newpath: New nested path

        Returns:
            New NestedField with updated path
        """
        return NestedField(
            field=self.field,
            nestedpath=newpath,
            name=self.name
        )

    def __repr__(self) -> str:
        return f"NestedField({self.field!r} @ {self.nestedpath!r})"

class AccumulatedField(BaseField):
    """
    Field that combines values from multiple fields using type-appropriate accumulation.

    Result of the + operator: field1 + field2 + field3
    """
    __constructs__ = (Field.__constructs__ | {'fields', 'separator'})

    def __init__(
        self,
        fields: t.List[BaseField],
        separator: str = " ",
        name: t.Optional[str] = None
    ):
        """
        Initialize accumulated field.

        Args:
            fields: List of fields to accumulate values from
            separator: Separator for string concatenation fallback
            name: Override name for this field
        """
        if not fields:
            raise ValueError("AccumulatedField requires at least one field")

        if not isinstance(fields, (list, tuple, set)):
            raise ValueError("'fields' param must be list, tuple, or set")

        fields = list(fields)

        firstfield = fields[0]
        super().__init__(
            name=name, #
            required=any(f.required for f in fields),  # Required if any field is required
            default=None,
        )
        self.fields = fields
        self.separator = separator

    def extract(self, data: t.Any, computed: t.Optional[t.Dict[str, t.Any]] = None) -> t.Any:
        """
        Extract values from all fields and accumulate them.

        Args:
            data: Source data object

        Returns:
            Accumulated value using type-appropriate combination
        """
        values = []

        # Extract all values
        for field in self.fields:
            try:
                value = field.extract(data)
                if value is not None:
                    values.append(value)
            except Exception as e:
                if field.required:
                    raise ValueError(f"Required field '{field.name}' failed in accumulation: {e}")
                # Skip non-required fields that fail

        if not values:
            if self.required:
                raise ValueError("No values available for required accumulated field")
            return self.default

        # Accumulate based on type
        return self._accumulatevalues(values)

    def assign(self, targetobj: t.Any, value: t.Any) -> None:
        """
        Assign accumulated value using first field's assignment logic.

        Args:
            targetobj: Object to assign to
            value: Accumulated value to assign
        """
        # Use first field's assignment logic
        self.fields[0].assign(targetobj, value)

    def _accumulatevalues(self, values: t.List[t.Any]) -> t.Any:
        """
        Accumulate values using type-appropriate logic.

        Args:
            values: List of values to accumulate

        Returns:
            Accumulated result
        """
        if not values:
            return self.default

        if len(values) == 1:
            return values[0]

        # Start with first value
        result = values[0]

        for value in values[1:]:
            result = self._combinevalues(result, value)

        return result

    def _combinevalues(self, left: t.Any, right: t.Any) -> t.Any:
        """
        Combine two values using type-appropriate logic.

        Args:
            left: First value
            right: Second value

        Returns:
            Combined result
        """
        # Handle special cases first
        if isinstance(left, dict) and isinstance(right, dict):
            # Merge dictionaries
            result = left.copy()
            result.update(right)
            return result

        if isinstance(left, (list, tuple)) and isinstance(right, (list, tuple)):
            # Combine sequences
            return list(left) + list(right)

        if isinstance(left, (int, float)) and isinstance(right, (int, float)):
            # Add numbers
            return left + right

        if isinstance(left, str) and isinstance(right, str):
            # Handle string concatenation with separator
            return left + self.separator + right

        # Same types (other than above special cases) - try natural addition
        if type(left) == type(right):
            try:
                return left + right
            except TypeError:
                # Types don't support +, fall back to string concat
                return str(left) + self.separator + str(right)

        # Fallback: convert to strings and concatenate
        return str(left) + self.separator + str(right)

    def addfield(self, field: BaseField) -> 'AccumulatedField':
        """
        Add another field to this accumulation.

        Args:
            field: Field to add

        Returns:
            New AccumulatedField with added field
        """
        return AccumulatedField(
            fields=self.fields + [field],
            separator=self.separator,
            name=self.name
        )

    def withseparator(self, separator: str) -> 'AccumulatedField':
        """
        Create new AccumulatedField with different separator.

        Args:
            separator: New separator for string concatenation

        Returns:
            New AccumulatedField with updated separator
        """
        return AccumulatedField(
            fields=self.fields,
            separator=separator,
            name=self.name
        )

    def __repr__(self) -> str:
        fieldnames = [f.name or str(f) for f in self.fields]
        return f"AccumulatedField([{' + '.join(fieldnames)}])"

    def __add__(self, other: 'BaseField') -> 'AccumulatedField':
        if isinstance(other, AccumulatedField):
            return AccumulatedField(
                fields=(self.fields + other.fields),
                separator=self.separator
            )
        else:
            return AccumulatedField(
                fields=(self.fields + [other]),
                separator=self.separator
            )

## Field Derivatives ##
class SourceField(Field):
    """
    Enhanced field for complex data extraction scenarios.

    Provides additional capabilities for:
    - Multiple fallback source paths
    - Conditional extraction logic
    - Complex nested data handling
    - Source data validation
    """
    __constructs__ = (Field.__constructs__ | {'fallbacks', 'condition'})

    def __init__(
        self,
        fallbacks: t.Optional[t.List[str]] = None,
        condition: t.Optional[t.Callable[[t.Any], bool]] = None,
        **kwargs
    ):
        """
        Initialize SourceField with enhanced extraction capabilities.

        Args:
            fallbacks: List of fallback source paths to try if primary source fails
            condition: Callable that returns True if extraction should proceed
            **kwargs: Standard Field arguments
        """
        super().__init__(**kwargs)
        self.fallbacks = fallbacks or []
        self.condition = condition

    def extract(self, data: t.Any, computed: t.Optional[t.Dict[str, t.Any]] = None) -> t.Any:
        """
        Enhanced extraction with fallbacks and conditions.

        Args:
            data: Source data object

        Returns:
            Extracted value using fallback logic if needed
        """
        # Check condition first
        if self.condition and not self.condition(data):
            return self.default

        # Try primary source first
        try:
            result = super().extract(data)
            if (result == self.default):
                return self._extractwithfallbacks(data)
            return result
        except (ValueError, KeyError, AttributeError):
            # Try fallback sources
            return self._extractwithfallbacks(data)

    def _extractwithfallbacks(self, data: t.Any) -> t.Any:
        """
        Try extracting from fallback sources.

        Args:
            data: Source data object

        Returns:
            First successful extraction or default value
        """
        originalsource = self.source

        for fallbacksource in self.fallbacks:
            try:
                # Temporarily set fallback as source
                self.source = fallbacksource
                result = super().extract(data)
                return result
            except Exception:
                continue
            finally:
                # Restore original source
                self.source = originalsource

        # All fallbacks failed
        if self.required:
            sources = [originalsource] + self.fallbacks
            raise ValueError(f"Required field '{self.name}' not found in any sources: {sources}")

        return self.default

    def addfallback(self, source_path: str) -> 'SourceField':
        """
        Add a fallback source path.

        Args:
            source_path: Source path to add as fallback

        Returns:
            New SourceField instance with added fallback
        """
        newfallbacks = self.fallbacks + [source_path]
        return SourceField(
            fallbacks=newfallbacks,
            condition=self.condition,
            name=self.name,
            source=self.source,
            target=self.target,
            required=self.required,
            default=self.default,
            transform=self.transform,
            **self._kwargs
        )

class TargetField(Field):
    """
    Enhanced field for complex data assignment scenarios.

    Provides additional capabilities for:
    - Conditional assignment logic
    - Value formatting before assignment
    - Multiple target assignments
    - Target structure creation
    """

    __constructs__ = (Field.__constructs__ | {'formatter', 'condition', 'additionaltargets', 'createstructure'})

    def __init__(
        self,
        formatter: t.Optional[t.Callable[[t.Any], t.Any]] = None,
        condition: t.Optional[t.Callable[[t.Any], bool]] = None,
        additionaltargets: t.Optional[t.List[str]] = None,
        createstructure: bool = True,
        **kwargs
    ):
        """
        Initialize TargetField with enhanced assignment capabilities.

        Args:
            formatter: Function to format value before assignment
            condition: Callable that returns True if assignment should proceed
            additionaltargets: List of additional target paths for same value
            createstructure: Whether to create nested structures if they don't exist
            **kwargs: Standard Field arguments
        """
        super().__init__(**kwargs)
        self.formatter = formatter
        self.condition = condition
        self.additionaltargets = additionaltargets or []
        self.createstructure = createstructure

    def assign(self, targetobj: t.Any, value: t.Any) -> None:
        """
        Enhanced assignment with formatting and conditions.

        Args:
            targetobj: Object to assign value to
            value: Value to assign
        """
        # Check condition first
        if self.condition and not self.condition(value):
            return

        # Apply formatting
        formattedvalue = self.formatter(value) if self.formatter else value

        # Validate formatted value
        validatedvalue = self.validate(formattedvalue)

        # Assign to primary target
        self._assigntotarget(targetobj, self.target, validatedvalue)

        # Assign to additional targets
        for additionaltarget in self.additionaltargets:
            self._assigntotarget(targetobj, additionaltarget, validatedvalue)

    def _assigntotarget(self, targetobj: t.Any, targetpath: str, value: t.Any) -> None:
        """
        Assign value to a specific target path.

        Args:
            targetobj: Target object
            targetpath: Path to assign to
            value: Value to assign
        """
        if targetpath is None:
            raise ValueError(f"Target path cannot be None")

        # Temporarily set target for assignment
        originaltarget = self.target
        try:
            self.target = targetpath

            if self.createstructure:
                self._createnestedstructure(targetobj, targetpath)

            self._applytargetvalue(targetobj, value)

        finally:
            # Restore original target
            self.target = originaltarget

    def _createnestedstructure(self, targetobj: t.Any, targetpath: str) -> None:
        """
        Create nested structure if it doesn't exist.

        Args:
            targetobj: Target object to modify
            targetpath: Target path that might need structure creation
        """
        if '.' not in targetpath:
            return

        pathparts = targetpath.split('.')
        current = targetobj

        # Create intermediate structure
        for part in pathparts[:-1]:
            if hasattr(current, '__setitem__') and hasattr(current, '__getitem__'):
                # Dict-like object
                if part not in current:
                    current[part] = {}
                current = current[part]
            elif hasattr(current, part):
                # Object with attributes - assume it exists
                current = getattr(current, part)
            else:
                # Can't create structure for object attributes
                break

    def addtarget(self, targetpath: str) -> 'TargetField':
        """
        Add an additional target path.

        Args:
            targetpath: Target path to add

        Returns:
            New TargetField instance with added target
        """
        newtargets = self.additionaltargets + [targetpath]
        return TargetField(
            formatter=self.formatter,
            condition=self.condition,
            additionaltargets=newtargets,
            createstructure=self.createstructure,
            name=self.name,
            source=self.source,
            target=self.target,
            required=self.required,
            default=self.default,
            transform=self.transform,
            **self._kwargs
        )

## Other ##
class BoundField:
    """
    A field with complete source-to-target binding.

    Represents a complete transformation: extract from source, transform, validate,
    and assign to target. This is the result of binding source and target fields together.
    """
    __constructs__: set[str] = {'sourcefield', 'targetfield', 'name', 'transform'}

    def __init__(
        self,
        sourcefield: BaseField,
        targetfield: t.Optional[BaseField] = None,
        name: t.Optional[str] = None,
        transform: t.Optional[t.Callable] = None
    ) -> None:
        """
        Initialize bound field.

        Args:
            sourcefield: Field configured for extraction
            targetfield: Field configured for assignment (optional)
            name: Override name for this binding
            transform: Additional transform to apply
        """
        self.sourcefield = sourcefield
        self.targetfield = (targetfield or sourcefield)
        self.name = (name or sourcefield.name)
        self.transform = transform

        self._validatebinding()

    def _validatebinding(self) -> None:
        """Validate the bound field configuration."""
        if self.sourcefield.source is None:
            raise ValueError(f"Source field '{self.sourcefield.name}' has no source defined")

        # only validate explicit target fields
        if (self.targetfield is not self.sourcefield) and (self.targetfield.target is None):
            raise ValueError(f"Target field '{self.targetfield.name}' has no target defined ")


    def transformdata(self, data: t.Any, targetobj: t.Any) -> None:
        """
        Perform complete source-to-target transformation.

        1. Extract value from source using source_field
        2. Apply additional transform if defined
        3. Assign to target using target_field

        Args:
            sourcedata: Data to extract from
            targetobj: Object to assign to
        """
        extracted = self.sourcefield.extract(data)

        if self.transform is not None:
            extracted = self.transform(extracted)
        if self.targetfield:
            self.targetfield.assign(targetobj, extracted)
        else:
            raise ValueError(f"...")

    def extractonly(self, data: t.Any) -> t.Any:
        """
        Extract value without assignment (useful for validation/testing).

        Args:
            data: Data to extract from

        Returns:
            Extracted and transformed value
        """
        extracted = self.sourcefield.extract(data)
        if self.transform is not None:
            extracted = self.transform(extracted)
        return extracted

    def assignonly(self, targetobj: t.Any, value: t.Any) -> None:
        """
        Assign value without extraction (useful when you have the value already).

        Args:
            targetobj: Object to assign to
            value: Value to assign
        """
        if self.targetfield:
            self.targetfield.assign(targetobj, value)
        else:
            raise ValueError(f"")


    @property
    def sourcepath(self) -> t.Optional[str]:
        return self.sourcefield.source

    @property
    def targetpath(self) -> t.Optional[str]:
        if self.targetfield:
            return self.targetfield.target
        return None

    @property
    def isrequired(self) -> bool:
        if self.targetfield:
            return (self.sourcefield.required or self.targetfield.required)
        return self.sourcefield.required

    def withtransform(self, transform: t.Callable) -> 'BoundField':
        """
        Create a new BoundField with an additional transform.

        Args:
            transform: Transform function to apply

        Returns:
            New BoundField instance with the transform
        """
        return BoundField(
            sourcefield=self.sourcefield,
            targetfield=self.targetfield,
            name=self.name,
            transform=transform
        )

    def withname(self, name: str) -> 'BoundField':
        """
        Create a new BoundField with a different name.

        Args:
            name: New name for the binding

        Returns:
            New BoundField instance with the new name
        """
        return BoundField(
            sourcefield=self.sourcefield,
            targetfield=self.targetfield,
            name=name,
            transform=self.transform
        )

class FieldBindingFactory:
    """
    Factory class for creating bound fields from various inputs.

    Provides convenient methods for creating BoundField instances from different
    field configurations and mapping patterns.
    """

    @classmethod
    def FromFields(cls, source: BaseField, target: BaseField) -> BoundField:
        """
         Create BoundField from separate source and target fields.

         Args:
             source: Field configured for extraction
             target: Field configured for assignment

         Returns:
             BoundField instance
         """
        return BoundField(source, target)

    @classmethod
    def FromField(cls, field: BaseField) -> BoundField:
        """
        Create BoundField from a single field with both source and target.

        Args:
            field: Field with both source and target configured

        Returns:
            BoundField instance
        """
        return BoundField(field, field)

    @classmethod
    def FromMapping(
        cls,
        mapping: t.Dict[str, t.Any],
        fieldclass: t.Type[BaseField]
    ) -> t.Dict[str, BoundField]:
        """
        Create multiple BoundFields from a mapping dictionary.

        Args:
            mapping: Dict of field_name -> source_config
            fieldclass: Field class to use for creating fields

        Returns:
            Dict of fieldname -> BoundField
        """
        bound = {}

        for name, config in mapping.items():
            if isinstance(config, str):
                source = fieldclass(name=name, source=config)
            elif isinstance(config, tuple) and len(config) == 2:
                path, transform = config
                source = fieldclass(name=name, source=path, transform=transform)
            else:
                raise ValueError(f"Invalid source config for '{name}': {config}")

            target = fieldclass(name=name, target=name)

            bound[name] = BoundField(source, target)

        return bound
