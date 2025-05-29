# ~/schematix/tests/test_decorators.py
"""Tests for decorator API."""
import pytest
from schematix import schema, field, Field, SourceField, TargetField
from schematix import BoundField, FallbackField, CombinedField, NestedField, AccumulatedField


class TestSchemaDecorator:
    """Test @schema decorator functionality."""

    def test_basic_schema_decorator(self):
        """Test basic schema creation with decorator."""
        @schema
        class UserSchema:
            id = Field(source='user_id')
            email = Field(source='email_addr', required=True)
            name = Field(source='full_name')

        # Should be a Schema class
        assert hasattr(UserSchema, '_fields')
        assert hasattr(UserSchema, '_fieldnames')
        assert len(UserSchema._fields) == 3

        # Fields should be properly configured
        assert UserSchema._fields['id'].source == 'user_id'
        assert UserSchema._fields['email'].source == 'email_addr'
        assert UserSchema._fields['email'].required is True

    def test_schema_decorator_preserves_docstring(self):
        """Test that decorator preserves class docstring."""
        @schema
        class DocumentedSchema:
            """This is a test schema."""
            field1 = Field(source='test')

        assert DocumentedSchema.__doc__ == "This is a test schema."

    def test_schema_decorator_with_operators(self):
        """Test schema decorator with field operators."""
        @schema
        class OperatorSchema:
            id = Field(source='user_id')
            email = Field(source='email') | Field(source='contact_email')
            fullname = Field(source='first') + Field(source='last')

        # Should handle operator results
        assert len(OperatorSchema._fields) == 3
        assert isinstance(OperatorSchema._fields['email'], FallbackField)
        assert isinstance(OperatorSchema._fields['fullname'], AccumulatedField)

    def test_schema_transformation(self, sample_dict_data):
        """Test that decorated schema works for transformation."""
        @schema
        class TestSchema:
            id = Field(source='user_id')
            email = Field(source='email_address')
            name = Field(source='first_name')

        result = TestSchema().transform(sample_dict_data)
        assert result['id'] == 123
        assert result['email'] == 'test@example.com'
        assert result['name'] == 'John'


class TestFieldDecorator:
    """Test @field decorator functionality."""

    def test_basic_field_decorator(self):
        """Test basic field creation with decorator."""
        @field
        class UserID:
            source = 'user_id'
            required = True
            transform = int

        assert isinstance(UserID, Field)
        assert UserID.source == 'user_id'
        assert UserID.required is True
        assert UserID.transform == int
        assert UserID.name is None

    def test_field_decorator_with_explicit_name(self):
        """Test field decorator with explicit name."""
        @field
        class SomeField:
            source = 'test_source'
            name = 'custom_name'

        assert SomeField.name == 'custom_name'

    def test_field_decorator_minimal_config(self):
        """Test field decorator with minimal configuration."""
        @field
        class SimpleField:
            source = 'simple'

        assert SimpleField.source == 'simple'
        assert SimpleField.required is False
        assert SimpleField.default is None
        assert SimpleField.name is None

    def test_field_extraction(self, sample_dict_data):
        """Test that decorated field works for extraction."""
        @field
        class TestField:
            source = 'user_id'
            transform = lambda x: x * 2

        result = TestField.extract(sample_dict_data)
        assert result == 246  # 123 * 2


class TestSourceFieldDecorator:
    """Test @field.source decorator functionality."""

    def test_source_field_decorator(self):
        """Test SourceField creation with decorator."""
        @field.source
        class EmailField:
            source = 'email'
            fallbacks = ['contact_email', 'user_email']
            required = True

        assert isinstance(EmailField, SourceField)
        assert EmailField.source == 'email'
        assert EmailField.fallbacks == ['contact_email', 'user_email']
        assert EmailField.required is True
        assert EmailField.name is None

    def test_source_field_with_condition(self):
        """Test SourceField with condition."""
        @field.source
        class ConditionalField:
            source = 'test'
            condition = lambda data: data.get('active', True)

        assert ConditionalField.condition is not None
        assert callable(ConditionalField.condition)

    def test_source_field_fallback_functionality(self, sample_dict_data):
        """Test SourceField fallback behavior."""
        @field.source
        class FallbackField:
            source = 'missing_field'
            fallbacks = ['user_id']
            default = 'not_found'

        result = FallbackField.extract(sample_dict_data)
        assert result == 123  # Should get user_id from fallback


class TestTargetFieldDecorator:
    """Test @field.target decorator functionality."""

    def test_target_field_decorator(self):
        """Test TargetField creation with decorator."""
        @field.target
        class FormattedName:
            target = 'display_name'
            formatter = str.title
            additionaltargets = ['full_name']

        assert isinstance(FormattedName, TargetField)
        assert FormattedName.target == 'display_name'
        assert FormattedName.formatter == str.title
        assert FormattedName.additionaltargets == ['full_name']

    def test_target_field_assignment(self):
        """Test TargetField assignment behavior."""
        @field.target
        class TestTarget:
            target = 'test_field'
            formatter = str.upper

        target_obj = {}
        TestTarget.assign(target_obj, 'test value')
        assert target_obj['test_field'] == 'TEST VALUE'


class TestOperatorFieldDecorators:
    """Test operator result field decorators."""

    def test_bound_field_decorator(self):
        """Test @field.bound decorator."""
        source_field = Field(source='user_id')
        target_field = Field(target='id')

        @field.bound
        class UserMapping:
            sourcefield = source_field
            targetfield = target_field

        assert isinstance(UserMapping, BoundField)
        assert UserMapping.sourcefield == source_field
        assert UserMapping.targetfield == target_field

    def test_bound_field_decorator_minimal(self):
        """Test @field.bound with minimal config."""
        source_field = Field(source='test')

        @field.bound
        class SimpleMapping:
            sourcefield = source_field

        assert isinstance(SimpleMapping, BoundField)
        assert SimpleMapping.sourcefield == source_field
        assert SimpleMapping.targetfield == source_field  # Should default to sourcefield

    def test_bound_field_decorator_missing_source(self):
        """Test @field.bound with missing sourcefield."""
        with pytest.raises(ValueError):
            @field.bound
            class InvalidMapping:
                targetfield = Field(target='test')

    def test_fallback_field_decorator(self):
        """Test @field.fallback decorator."""
        primary_field = Field(source='email')
        fallback_field = Field(source='contact_email')

        @field.fallback
        class EmailFallback:
            primary = primary_field
            fallback = fallback_field

        assert isinstance(EmailFallback, FallbackField)
        assert EmailFallback.primary == primary_field
        assert EmailFallback.fallback == fallback_field

    def test_fallback_field_decorator_missing_fields(self):
        """Test @field.fallback with missing fields."""
        with pytest.raises(ValueError):
            @field.fallback
            class InvalidFallback:
                primary = Field(source='test')
                # Missing fallback

    def test_combined_field_decorator(self):
        """Test @field.combined decorator."""
        field1 = Field(name='id', source='user_id')
        field2 = Field(name='email', source='email_addr')

        @field.combined
        class UserFields:
            fields = [field1, field2]

        assert isinstance(UserFields, CombinedField)
        assert len(UserFields.fields) == 2
        assert UserFields.fields[0] == field1
        assert UserFields.fields[1] == field2

    def test_combined_field_decorator_invalid_fields(self):
        """Test @field.combined with invalid fields."""
        with pytest.raises(ValueError):
            @field.combined
            class InvalidCombined:
                fields = "not a list"

    def test_nested_field_decorator(self):
        """Test @field.nested decorator."""
        base_field = Field(source='name')

        @field.nested
        class NestedName:
            field = base_field
            nestedpath = 'user.profile'

        assert isinstance(NestedName, NestedField)
        assert NestedName.field == base_field
        assert NestedName.nestedpath == 'user.profile'

    def test_nested_field_decorator_missing_attributes(self):
        """Test @field.nested with missing attributes."""
        with pytest.raises(ValueError):
            @field.nested
            class InvalidNested:
                field = Field(source='test')
                # Missing nestedpath

    def test_accumulated_field_decorator(self):
        """Test @field.accumulated decorator."""
        field1 = Field(source='first_name')
        field2 = Field(source='last_name')

        @field.accumulated
        class FullName:
            fields = [field1, field2]
            separator = ' '

        assert isinstance(FullName, AccumulatedField)
        assert len(FullName.fields) == 2
        assert FullName.separator == ' '

    def test_accumulated_field_decorator_default_separator(self):
        """Test @field.accumulated with default separator."""
        field1 = Field(source='first')
        field2 = Field(source='last')

        @field.accumulated
        class DefaultSeparator:
            fields = [field1, field2]

        assert DefaultSeparator.separator == ' '  # Default

    def test_accumulated_field_decorator_invalid_fields(self):
        """Test @field.accumulated with invalid fields."""
        with pytest.raises(ValueError):
            @field.accumulated
            class InvalidAccumulated:
                fields = None


class TestDecoratorIntegration:
    """Test integration between schema and field decorators."""

    def test_schema_with_decorated_fields(self, sample_dict_data):
        """Test schema using decorated fields."""
        @field
        class UserID:
            source = 'user_id'
            required = True

        @field.source
        class EmailField:
            source = 'email_address'
            fallbacks = ['contact_email']

        @field.accumulated
        class FullName:
            fields = [
                Field(source='first_name'),
                Field(source='last_name')
            ]

        @schema
        class MixedSchema:
            id = UserID
            email = EmailField
            name = FullName

        result = MixedSchema().transform(sample_dict_data)
        assert result['id'] == 123
        assert result['email'] == 'test@example.com'
        assert result['name'] == 'John Doe'

    def test_complex_decorator_composition(self, sample_dict_data):
        """Test complex composition with decorators."""
        @field.source
        class PrimaryEmail:
            source = 'email_address'
            required = True

        @field.source
        class BackupEmail:
            source = 'contact_email'
            default = 'no-email@example.com'

        @field.fallback
        class EmailWithFallback:
            primary = PrimaryEmail
            fallback = BackupEmail

        @schema
        class ComplexSchema:
            id = Field(source='user_id')
            email = EmailWithFallback

        # Should work with existing data
        result = ComplexSchema().transform(sample_dict_data)
        assert result['id'] == 123
        assert result['email'] == 'test@example.com'

        # Should fallback when primary missing
        incomplete_data = {'user_id': 456}
        result2 = ComplexSchema().transform(incomplete_data)
        assert result2['id'] == 456
        assert result2['email'] == 'no-email@example.com'
