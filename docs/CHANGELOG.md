# SCHEMATIX - CHANGELOG

## [0.2.0] -- May 27th, 2025
### Core Foundation
* **Metaclasses**: Implemented `SchemaMeta` for automatic field discovery and `FieldMeta` (skeleton for future extension)
* **Base Classes**: Created `BaseField` (abstract field interface) and `BaseSchema` (abstract schema interface)
* **Core Field Types**:
  - `Field` - Basic concrete field implementation with source/target support
  - `BoundField` - Complete source-to-target transformation binding
  - `SourceField` - Enhanced extraction with fallbacks and conditions
  - `TargetField` - Enhanced assignment with formatting and multiple targets

### Operator Overloading System
* **Pipeline Operator** (`>>`): `source_field >> target_field` → `BoundField`
* **Fallback Operator** (`|`): `primary_field | backup_field` → `FallbackField`
* **Combine Operator** (`&`): `field1 & field2` → `CombinedField`
* **Nested Operator** (`@`): `field @ "nested.path"` → `NestedField`
* **Accumulate Operator** (`+`): `field1 + field2` → `AccumulatedField`
* **Method Chaining**: Equivalent methods for all operators (`.pipeline()`, `.fallback()`, etc.)

### Specialized Field Classes
* **`FallbackField`**: Try primary field, fall back to secondary on failure
* **`CombinedField`**: Apply multiple fields and merge results into single dict
* **`NestedField`**: Apply field operations to nested data paths
* **`AccumulatedField`**: Smart type-based value combination (strings, numbers, dicts, lists)

### Schema Infrastructure
* **`BoundSchema`**: Schema instances bound to specific source mappings
* **`FieldBindingFactory`**: Factory methods for creating bound fields from various inputs
* **Field Discovery**: Automatic field detection and organization via metaclass

### Architecture
* **Type-agnostic Design**: Works with dicts, dataclasses, any attributable objects
* **Nested Path Support**: Handle complex data structures with dot notation
* **Error Handling**: Comprehensive validation and clear error messages
* **Extensible**: Clean inheritance hierarchy for custom field types

## [0.1.0] -- May 27th, 2025
* project initialized
