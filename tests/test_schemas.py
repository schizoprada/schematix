# ~/schematix/tests/test_schemas.py
"""Tests for schema classes and functionality."""
import pytest
from dataclasses import dataclass
from schematix import Schema, Field, SourceField


class TestSchema:
    """Test Schema class functionality."""

    def test_schema_creation(self):
        """Test basic schema creation."""
        class UserSchema(Schema):
            id = Field(source='user_id')
            email = Field(source='email_address', required=True)
            name = Field(source='first_name', default='Unknown')

        # Check field discovery
        assert 'id' in UserSchema._fields
        assert 'email' in UserSchema._fields
        assert 'name' in UserSchema._fields
        assert len(UserSchema._fields) == 3

        # Check field names are set correctly
        assert UserSchema._fields['id'].name == 'id'
        assert UserSchema._fields['email'].name == 'email'
        assert UserSchema._fields['name'].name == 'name'

    def test_schema_inheritance(self):
        """Test schema inheritance."""
        class BaseSchema(Schema):
            id = Field(source='id')
            created = Field(source='created_at')

        class UserSchema(BaseSchema):
            email = Field(source='email')
            name = Field(source='name')

        # Should have fields from both base and derived
        assert len(UserSchema._fields) == 4
        assert 'id' in UserSchema._fields
        assert 'created' in UserSchema._fields
        assert 'email' in UserSchema._fields
        assert 'name' in UserSchema._fields

    def test_schema_field_override(self):
        """Test field override in inheritance."""
        class BaseSchema(Schema):
            id = Field(source='base_id')
            name = Field(source='base_name')

        class DerivedSchema(BaseSchema):
            id = Field(source='derived_id')  # Override base field

        # Derived field should override base
        assert DerivedSchema._fields['id'].source == 'derived_id'
        assert DerivedSchema._fields['name'].source == 'base_name'

    def test_schema_transform_basic(self, sample_dict_data):
        """Test basic schema transformation."""
        class UserSchema(Schema):
            id = Field(source='user_id')
            email = Field(source='email_address')
            name = Field(source='first_name')

        schema = UserSchema()
        result = schema.transform(sample_dict_data)

        assert result['id'] == 123
        assert result['email'] == 'test@example.com'
        assert result['name'] == 'John'

    def test_schema_transform_with_target_type(self, sample_dict_data, user_dataclass):
        """Test schema transformation with target type conversion."""
        class UserSchema(Schema):
            id = Field(source='user_id')
            email = Field(source='email_address')
            name = Field(source='first_name')

        schema = UserSchema()
        result = schema.transform(sample_dict_data, typetarget=user_dataclass)

        assert isinstance(result, user_dataclass)
        assert result.id == 123
        assert result.email == 'test@example.com'
        assert result.name == 'John'

    def test_schema_validation(self, sample_dict_data):
        """Test schema validation."""
        class UserSchema(Schema):
            id = Field(source='user_id', required=True)
            email = Field(source='missing_field', required=True)
            name = Field(source='first_name')

        schema = UserSchema()
        errors = schema.validate(sample_dict_data)

        # Should have error for missing required field
        assert 'email' in errors
        assert 'id' not in errors  # This field exists
        assert 'name' not in errors  # This field is not required

    def test_schema_bind(self, sample_dict_data):
        """Test schema binding to source mapping."""
        class UserSchema(Schema):
            id = Field()
            email = Field(required=True)
            name = Field()

        schema = UserSchema()
        bound = schema.bind({
            'id': 'user_id',
            'email': 'email_address',
            'name': ('first_name', str.upper)
        })

        result = bound.transform(sample_dict_data)
        assert result['id'] == 123
        assert result['email'] == 'test@example.com'
        assert result['name'] == 'JOHN'  # Transformed

    def test_schema_callable(self, sample_dict_data):
        """Test schema as callable."""
        class UserSchema(Schema):
            id = Field(source='user_id')
            name = Field(source='first_name')

        schema = UserSchema()
        result = schema(sample_dict_data)  # Call directly

        assert result['id'] == 123
        assert result['name'] == 'John'

    def test_schema_transformplural(self, sample_list_data):
        """Test schema batch transformation."""
        class UserSchema(Schema):
            id = Field(source='id')
            name = Field(source='name')
            email = Field(source='email')

        schema = UserSchema()
        results = schema.transformplural(sample_list_data)

        assert len(results) == 3
        assert results[0]['name'] == 'Alice'
        assert results[1]['name'] == 'Bob'
        assert results[2]['name'] == 'Charlie'


class TestSchemaComposition:
    """Test schema composition methods."""

    def test_schema_fromfields(self):
        """Test creating schema from field definitions."""
        id_field = Field(source='user_id')
        email_field = Field(source='email_address', required=True)

        UserSchema = Schema.FromFields(
            id=id_field,
            email=email_field
        )

        assert 'id' in UserSchema._fields
        assert 'email' in UserSchema._fields
        assert UserSchema._fields['email'].required is True

    def test_schema_merge(self):
        """Test merging multiple schemas."""
        class BaseSchema(Schema):
            id = Field(source='id')
            created = Field(source='created_at')

        class ContactSchema(Schema):
            email = Field(source='email')
            phone = Field(source='phone')

        MergedSchema = Schema.Merge(BaseSchema, ContactSchema)

        assert len(MergedSchema._fields) == 4
        assert 'id' in MergedSchema._fields
        assert 'created' in MergedSchema._fields
        assert 'email' in MergedSchema._fields
        assert 'phone' in MergedSchema._fields

    def test_schema_copy(self):
        """Test copying schema with overrides."""
        class OriginalSchema(Schema):
            id = Field(source='id')
            name = Field(source='name')
            email = Field(source='email')

        schema = OriginalSchema()
        CopiedSchema = schema.copy(
            name=Field(source='full_name', transform=str.title),
            phone=Field(source='phone_number')
        )

        # Should have original fields plus overrides
        assert len(CopiedSchema._fields) == 4
        assert CopiedSchema._fields['name'].source == 'full_name'
        assert CopiedSchema._fields['name'].transform == str.title
        assert 'phone' in CopiedSchema._fields

    def test_schema_subset(self):
        """Test creating schema subset."""
        class FullSchema(Schema):
            id = Field(source='id')
            name = Field(source='name')
            email = Field(source='email')
            phone = Field(source='phone')

        schema = FullSchema()
        SubsetSchema = schema.subset('id', 'name')

        assert len(SubsetSchema._fields) == 2
        assert 'id' in SubsetSchema._fields
        assert 'name' in SubsetSchema._fields
        assert 'email' not in SubsetSchema._fields
        assert 'phone' not in SubsetSchema._fields

    def test_schema_subset_invalid_fields(self):
        """Test subset with invalid field names."""
        class TestSchema(Schema):
            id = Field(source='id')

        schema = TestSchema()
        with pytest.raises(ValueError, match="No valid fields"):
            schema.subset('nonexistent_field')


class TestSchemaEdgeCases:
    """Test schema edge cases and error conditions."""

    def test_schema_duplicate_field_names(self):
        """Test schema with duplicate field names should raise error."""
        with pytest.raises(ValueError, match="duplicate field names"):
            class DuplicateSchema(Schema):
                field1 = Field(name='same_name', source='source1')
                field2 = Field(name='same_name', source='source2')

    def test_schema_field_name_mismatch(self):
        """Test schema with field name mismatch should raise error."""
        with pytest.raises(ValueError, match="field name mismatch"):
            class MismatchSchema(Schema):
                fieldname = Field(name='different_name', source='source')

    def test_schema_transform_field_error(self, sample_dict_data):
        """Test schema transformation with field error."""
        class ErrorSchema(Schema):
            id = Field(source='user_id')
            missing = Field(source='nonexistent', required=True)

        schema = ErrorSchema()
        with pytest.raises(ValueError, match="Schema transformation failed"):
            schema.transform(sample_dict_data)

    def test_schema_invalid_target_type(self, sample_dict_data):
        """Test schema transformation with invalid target type."""
        class UserSchema(Schema):
            id = Field(source='user_id')

        class InvalidTarget:
            def __init__(self, invalid_param):
                pass

        schema = UserSchema()
        with pytest.raises(ValueError, match="Cannot convert"):
            schema.transform(sample_dict_data, typetarget=InvalidTarget)


class TestBoundSchema:
    """Test BoundSchema functionality."""

    def test_boundschema_creation(self):
        """Test BoundSchema creation."""
        class UserSchema(Schema):
            id = Field()
            email = Field(required=True)

        bound = UserSchema().bind({
            'id': 'user_id',
            'email': 'email_address'
        })

        assert bound.schemacls == UserSchema
        assert bound.mapping['id'] == 'user_id'
        assert bound.mapping['email'] == 'email_address'

    def test_boundschema_transform(self, sample_dict_data):
        """Test BoundSchema transformation."""
        class UserSchema(Schema):
            id = Field()
            email = Field()
            name = Field()

        bound = UserSchema().bind({
            'id': 'user_id',
            'email': 'email_address',
            'name': ('first_name', str.upper)
        })

        result = bound.transform(sample_dict_data)
        assert result['id'] == 123
        assert result['email'] == 'test@example.com'
        assert result['name'] == 'JOHN'

    def test_boundschema_partial_mapping(self, sample_dict_data):
        """Test BoundSchema with partial field mapping."""
        class UserSchema(Schema):
            id = Field(source='user_id')  # Has default source
            email = Field()               # Will be mapped

        bound = UserSchema().bind({
            'email': 'email_address'
        })

        result = bound.transform(sample_dict_data)
        assert result['id'] == 123      # From default source
        assert result['email'] == 'test@example.com'  # From mapping
