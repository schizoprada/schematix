# ~/schematix/src/schematix/core/schema.py
from __future__ import annotations
import abc, typing as t

if t.TYPE_CHECKING:
    from schematix.core.bases.field import BaseField
    from schematix.core.bases.schema import BaseSchema

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
