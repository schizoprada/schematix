# ~/schematix/src/schematix/core/schema.py
"""
Concrete schema implementation for data transformation.
"""
from __future__ import annotations
import abc, typing as t
from schematix.core.bases.schema import BaseSchema

if t.TYPE_CHECKING:
    from schematix.core.bases.field import BaseField

class BoundSchema:
    """
    A schema bound to specific source mappings.

    This is returned by Schema.bind() and contains the actual transformation
    logic for a specific data source.
    """

    def __init__(
        self,
        schemacls: t.Type[BaseSchema],
        mapping: t.Dict[str, t.Any]
    ) -> None:
        """
        Initialize bound schema.

        Args:
            schemacls: The schema class this is bound to
            mapping: Field name -> source path/transform mappings
        """
        self.schemacls = schemacls
        self.mapping = mapping
        self._boundfields = self._bindfields()


    def _bindfield(self, field: BaseField, name: str) -> BaseField:
        """
        Bind a field to its source mapping.

        Args:
            field: Original field instance
            name: Name of the field

        Returns:
            Field instance with source configuration applied
        """
        mapping = self.mapping.get(name)
        if mapping is None:
            return field

        if isinstance(mapping, str):
            newsource = mapping
            newtransform = field.transform
        elif isinstance(mapping, tuple) and len(mapping) == 2:
            newsource, newtransform = mapping
        elif callable(mapping):
            newsource = field.source
            newtransform = mapping
        else:
            raise ValueError(f"Invalid mapping for field '{name}': {mapping}")

        bound = field.__class__(
            name=field.name,
            source=newsource,
            transform=newtransform,
            required=field.required,
            default=field.default,
            **getattr(field, '_kwargs', {})
        )
        return bound

    def _bindfields(self) -> t.Dict[str, BaseField]:
        """
        Create field instances with source mappings applied.

        Returns:
            Dict of fieldname -> bound field instance
        """
        bindings = {}
        for name, field in self.schemacls._fields.items():
            bound = self._bindfield(field, name)
            bindings[name] = bound
        return bindings


    def transform(self, data: t.Any) -> t.Dict[str, t.Any]:
        """
        Transform data using bound field mappings.

        Args:
            data: Source data to transform

        Returns:
            Transformed data as dictionary
        """
        result = {}

        for fieldname, boundfield in self._boundfields.items():
            try:
                result[fieldname] = boundfield.extract(data)
            except Exception as e:
                raise ValueError(f"Error transforming field '{fieldname}': {str(e)}")

        return result

    def __repr__(self) -> str:
        return f"BoundSchema({self.schemacls.__name__}, mappings={len(self.mapping)})"

class Schema(BaseSchema):
    """
    Concrete schema class for defining data transformations.

    Users inherit from this class and define fields as class attributes.
    The metaclass automatically discovers fields and creates the schema.
    """
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.fromfields = self.FromFields
        self.merge = self.Merge
        self.copy = self.Copy

    def _typeconvert(self, data: t.Dict[str, t.Any], typetarget: t.Type) -> t.Any:
        """
        Convert dict result to specified target type.

        Args:
            data: Dictionary data to convert
            typetarget: Target type to convert to

        Returns:
            Data converted to target type
        """
        if typetarget is dict:
            return data

        for attr in ['__dataclass_fields__', '_fields', '__pydantic_model__']:
            if hasattr(typetarget, attr):
                if hasattr(typetarget ,'model_validate'):
                    return typetarget.model_validate(data)
                return typetarget(**data)

        if hasattr(typetarget, '__annotations__') and hasattr(typetarget, '__total__'):
            return data

        try:
            return typetarget(**data)
        except Exception as e:
            raise ValueError(f"Cannot convert to {typetarget}: {e}")


    def transform(self, data: t.Any, typetarget: t.Optional[t.Type] = None) -> t.Any:
        """
        Transform source data using schema's field definitions.

        Args:
            data: Source data to transform
            typetarget: Optional target type (dict, dataclass, etc.)

        Returns:
            Transformed data in specified format
        """
        result = {}

        for name, field in self._fields.items():
            try:
                result[name] = field.extract(data)
            except Exception as e:
                raise ValueError(f"Schema transformation failed on field '{name}': {e}")

        if typetarget is not None:
            return self._typeconvert(result, typetarget)
        return result

    def bind(self, mapping: t.Dict[str, t.Any]) -> BoundSchema:
        """
        Create a bound schema with source-specific field mappings.

        Args:
            mapping: Dict mapping field names to source paths/transforms

        Returns:
            BoundSchema instance configured for specific data source
        """
        return BoundSchema(
            schemacls=self.__class__,
            mapping=mapping
        )

    def validate(self, data: t.Any) -> t.Dict[str, t.Any]:
        """
        Enhanced validation with detailed error reporting.

        Args:
            data: Data to validate

        Returns:
            Dict of fieldname -> validation errors (empty if valid)
        """
        errors = {}

        for fieldname, field in self._fields.items():
            try:
                field.extract(data)
            except Exception as e:
                errors[fieldname] = str(e)

        return errors

    @classmethod
    def FromFields(cls, **fields: 'BaseField') -> t.Type['Schema']:
        """
        Create a schema class dynamically from field definitions.

        Args:
            **fields: Field definitions

        Returns:
            New schema class with specified fields
        """
        # Create new class with fields as attributes
        attrs = dict(fields)
        return type(f"Dynamic{cls.__name__}", (cls,), attrs)

    @classmethod
    def Merge(cls, *schemas: t.Type['Schema']) -> t.Type['Schema']:
        """
        Merge multiple schemas into a single schema.

        Args:
            *schemas: Schema classes to merge

        Returns:
            New schema class with fields from all input schemas
        """
        merged = {}
        for schema in schemas:
            if hasattr(schema, '_fields'):
                merged.update(schema._fields)

        return type(f"Merged{cls.__name__}", (cls, ), merged)

    @classmethod
    def Copy(cls, **overrides: 'BaseField') -> t.Type['Schema']:
        """
        Create a copy of this schema with field overrides.

        Args:
            **overrides: Fields to override or add

        Returns:
            New schema class with updated fields
        """
        # Start with current fields
        new = cls._fields.copy()

        # Apply overrides
        new.update(overrides)

        return type(f"Copy{cls.__name__}", (Schema,), new)

    def subset(self, *fieldnames: str) -> t.Type['Schema']:
        """
        Create a schema with only specified fields.

        Args:
            *fieldnames: Names of fields to include

        Returns:
            New schema class with subset of fields
        """
        subsets = {
            name: field for name, field in self._fields.items()
            if name in fieldnames
        }

        if not subsets:
            raise ValueError(f"No valid fields found in subset: {fieldnames}")

        return type(f"Subset{self.__class__.__name__}", (Schema,), subsets)

    def transformplural(self, datalist: t.List[t.Any], typetarget: t.Optional[t.Type] = None) -> t.List[t.Any]:
        """
        Transform multiple data objects using this schema.

        Args:
            datalist: List of data objects to transform
            typetarget: Optional target type for each result

        Returns:
            List of transformed data objects
        """
        results = []

        for i, data in enumerate(datalist):
            try:
                result = self.transform(data, typetarget)
                results.append(result)
            except Exception as e:
                raise ValueError(f"Failed to transform item {i}: {e}")

        return results


    def __call__(self, data: t.Any, typetarget: t.Optional[t.Type] = None) -> t.Any:
        """
        Make schema instances callable for convenient transformation.

        Args:
            data: Source data to transform
            typetarget: Optional target type

        Returns:
            Transformed data
        """
        return self.transform(data, typetarget)
