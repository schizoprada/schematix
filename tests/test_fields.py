# ~/schematix/tests/test_fields.py
"""Tests for field classes and functionality."""
import pytest
from schematix import Field, SourceField, TargetField, BoundField
from schematix import FallbackField, CombinedField, NestedField, AccumulatedField


class TestField:
    """Test basic Field functionality."""

    def test_field_creation(self):
        """Test basic field creation."""
        field = Field(name='test', source='src', target='tgt')
        assert field.name == 'test'
        assert field.source == 'src'
        assert field.target == 'tgt'
        assert field.required is False
        assert field.default is None

    def test_field_extract_simple(self, sample_dict_data):
        """Test simple field extraction."""
        field = Field(source='user_id')
        result = field.extract(sample_dict_data)
        assert result == 123

    def test_field_extract_nested(self, sample_dict_data):
        """Test nested field extraction."""
        field = Field(source='profile.bio')
        result = field.extract(sample_dict_data)
        assert result == 'Software developer'

    def test_field_extract_with_transform(self, sample_dict_data):
        """Test field extraction with transformation."""
        field = Field(source='first_name', transform=str.upper)
        result = field.extract(sample_dict_data)
        assert result == 'JOHN'

    def test_field_extract_required_missing(self):
        """Test required field extraction when missing."""
        field = Field(source='missing', required=True)
        with pytest.raises(ValueError, match="required field"):
            field.extract({})

    def test_field_extract_with_default(self):
        """Test field extraction with default value."""
        field = Field(source='missing', default='default_value')
        result = field.extract({})
        assert result == 'default_value'

    def test_field_assign_simple(self):
        """Test simple field assignment."""
        field = Field(target='name')
        target_obj = {}
        field.assign(target_obj, 'John')
        assert target_obj['name'] == 'John'

    def test_field_assign_nested(self):
        """Test nested field assignment."""
        field = Field(target='user.profile.name')
        target_obj = {}
        field.assign(target_obj, 'John')
        assert target_obj['user']['profile']['name'] == 'John'

    def test_field_assign_to_object(self):
        """Test field assignment to object attributes."""
        class TestObj:
            pass

        field = Field(target='name')
        target_obj = TestObj()
        field.assign(target_obj, 'John')
        assert target_obj.name == 'John'


class TestSourceField:
    """Test SourceField enhanced functionality."""

    def test_sourcefield_fallbacks(self, sample_dict_data):
        """Test SourceField with fallback sources."""
        field = SourceField(
            source='missing_field',
            fallbacks=['user_id', 'another_missing'],
            default='fallback_default'
        )
        result = field.extract(sample_dict_data)
        assert result == 123  # Should get user_id from fallback

    def test_sourcefield_condition(self, sample_dict_data):
        """Test SourceField with condition."""
        # Condition that returns False
        field = SourceField(
            source='user_id',
            condition=lambda data: False,
            default='condition_failed'
        )
        result = field.extract(sample_dict_data)
        assert result == 'condition_failed'

        # Condition that returns True
        field = SourceField(
            source='user_id',
            condition=lambda data: True
        )
        result = field.extract(sample_dict_data)
        assert result == 123

    def test_sourcefield_addfallback(self):
        """Test adding fallback to SourceField."""
        field = SourceField(source='primary', fallbacks=['backup1'])
        new_field = field.addfallback('backup2')

        assert new_field.fallbacks == ['backup1', 'backup2']
        assert field.fallbacks == ['backup1']  # Original unchanged


class TestTargetField:
    """Test TargetField enhanced functionality."""

    def test_targetfield_formatter(self):
        """Test TargetField with formatter."""
        field = TargetField(target='name', formatter=str.upper)
        target_obj = {}
        field.assign(target_obj, 'john')
        assert target_obj['name'] == 'JOHN'

    def test_targetfield_condition(self):
        """Test TargetField with condition."""
        # Condition that returns False (should not assign)
        field = TargetField(
            target='name',
            condition=lambda value: value != 'skip'
        )
        target_obj = {}
        field.assign(target_obj, 'skip')
        assert 'name' not in target_obj

        # Condition that returns True (should assign)
        field.assign(target_obj, 'include')
        assert target_obj['name'] == 'include'

    def test_targetfield_multiple_targets(self):
        """Test TargetField with multiple targets."""
        field = TargetField(
            target='primary',
            additionaltargets=['secondary', 'tertiary']
        )
        target_obj = {}
        field.assign(target_obj, 'value')

        assert target_obj['primary'] == 'value'
        assert target_obj['secondary'] == 'value'
        assert target_obj['tertiary'] == 'value'

    def test_targetfield_addtarget(self):
        """Test adding target to TargetField."""
        field = TargetField(target='primary', additionaltargets=['secondary'])
        new_field = field.addtarget('tertiary')

        assert new_field.additionaltargets == ['secondary', 'tertiary']
        assert field.additionaltargets == ['secondary']  # Original unchanged


class TestFieldOperators:
    """Test field operator overloading."""

    def test_pipeline_operator(self, sample_dict_data):
        """Test >> operator (pipeline)."""
        source = Field(source='user_id')
        target = Field(target='id')
        bound = source >> target

        assert isinstance(bound, BoundField)
        assert bound.sourcefield == source
        assert bound.targetfield == target

    def test_fallback_operator(self, sample_dict_data):
        """Test | operator (fallback)."""
        primary = Field(source='missing')
        fallback = Field(source='user_id')
        combined = primary | fallback

        assert isinstance(combined, FallbackField)
        result = combined.extract(sample_dict_data)
        assert result == 123  # Should get fallback value

    def test_combine_operator(self, sample_dict_data):
        """Test & operator (combine)."""
        field1 = Field(name='id', source='user_id')
        field2 = Field(name='email', source='email_address')
        combined = field1 & field2

        assert isinstance(combined, CombinedField)
        result = combined.extract(sample_dict_data)
        assert result['id'] == 123
        assert result['email'] == 'test@example.com'

    def test_nested_operator(self, sample_nested_data):
        """Test @ operator (nested)."""
        field = Field(source='id')
        nested = field @ 'user.info'

        assert isinstance(nested, NestedField)
        result = nested.extract(sample_nested_data)
        assert result == 456

    def test_accumulate_operator(self, sample_dict_data):
        """Test + operator (accumulate)."""
        first = Field(source='first_name')
        last = Field(source='last_name')
        combined = first + last

        assert isinstance(combined, AccumulatedField)
        result = combined.extract(sample_dict_data)
        assert result == 'John Doe'  # Default space separator

    def test_method_chaining_equivalents(self, sample_dict_data):
        """Test method chaining equivalents of operators."""
        source = Field(source='user_id')
        target = Field(target='id')

        # Test each method
        bound = source.pipeline(target)
        assert isinstance(bound, BoundField)

        primary = Field(source='missing')
        fallback_field = Field(source='user_id')
        fallback_result = primary.fallback(fallback_field)
        assert isinstance(fallback_result, FallbackField)

        field1 = Field(name='test', source='user_id')
        field2 = Field(name='test2', source='email_address')
        combined = field1.combine(field2)
        assert isinstance(combined, CombinedField)

        nested = source.nested('profile')
        assert isinstance(nested, NestedField)

        accumulated = field1.accumulate(field2)
        assert isinstance(accumulated, AccumulatedField)


class TestBoundField:
    """Test BoundField functionality."""

    def test_boundfield_creation(self):
        """Test BoundField creation."""
        source = Field(name='test', source='src')
        target = Field(name='test', target='tgt')
        bound = BoundField(sourcefield=source, targetfield=target)

        assert bound.sourcefield == source
        assert bound.targetfield == target
        assert bound.name == 'test'

    def test_boundfield_transformdata(self, sample_dict_data):
        """Test BoundField complete transformation."""
        source = Field(source='user_id')
        target = Field(target='id')
        bound = BoundField(sourcefield=source, targetfield=target)

        target_obj = {}
        bound.transformdata(sample_dict_data, target_obj)
        assert target_obj['id'] == 123

    def test_boundfield_extractonly(self, sample_dict_data):
        """Test BoundField extract-only operation."""
        source = Field(source='user_id', transform=lambda x: x * 2)
        target = Field(target='id')
        bound = BoundField(sourcefield=source, targetfield=target)

        result = bound.extractonly(sample_dict_data)
        assert result == 246  # 123 * 2

    def test_boundfield_withtransform(self, sample_dict_data):
        """Test BoundField with additional transform."""
        source = Field(source='first_name')
        target = Field(target='name')
        bound = BoundField(sourcefield=source, targetfield=target)

        new_bound = bound.withtransform(str.upper)
        result = new_bound.extractonly(sample_dict_data)
        assert result == 'JOHN'
