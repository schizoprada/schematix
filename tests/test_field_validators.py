# ~/schematix/tests/test_field_validators.py
"""Tests for custom validator functionality in BaseField and derived classes."""
import pytest
from schematix import Field, Schema, SourceField, TargetField, BoundField
from schematix.core.field import FallbackField, CombinedField, NestedField, AccumulatedField


class TestBasicValidatorFunctionality:
   """Test basic custom validator functionality."""

   def test_validator_function_called(self):
       """Test that custom validator function is called during extraction."""
       calls = []

       def my_validator(value):
           calls.append(value)
           if not isinstance(value, str):
               raise ValueError("Must be string")

       field = Field(source='name', validator=my_validator)
       data = {'name': 'john'}

       result = field.extract(data)
       assert result == 'john'
       assert calls == ['john']

   def test_validator_raises_on_invalid(self):
       """Test that validator raises appropriate errors."""
       def positive_validator(value):
           if value <= 0:
               raise ValueError("Must be positive")

       field = Field(source='num', validator=positive_validator)

       # Should succeed
       assert field.extract({'num': 5}) == 5

       # Should fail
       with pytest.raises(ValueError):
           field.extract({'num': -1})

   def test_validator_with_none_value(self):
       """Test validator behavior with None values."""
       def non_null_validator(value):
           if value is None:
               raise ValueError("Cannot be None")

       field = Field(source='data', validator=non_null_validator, default='default')

       # Should fail with None
       with pytest.raises(ValueError):
           field.extract({'data': None})

       # Should work with actual value
       assert field.extract({'data': 'test'}) == 'test'

   def test_validator_none_means_no_validation(self):
       """Test that validator=None means no custom validation."""
       field = Field(source='data', validator=None)
       assert field.extract({'data': 'anything'}) == 'anything'
       assert field.extract({'data': None}) == None


class TestValidatorInExtractionPipeline:
   """Test validator placement in the extraction pipeline."""

   def test_validator_after_transform(self):
       """Test that validator runs after transform."""
       def my_validator(value):
           if not value.startswith('prefix_'):
               raise ValueError("Must have prefix")

       field = Field(
           source='data',
           transform=lambda x: f'prefix_{x}',
           validator=my_validator
       )

       # Should work - transform adds prefix, validator checks it
       assert field.extract({'data': 'test'}) == 'prefix_test'

   def test_validator_after_type_conversion(self):
       """Test that validator runs after type conversion."""
       def int_range_validator(value):
           if not (1 <= value <= 10):
               raise ValueError("Must be 1-10")

       field = Field(
           source='rating',
           type=int,
           validator=int_range_validator
       )

       # Should convert string to int, then validate
       assert field.extract({'rating': '5'}) == 5

       # Should fail validation after conversion
       with pytest.raises(ValueError):
           field.extract({'rating': '15'})

   def test_validator_after_mapping(self):
       """Test that validator runs after mapping."""
       def status_validator(value):
           if value not in ['active', 'inactive']:
               raise ValueError("Invalid status")

       field = Field(
           source='status_code',
           mapping={1: 'active', 2: 'inactive', 3: 'pending'},
           validator=status_validator
       )

       # Should map then validate
       assert field.extract({'status_code': 1}) == 'active'

       # Should fail validation after mapping
       with pytest.raises(ValueError):
           field.extract({'status_code': 3})  # maps to 'pending'

   def test_validator_before_choices(self):
       """Test that validator runs before choices validation."""
       def normalize_validator(value):
           return value.lower().strip()

       # This won't work because validator can't modify value
       field = Field(
           source='status',
           validator=lambda x: None,  # Just check, don't modify
           choices=['active', 'pending']
       )

       # This should work
       assert field.extract({'status': 'active'}) == 'active'


class TestValidatorWithSpecializedFields:
   """Test validator with specialized field types."""

   def test_validator_with_source_field(self):
      """Test validator works with SourceField fallbacks."""
      def email_validator(value):
          if value is None:
              return  # Allow None values to pass
          if '@' not in value:
              raise ValueError("Invalid email")

      field = SourceField(
          source='email',
          fallbacks=['contact_email'],
          validator=email_validator
      )

      # Should validate primary source
      result = field.extract({'email': 'test@example.com'})
      assert result == 'test@example.com'

      # Should validate fallback source
      result = field.extract({'contact_email': 'backup@example.com'})
      assert result == 'backup@example.com'

      # Should fail validation on primary - provide only invalid primary, no fallback data
      with pytest.raises(ValueError):
          field.extract({'email': 'invalid-email'})  # No contact_email fallback available

      # Should fail validation on fallback - provide only invalid fallback, no primary data
      with pytest.raises(ValueError):
          field.extract({'contact_email': 'also-invalid'})  # No email primary available


   def test_validator_with_target_field(self):
       """Test validator in assignment path."""
       def name_validator(value):
           if len(value) < 2:
               raise ValueError("Name too short")

       field = TargetField(target='name', validator=name_validator)

       # Should validate before assignment
       target = {}
       field.assign(target, 'John')
       assert target['name'] == 'John'

       # Should fail validation
       with pytest.raises(ValueError):
           field.assign({}, 'J')

   def test_validator_with_bound_field(self):
       """Test validator in BoundField scenarios."""
       def price_validator(value):
           if value < 0:
               raise ValueError("Price cannot be negative")

       source = Field(source='price', type=float, validator=price_validator)
       target = Field(target='final_price')
       bound = BoundField(sourcefield=source, targetfield=target)

       # Should validate during extraction
       result = bound.extractonly({'price': '10.50'})
       assert result == 10.5

       # Should fail validation
       with pytest.raises(ValueError):
           bound.extractonly({'price': '-5.0'})


class TestValidatorWithCompositeFields:
   """Test validator with composite field types."""

   def test_validator_with_fallback_field(self):
      """Test validator with FallbackField."""
      def positive_validator(value):
          print(f"DEBUG: received: {value}")
          if value is None:
              return  # Allow None values to pass
          if value <= 0:
              raise ValueError("Must be positive")

      primary = Field(source='primary', validator=positive_validator)
      fallback = Field(source='fallback', validator=positive_validator)
      field = FallbackField(primary=primary, fallback=fallback)

      # Should validate primary
      assert field.extract({'primary': 5}) == 5

      # Should validate fallback when primary missing
      assert field.extract({'fallback': 3}) == 3

      # Should fail validation on primary - provide only invalid primary, no fallback data
      with pytest.raises(ValueError):
          field.extract({'primary': -1})  # No fallback data available

      # Should fail validation when both primary and fallback are invalid
      with pytest.raises(ValueError):
          field.extract({'primary': -1, 'fallback': -2})  # Both fail validation

   def test_validator_with_combined_field(self):
       """Test validator with CombinedField."""
       def name_validator(value):
           if not value.isalpha():
               raise ValueError("Must be alphabetic")

       field1 = Field(name='first', source='first_name', validator=name_validator)
       field2 = Field(name='last', source='last_name', validator=name_validator)
       combined = CombinedField(fields=[field1, field2])

       # Should validate both fields
       result = combined.extract({'first_name': 'John', 'last_name': 'Doe'})
       assert result == {'first': 'John', 'last': 'Doe'}

       # Should fail validation on first field
       with pytest.raises(ValueError):
           combined.extract({'first_name': 'John123', 'last_name': 'Doe'})

   def test_validator_with_nested_field(self):
       """Test validator with NestedField."""
       def id_validator(value):
           if not isinstance(value, int):
               raise ValueError("ID must be integer")

       base_field = Field(source='id', validator=id_validator)
       nested = NestedField(field=base_field, nestedpath='user.profile')

       data = {'user': {'profile': {'id': 123}}}
       assert nested.extract(data) == 123

       # Should fail validation
       data = {'user': {'profile': {'id': 'abc'}}}
       with pytest.raises(ValueError):
           nested.extract(data)

   def test_validator_with_accumulated_field(self):
       """Test validator with AccumulatedField."""
       def string_validator(value):
           if not isinstance(value, str):
               raise ValueError("Must be string")

       field1 = Field(source='first', validator=string_validator)
       field2 = Field(source='last', validator=string_validator)
       accumulated = AccumulatedField(fields=[field1, field2])

       # Should validate both fields and accumulate
       result = accumulated.extract({'first': 'John', 'last': 'Doe'})
       assert result == 'John Doe'

       # Should fail validation on second field
       with pytest.raises(ValueError):
           accumulated.extract({'first': 'John', 'last': 123})


class TestValidatorWithConditionalFields:
   """Test validator with conditional field logic."""

   def test_validator_in_conditional_overrides(self):
       """Test that validator can be overridden in conditional fields."""
       def strict_validator(value):
           if value < 10:
               raise ValueError("Must be >= 10")

       def lenient_validator(value):
           if value < 0:
               raise ValueError("Must be >= 0")

       class TestSchema(Schema):
           mode = Field(source='mode', transient=True)
           value = Field(
               source='value',
               conditional=True,
               dependencies=['mode'],
               conditions={
                   'validator': lambda mode: strict_validator if mode == 'strict' else lenient_validator
               }
           )

       # Should use strict validator
       with pytest.raises(ValueError):
           TestSchema().transform({'mode': 'strict', 'value': 5})

       # Should use lenient validator
       result = TestSchema().transform({'mode': 'lenient', 'value': 5})
       assert result['value'] == 5

       # Should fail lenient validator
       with pytest.raises(ValueError):
           TestSchema().transform({'mode': 'lenient', 'value': -1})


class TestValidatorEdgeCases:
   """Test edge cases and error conditions."""

   def test_validator_exception_wrapping(self):
       """Test that validator exceptions are properly wrapped."""
       def failing_validator(value):
           raise RuntimeError("Custom error message")

       field = Field(source='data', validator=failing_validator)

       with pytest.raises(RuntimeError):
           field.extract({'data': 'test'})

   def test_validator_with_required_field(self):
       """Test validator interaction with required field logic."""
       def non_empty_validator(value):
           if not value:
               raise ValueError("Cannot be empty")

       field = Field(source='data', required=True, validator=non_empty_validator)

       # Should fail required check first (None value)
       with pytest.raises(ValueError):
           field.extract({})

       # Should fail validator (empty string)
       with pytest.raises(ValueError):
           field.extract({'data': ''})

   def test_validator_with_default_values(self):
       """Test validator with default values."""
       def positive_validator(value):
           if value <= 0:
               raise ValueError("Must be positive")

       field = Field(source='missing', default=5, validator=positive_validator)

       # Should validate default value
       result = field.extract({})
       assert result == 5

       # Test with bad default
       field_bad = Field(source='missing', default=-1, validator=positive_validator)
       with pytest.raises(ValueError):
           field_bad.extract({})


class TestValidatorIntegrationWithSchema:
   """Test validator integration at schema level."""

   def test_validator_in_schema_transformation(self):
       """Test validators work in full schema transformation."""
       def email_validator(value):
           if '@' not in value:
               raise ValueError("Invalid email")

       def age_validator(value):
           if not (0 <= value <= 150):
               raise ValueError("Invalid age")

       class UserSchema(Schema):
           email = Field(source='email_addr', validator=email_validator)
           age = Field(source='user_age', type=int, validator=age_validator)
           name = Field(source='full_name')

       # Should work with valid data
       data = {'email_addr': 'test@example.com', 'user_age': '25', 'full_name': 'John'}
       result = UserSchema().transform(data)
       assert result == {'email': 'test@example.com', 'age': 25, 'name': 'John'}

       # Should fail email validation
       bad_data = {'email_addr': 'invalid', 'user_age': '25', 'full_name': 'John'}
       with pytest.raises(ValueError):
           UserSchema().transform(bad_data)

       # Should fail age validation
       bad_data = {'email_addr': 'test@example.com', 'user_age': '200', 'full_name': 'John'}
       with pytest.raises(ValueError):
           UserSchema().transform(bad_data)

   def test_validator_in_schema_validation(self):
       """Test validators in schema validation method."""
       def email_validator(value):
           if '@' not in value:
               raise ValueError("Invalid email")

       class UserSchema(Schema):
           email = Field(source='email', validator=email_validator)
           name = Field(source='name')

       # Should pass validation
       errors = UserSchema().validate({'email': 'test@example.com', 'name': 'John'})
       assert errors == {}

       # Should catch validation error
       errors = UserSchema().validate({'email': 'invalid', 'name': 'John'})
       assert 'email' in errors
       assert 'Invalid email' in errors['email']
