# ~/schematix/tests/test_value_pipeline.py
"""Tests for new value transformation pipeline: type, choices, mapping."""
import pytest
from schematix import Field


class TestTypePipeline:
   """Test type conversion in pipeline."""

   def test_type_conversion_basic(self):
       """Test basic type conversion."""
       field = Field(source='rating', type=int)
       data = {'rating': '5'}
       result = field.extract(data)
       assert result == 5
       assert isinstance(result, int)

   def test_type_conversion_failure(self):
       """Test type conversion failure."""
       field = Field(source='rating', type=int)
       data = {'rating': 'invalid'}
       with pytest.raises(ValueError, match="Cannot convert 'invalid' to int"):
           field.extract(data)


class TestChoicesPipeline:
   """Test choices validation in pipeline."""

   def test_choices_valid(self):
       """Test valid choice."""
       field = Field(source='status', choices=['pending', 'shipped', 'delivered'])
       data = {'status': 'shipped'}
       result = field.extract(data)
       assert result == 'shipped'

   def test_choices_invalid(self):
       """Test invalid choice."""
       field = Field(source='status', choices=['pending', 'shipped'])
       data = {'status': 'delivered'}
       with pytest.raises(ValueError, match="Value 'delivered' not in allowed choices"):
           field.extract(data)

   def test_type_then_choices(self):
       """Test type conversion then choices validation."""
       field = Field(source='rating', type=int, choices=[1, 2, 3, 4, 5])
       data = {'rating': '3'}
       result = field.extract(data)
       assert result == 3


class TestMappingPipeline:
   """Test value mapping in pipeline."""

   def test_mapping_direct_lookup(self):
       """Test direct mapping lookup."""
       mapping = {'nike': 'brand_001', 'adidas': 'brand_002'}
       field = Field(source='brand', mapping=mapping)
       data = {'brand': 'nike'}
       result = field.extract(data)
       assert result == 'brand_001'

   def test_mapping_with_mapper_function(self):
       """Test mapping with custom mapper function."""
       mapping = {'nike': 'brand_001', 'adidas': 'brand_002'}

       def fuzzy_mapper(value, mapping_dict):
           # Simple fuzzy logic - check if value is substring of any key
           for key, mapped_value in mapping_dict.items():
               if value.lower() in key.lower():
                   return mapped_value
           raise ValueError(f"No fuzzy match for {value}")

       field = Field(source='brand', mapping=mapping, mapper=fuzzy_mapper)
       data = {'brand': 'nik'}  # Partial match
       result = field.extract(data)
       assert result == 'brand_001'

   def test_mapping_no_match_no_mapper(self):
       """Test mapping with no match and no mapper function."""
       mapping = {'nike': 'brand_001'}
       field = Field(source='brand', mapping=mapping)
       data = {'brand': 'puma'}
       with pytest.raises(ValueError, match="No mapping found for value 'puma'"):
           field.extract(data)

   def test_mapping_no_match_with_default(self):
       """Test mapping with no match but default value."""
       mapping = {'nike': 'brand_001'}
       field = Field(source='brand', mapping=mapping, default='unknown_brand')
       data = {'brand': 'puma'}
       result = field.extract(data)
       assert result == 'unknown_brand'


class TestPipelineIntegration:
   """Test full pipeline integration."""

   def test_transform_type_choices(self):
       """Test transform → type → choices pipeline."""
       field = Field(
           source='rating',
           transform=str.strip,
           type=int,
           choices=[1, 2, 3, 4, 5]
       )
       data = {'rating': '  3  '}
       result = field.extract(data)
       assert result == 3

   def test_type_mapping_choices(self):
       """Test type → mapping → choices pipeline."""
       status_mapping = {1: 'pending', 2: 'shipped', 3: 'delivered'}
       field = Field(
           source='status_code',
           type=int,
           mapping=status_mapping,
           choices=['pending', 'shipped', 'delivered']
       )
       data = {'status_code': '2'}
       result = field.extract(data)
       assert result == 'shipped'

   def test_full_pipeline_with_error(self):
       """Test pipeline fails at choices validation."""
       mapping = {'low': 1, 'medium': 2, 'high': 3}
       field = Field(
           source='priority',
           mapping=mapping,
           choices=[1, 2]  # Excludes 'high' -> 3
       )
       data = {'priority': 'high'}
       with pytest.raises(ValueError, match="Value '3' not in allowed choices"):
           field.extract(data)
