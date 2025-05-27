# SCHEMATIX - CHANGELOG

## [0.3.0] -- May 27th, 2025
### Complete Schema Implementation
* **Concrete Schema Class**: Full implementation of `Schema` with transformation, validation, and composition
* **Target Type Conversion**: Support for dataclasses, Pydantic models, NamedTuples, TypedDict
* **Schema Composition**: `fromfields()`, `merge()`, `copy()`, `subset()` methods for flexible schema building
* **Batch Processing**: `transformplural()` for processing lists of data objects
* **Callable Interface**: Schema instances are callable for convenient transformation

### Comprehensive Test Suite
* **93 Passing Tests**: Complete test coverage across all components
* **Unit Tests**: Individual field and schema functionality
* **Integration Tests**: Real-world transformation workflows
* **Edge Case Testing**: Error handling, validation, boundary conditions
* **Test Categories**: API transformation, web scraping, ETL pipelines, nested data

### Production Ready Features
* **Error Handling**: Detailed error messages with field-level reporting
* **Validation System**: Schema and field-level validation with comprehensive error reporting
* **Performance Optimized**: Efficient field extraction and operator chaining
* **Memory Management**: Proper cleanup and resource handling

### Bug Fixes & Stability
* **Operator Chaining**: Fixed field flattening in combined and accumulated operations
* **String Accumulation**: Proper separator handling in AccumulatedField
* **Field Assignment**: Robust object attribute assignment across different types
* **Fallback Logic**: Improved SourceField fallback detection and handling
* **Dict Merging**: Correct dictionary combination in AccumulatedField

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
