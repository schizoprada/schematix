# SCHEMATIX - CHANGELOG

## [0.4.6] -- June 17th, 2025
+ **Updated BaseField __repr__**: Updated `BaseField` representation to include new attributes added in [0.4.5]

## [0.4.5] -- June 15th, 2025
### Enhanced Field System
* **Type Conversion**: Built-in type conversion with `Field(type=int)` for automatic value casting
* **Choices Validation**: Constrain field values with `Field(choices=[1,2,3,4,5])` for data validation
* **Value Mapping**: Transform values through lookup tables with `Field(mapping=BRAND_IDS, mapper=fuzzy_func)`
* **Flexible Mapping**: User-defined mapper functions with signature `mapper(value, mapping_dict) -> mapped_value`
* **Enhanced Pipeline**: Extraction order: source → transform → type → mapping → choices → validate → required

### Conditional Fields & Dependencies
* **Conditional Fields**: Dynamic field behavior based on other field values with `Field(conditional=True)`
* **Dependency System**: Fields can depend on other computed values via `dependencies=['field1', 'field2']`
* **Multiple Conditions**: Support for 'value', 'required', 'default', 'transform', 'choices', 'type', 'mapping' conditions
* **Automatic Dependency Resolution**: Topological sorting ensures fields execute in correct dependency order
* **Circular Dependency Detection**: Clear error messages for invalid dependency graphs

### Transient Fields
* **Transient Field Support**: Fields used for computation but excluded from final output with `transient=True`
* **Clean Data Flow**: Separate computation fields from result fields for complex transformations

### Production Features
* **Robust Error Handling**: Detailed error messages for type conversion, mapping, and dependency failures
* **Performance Optimized**: Dependency resolution computed once at schema creation time
* **Backward Compatible**: All existing Field functionality preserved, new features are additive
* **Comprehensive Testing**: Full test coverage for new pipeline, conditional logic, and dependency resolution

### Advanced Use Cases
* **E-commerce Product Schemas**: Dynamic category mapping based on gender/brand combinations
* **Conditional Validation**: Required fields that depend on other field combinations
* **Multi-stage Transformations**: Complex data pipelines with intermediate computed values
* **Fuzzy Data Matching**: Custom mapper functions for flexible value transformation

## [0.4.0] -- May 29th, 2025
### Transform System Architecture
* **BaseTransform & Transform Classes**: Complete transform composition system with operator overloading (`>>`, `|`, `&`)
* **Transform Composition**: PipelineTransform, FallbackTransform, ParallelTransform for complex transformation chains
* **Context-Aware Transforms**: Support for transforms that access full source data context
* **Operator Overloading**: Intuitive `>>` (pipeline), `|` (fallback), `&` (parallel) operators with method chaining equivalents
* **@transform Decorator**: Clean decorator syntax for creating transforms from functions

### Comprehensive Transform Library
* **Text Transforms**: String manipulation, regex operations, encoding/decoding, formatting (35+ transforms)
* **Number Transforms**: Type conversion, math operations, rounding, range validation, formatting (30+ transforms)
* **Date Transforms**: Parsing, formatting, arithmetic, timezone handling, component extraction (40+ transforms)
* **Collection Transforms**: List/dict operations, filtering, mapping, aggregation, set operations (25+ transforms)
* **Validation Transforms**: Format validation, content checks, cleaning, requirements with error handling (20+ transforms)
* **Common Transforms**: Pre-built patterns combining multiple modules for real-world use cases (25+ transforms)

### Transform Module Organization
* **Modular Design**: Separate modules (text, numbers, dates, collections, validation, common) with short aliases
* **Class-Based Grouping**: Logical organization (encode/decode, format, parse, clean, safe, requires)
* **Factory Functions**: Parameterized transforms for flexible configuration
* **Static Method Transforms**: Clean API for common operations

### Advanced Features
* **Pipeline Composition**: Chain multiple transforms with automatic error propagation
* **Fallback Logic**: Primary/backup transform patterns with graceful error handling
* **Parallel Execution**: Apply multiple transforms simultaneously with custom result combiners
* **Safe Operations**: Transforms with default fallbacks that never raise errors
* **Multi-field Transforms**: Context-aware transforms accessing multiple source fields
* **Conditional Transforms**: Apply different transforms based on runtime conditions

### Production Quality
* **156 Passing Tests**: Comprehensive test coverage across all transform modules and compositions
* **Error Handling**: Robust error propagation with detailed error messages
* **Type Safety**: Full type hints throughout transform system
* **Performance Optimized**: Efficient transform chaining and operator overloading
* **Memory Safe**: Proper cleanup and resource management

### Integration & Usability
* **Field Integration**: Transforms work seamlessly with existing Field system
* **Intuitive API**: Consistent calling patterns and predictable behavior
* **Real-world Patterns**: Pre-built pipelines for common data processing tasks
* **Documentation**: Extensive examples and usage patterns for all transform types

## [0.3.6] -- May 29th, 2025
### Decorator API
* **@schema Decorator**: Convert regular classes to Schema classes with field auto-discovery
* **@field Decorator Suite**: Complete decorator ecosystem for all field types
 - `@field` - Basic Field creation from class attributes
 - `@field.source` - SourceField with enhanced extraction capabilities
 - `@field.target` - TargetField with enhanced assignment features
 - `@field.bound` - BoundField for complete source-to-target binding
 - `@field.fallback` - FallbackField for primary/backup field logic
 - `@field.combined` - CombinedField for merging multiple field results
 - `@field.nested` - NestedField for applying fields to nested data paths
 - `@field.accumulated` - AccumulatedField for smart value combination

### Advanced Field Configuration
* **Dynamic Constructor Inspection**: Automatic validation of required decorator attributes using `inspect` module
* **Flexible Field Naming**: Schema metaclass controls field naming for maximum reusability across contexts
* **Enhanced Type Validation**: Robust input validation for complex field configurations (lists, field instances)
* **Comprehensive Error Handling**: Clear error messages for missing required attributes and invalid configurations

### API Improvements
* **Functional Programming Style**: Clean decorator syntax alongside existing class-based API
* **Constructor Introspection**: Dynamic validation based on actual field constructor signatures
* **Extended __constructs__ Pattern**: Systematic attribute mapping for all field types
* **Context-Aware Naming**: Field names determined by usage context rather than definition context

### Testing & Quality
* **27 Passing Decorator Tests**: Comprehensive test coverage for all decorator functionality
* **Integration Testing**: End-to-end decorator usage with schema composition
* **Error Case Validation**: Thorough testing of invalid inputs and edge cases
* **Documentation Examples**: Real-world usage patterns and best practices

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
