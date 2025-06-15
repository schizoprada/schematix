# ~/schematix/tests/test_conditional_fields.py
"""Tests for conditional fields and dependency resolution."""
import pytest
from schematix import Schema, Field


def test_basic_conditional_field():
    """Test basic conditional field with value condition."""

    class TestSchema(Schema):
        gender = Field(source='gender', transient=True)
        category = Field(source='category', transient=True)

        category_id = Field(
            conditional=True,
            dependencies=['gender', 'category'],
            conditions={
                'value': lambda gender, category: f"{gender}_{category}_001"
            }
        )

    data = {'gender': 'men', 'category': 'shoes'}
    result = TestSchema().transform(data)

    assert result['category_id'] == 'men_shoes_001'
    assert 'gender' not in result  # transient
    assert 'category' not in result  # transient


def test_conditional_required():
    """Test conditional required field."""

    class TestSchema(Schema):
        brand = Field(source='brand', transient=True)
        category = Field(source='category', transient=True)

        keyword = Field(
            source='keyword',
            conditional=True,
            dependencies=['brand', 'category'],
            conditions={
                'required': lambda brand, category: not brand or not category
            }
        )

    # Should be required when brand/category missing
    data1 = {'brand': '', 'category': 'shoes', 'keyword': 'test'}
    result1 = TestSchema().transform(data1)
    assert result1['keyword'] == 'test'

    # Should fail when required and missing
    data2 = {'brand': '', 'category': 'shoes'}  # no keyword
    with pytest.raises(ValueError, match="required field"):
        TestSchema().transform(data2)


def test_dependency_resolution_order():
    """Test that fields are executed in correct dependency order."""

    executed_order = []

    def track_execution(name):
        def tracker(*args):
            executed_order.append(name)
            return f"{name}_result"
        return tracker

    class TestSchema(Schema):
        # This should execute last (depends on b and c)
        a = Field(
            conditional=True,
            dependencies=['b', 'c'],
            conditions={'value': track_execution('a')}
        )

        # This should execute second (depends on d)
        b = Field(
            conditional=True,
            dependencies=['d'],
            conditions={'value': track_execution('b')}
        )

        # This should execute third (depends on d)
        c = Field(
            conditional=True,
            dependencies=['d'],
            conditions={'value': track_execution('c')}
        )

        # This should execute first (no dependencies)
        d = Field(source='input', transform=track_execution('d'))

    TestSchema().transform({'input': 'test'})

    # d should be first, then b and c (order doesn't matter), then a
    assert executed_order[0] == 'd'
    assert executed_order[-1] == 'a'
    assert 'b' in executed_order[1:3]
    assert 'c' in executed_order[1:3]
