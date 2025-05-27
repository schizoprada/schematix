# ~/schematix/tests/test_specialized_fields.py
"""Tests for specialized field types from operators."""
import pytest
from schematix import Field, FallbackField, CombinedField, NestedField, AccumulatedField


class TestFallbackField:
    """Test FallbackField functionality."""

    def test_fallbackfield_creation(self):
        """Test FallbackField creation."""
        primary = Field(name='test', source='primary')
        fallback = Field(name='backup', source='fallback')
        field = FallbackField(primary=primary, fallback=fallback)

        assert field.primary == primary
        assert field.fallback == fallback
        assert field.name == 'test'  # Uses primary name

    def test_fallbackfield_primary_success(self, sample_dict_data):
        """Test FallbackField when primary succeeds."""
        primary = Field(source='user_id')
        fallback = Field(source='email_address')
        field = FallbackField(primary=primary, fallback=fallback)

        result = field.extract(sample_dict_data)
        assert result == 123  # Primary value

    def test_fallbackfield_primary_fails(self, sample_dict_data):
        """Test FallbackField when primary fails."""
        primary = Field(source='nonexistent')
        fallback = Field(source='user_id')
        field = FallbackField(primary=primary, fallback=fallback)

        result = field.extract(sample_dict_data)
        assert result == 123  # Fallback value

    def test_fallbackfield_both_fail(self):
        """Test FallbackField when both fields fail."""
        primary = Field(source='missing1', required=True)
        fallback = Field(source='missing2', required=True)
        field = FallbackField(primary=primary, fallback=fallback)

        with pytest.raises(ValueError):
            field.extract({})

    def test_fallbackfield_none_fallback(self, sample_dict_data):
        """Test FallbackField handling None values."""
        # Primary returns None but isn't required
        primary = Field(source='nonexistent', required=False)
        fallback = Field(source='user_id')
        field = FallbackField(primary=primary, fallback=fallback)

        result = field.extract(sample_dict_data)
        assert result == 123  # Should fallback when primary returns None

    def test_fallbackfield_assignment(self):
        """Test FallbackField assignment uses primary field."""
        primary = Field(target='primary_target')
        fallback = Field(target='fallback_target')
        field = FallbackField(primary=primary, fallback=fallback)

        target_obj = {}
        field.assign(target_obj, 'test_value')

        assert target_obj['primary_target'] == 'test_value'
        assert 'fallback_target' not in target_obj


class TestCombinedField:
    """Test CombinedField functionality."""

    def test_combinedfield_creation(self):
        """Test CombinedField creation."""
        field1 = Field(name='field1', source='src1')
        field2 = Field(name='field2', source='src2')
        combined = CombinedField(fields=[field1, field2])

        assert len(combined.fields) == 2
        assert combined.fields[0] == field1
        assert combined.fields[1] == field2

    def test_combinedfield_empty_fields(self):
        """Test CombinedField with empty fields list."""
        with pytest.raises(ValueError, match="requires at least one field"):
            CombinedField(fields=[])

    def test_combinedfield_extract(self, sample_dict_data):
        """Test CombinedField extraction."""
        field1 = Field(name='id', source='user_id')
        field2 = Field(name='email', source='email_address')
        field3 = Field(name='name', source='first_name')
        combined = CombinedField(fields=[field1, field2, field3])

        result = combined.extract(sample_dict_data)

        assert isinstance(result, dict)
        assert result['id'] == 123
        assert result['email'] == 'test@example.com'
        assert result['name'] == 'John'

    def test_combinedfield_extract_with_failures(self, sample_dict_data):
        """Test CombinedField extraction with some field failures."""
        field1 = Field(name='id', source='user_id')
        field2 = Field(name='missing', source='nonexistent', required=False)
        field3 = Field(name='email', source='email_address')
        combined = CombinedField(fields=[field1, field2, field3])

        result = combined.extract(sample_dict_data)

        # Should include successful extractions, skip failed non-required
        assert result['id'] == 123
        assert result['email'] == 'test@example.com'
        assert 'missing' not in result

    def test_combinedfield_required_field_fails(self, sample_dict_data):
        """Test CombinedField when required field fails."""
        field1 = Field(name='id', source='user_id')
        field2 = Field(name='missing', source='nonexistent', required=True)
        combined = CombinedField(fields=[field1, field2])

        with pytest.raises(ValueError, match="CombinedField extraction failed"):
            combined.extract(sample_dict_data)

    def test_combinedfield_assign_dict(self):
        """Test CombinedField assignment with dict value."""
        field1 = Field(name='id', target='user_id')
        field2 = Field(name='email', target='user_email')
        combined = CombinedField(fields=[field1, field2])

        target_obj = {}
        value = {'id': 123, 'email': 'test@example.com'}
        combined.assign(target_obj, value)

        assert target_obj['user_id'] == 123
        assert target_obj['user_email'] == 'test@example.com'

    def test_combinedfield_assign_single_value(self):
        """Test CombinedField assignment with single value."""
        field1 = Field(name='field1', target='target1')
        field2 = Field(name='field2', target='target2')
        combined = CombinedField(fields=[field1, field2])

        target_obj = {}
        combined.assign(target_obj, 'single_value')

        assert target_obj['target1'] == 'single_value'
        assert target_obj['target2'] == 'single_value'

    def test_combinedfield_addfield(self):
        """Test adding field to CombinedField."""
        field1 = Field(name='field1')
        field2 = Field(name='field2')
        field3 = Field(name='field3')

        combined = CombinedField(fields=[field1, field2])
        new_combined = combined.addfield(field3)

        assert len(new_combined.fields) == 3
        assert len(combined.fields) == 2  # Original unchanged
        assert new_combined.fields[2] == field3

    def test_combinedfield_chaining(self):
        """Test CombinedField operator chaining."""
        field1 = Field(name='field1')
        field2 = Field(name='field2')
        field3 = Field(name='field3')

        # Test (field1 & field2) & field3
        combined = field1 & field2 & field3

        assert isinstance(combined, CombinedField)
        assert len(combined.fields) == 3


class TestNestedField:
    """Test NestedField functionality."""

    def test_nestedfield_creation(self):
        """Test NestedField creation."""
        base_field = Field(source='name')
        nested = NestedField(field=base_field, nestedpath='user.profile')

        assert nested.field == base_field
        assert nested.nestedpath == 'user.profile'
        #assert 'user.profile' in nested.name

    def test_nestedfield_extract_simple(self, sample_nested_data):
        """Test NestedField extraction from nested data."""
        field = Field(source='id')
        nested = NestedField(field=field, nestedpath='user.info')

        result = nested.extract(sample_nested_data)
        assert result == 456

    def test_nestedfield_extract_deep_nesting(self, sample_nested_data):
        """Test NestedField with deeply nested path."""
        field = Field(source='name')
        nested = NestedField(field=field, nestedpath='user.profile')

        result = nested.extract(sample_nested_data)
        assert result == 'Jane Smith'

    def test_nestedfield_extract_missing_path(self):
        """Test NestedField with missing nested path."""
        field = Field(source='field', required=True)
        nested = NestedField(field=field, nestedpath='missing.path')

        with pytest.raises(ValueError, match="nested path.*not found"):
            nested.extract({})

    def test_nestedfield_extract_partial_path(self, sample_nested_data):
        """Test NestedField with partially missing path."""
        field = Field(source='missing_field', default='default_value')
        nested = NestedField(field=field, nestedpath='user.missing')

        result = nested.extract(sample_nested_data)
        assert result == 'default_value'

    def test_nestedfield_assign_simple(self):
        """Test NestedField assignment."""
        field = Field(target='name')
        nested = NestedField(field=field, nestedpath='user.profile')

        target_obj = {}
        nested.assign(target_obj, 'John Doe')

        assert target_obj['user']['profile']['name'] == 'John Doe'

    def test_nestedfield_assign_create_structure(self):
        """Test NestedField assignment creates nested structure."""
        field = Field(target='value')
        nested = NestedField(field=field, nestedpath='level1.level2.level3')

        target_obj = {}
        nested.assign(target_obj, 'deep_value')

        assert target_obj['level1']['level2']['level3']['value'] == 'deep_value'

    def test_nestedfield_assign_existing_structure(self):
        """Test NestedField assignment to existing structure."""
        field = Field(target='new_field')
        nested = NestedField(field=field, nestedpath='user')

        target_obj = {'user': {'existing': 'value'}}
        nested.assign(target_obj, 'new_value')

        assert target_obj['user']['existing'] == 'value'  # Preserved
        assert target_obj['user']['new_field'] == 'new_value'  # Added

    def test_nestedfield_withpath(self):
        """Test NestedField withpath method."""
        field = Field(source='name')
        nested = NestedField(field=field, nestedpath='original.path')
        new_nested = nested.withpath('new.path')

        assert new_nested.nestedpath == 'new.path'
        assert nested.nestedpath == 'original.path'  # Original unchanged
        assert new_nested.field == field  # Same field reference


class TestAccumulatedField:
    """Test AccumulatedField functionality."""

    def test_accumulatedfield_creation(self):
        """Test AccumulatedField creation."""
        field1 = Field(name='first', source='first_name')
        field2 = Field(name='last', source='last_name')
        accumulated = AccumulatedField(fields=[field1, field2])

        assert len(accumulated.fields) == 2
        assert accumulated.separator == ' '  # Default separator

    def test_accumulatedfield_empty_fields(self):
        """Test AccumulatedField with empty fields list."""
        with pytest.raises(ValueError, match="requires at least one field"):
            AccumulatedField(fields=[])

    def test_accumulatedfield_string_accumulation(self, sample_dict_data):
        """Test AccumulatedField string accumulation."""
        field1 = Field(source='first_name')
        field2 = Field(source='last_name')
        accumulated = AccumulatedField(fields=[field1, field2])

        result = accumulated.extract(sample_dict_data)
        assert result == 'John Doe'

    def test_accumulatedfield_custom_separator(self, sample_dict_data):
        """Test AccumulatedField with custom separator."""
        field1 = Field(source='first_name')
        field2 = Field(source='last_name')
        accumulated = AccumulatedField(fields=[field1, field2], separator=', ')

        result = accumulated.extract(sample_dict_data)
        assert result == 'John, Doe'

    def test_accumulatedfield_number_accumulation(self):
        """Test AccumulatedField number accumulation."""
        data = {'price': 100, 'tax': 15, 'shipping': 10}

        field1 = Field(source='price')
        field2 = Field(source='tax')
        field3 = Field(source='shipping')
        accumulated = AccumulatedField(fields=[field1, field2, field3])

        result = accumulated.extract(data)
        assert result == 125  # 100 + 15 + 10

    def test_accumulatedfield_list_accumulation(self):
        """Test AccumulatedField list accumulation."""
        data = {'tags1': ['python', 'web'], 'tags2': ['api', 'rest']}

        field1 = Field(source='tags1')
        field2 = Field(source='tags2')
        accumulated = AccumulatedField(fields=[field1, field2])

        result = accumulated.extract(data)
        assert result == ['python', 'web', 'api', 'rest']

    def test_accumulatedfield_dict_accumulation(self):
        """Test AccumulatedField dict accumulation."""
        data = {
            'basic': {'name': 'John', 'age': 30},
            'contact': {'email': 'john@test.com', 'phone': '123-456-7890'}
        }

        field1 = Field(source='basic')
        field2 = Field(source='contact')
        accumulated = AccumulatedField(fields=[field1, field2])

        result = accumulated.extract(data)
        expected = {
            'name': 'John',
            'age': 30,
            'email': 'john@test.com',
            'phone': '123-456-7890'
        }
        assert result == expected

    def test_accumulatedfield_mixed_types(self):
        """Test AccumulatedField with mixed types (fallback to string)."""
        data = {'number': 42, 'text': 'hello', 'boolean': True}

        field1 = Field(source='number')
        field2 = Field(source='text')
        field3 = Field(source='boolean')
        accumulated = AccumulatedField(fields=[field1, field2, field3])

        result = accumulated.extract(data)
        assert result == '42 hello True'  # Fallback to string concatenation

    def test_accumulatedfield_with_failures(self, sample_dict_data):
        """Test AccumulatedField with some field failures."""
        field1 = Field(source='first_name')
        field2 = Field(source='nonexistent', required=False)
        field3 = Field(source='last_name')
        accumulated = AccumulatedField(fields=[field1, field2, field3])

        result = accumulated.extract(sample_dict_data)
        assert result == 'John Doe'  # Skips failed non-required field

    def test_accumulatedfield_required_field_fails(self, sample_dict_data):
        """Test AccumulatedField when required field fails."""
        field1 = Field(source='first_name')
        field2 = Field(source='nonexistent', required=True)
        accumulated = AccumulatedField(fields=[field1, field2])

        with pytest.raises(ValueError, match="Required field.*failed in accumulation"):
            accumulated.extract(sample_dict_data)

    def test_accumulatedfield_assign(self):
        """Test AccumulatedField assignment uses first field."""
        field1 = Field(target='combined_name')
        field2 = Field(target='other_target')
        accumulated = AccumulatedField(fields=[field1, field2])

        target_obj = {}
        accumulated.assign(target_obj, 'John Doe')

        assert target_obj['combined_name'] == 'John Doe'
        assert 'other_target' not in target_obj  # Only first field used

    def test_accumulatedfield_addfield(self):
        """Test adding field to AccumulatedField."""
        field1 = Field(source='first')
        field2 = Field(source='second')
        field3 = Field(source='third')

        accumulated = AccumulatedField(fields=[field1, field2])
        new_accumulated = accumulated.addfield(field3)

        assert len(new_accumulated.fields) == 3
        assert len(accumulated.fields) == 2  # Original unchanged
        assert new_accumulated.fields[2] == field3

    def test_accumulatedfield_withseparator(self):
        """Test AccumulatedField withseparator method."""
        field1 = Field(source='first')
        field2 = Field(source='second')
        accumulated = AccumulatedField(fields=[field1, field2], separator=' ')
        new_accumulated = accumulated.withseparator(', ')

        assert new_accumulated.separator == ', '
        assert accumulated.separator == ' '  # Original unchanged
        assert new_accumulated.fields == accumulated.fields  # Same fields

    def test_accumulatedfield_chaining(self):
        """Test AccumulatedField operator chaining."""
        field1 = Field(source='first')
        field2 = Field(source='second')
        field3 = Field(source='third')

        # Test (field1 + field2) + field3
        accumulated = field1 + field2 + field3

        assert isinstance(accumulated, AccumulatedField)
        assert len(accumulated.fields) == 3
