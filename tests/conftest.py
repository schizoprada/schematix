# ~/schematix/tests/conftest.py
"""Pytest configuration and shared fixtures."""
import pytest
from dataclasses import dataclass
from typing import Dict, Any


@pytest.fixture
def sample_dict_data():
    """Sample dictionary data for testing."""
    return {
        'user_id': 123,
        'email_address': 'test@example.com',
        'first_name': 'John',
        'last_name': 'Doe',
        'profile': {
            'bio': 'Software developer',
            'location': 'New York'
        },
        'tags': ['python', 'testing']
    }


@pytest.fixture
def sample_nested_data():
    """Sample nested data structure."""
    return {
        'user': {
            'info': {
                'id': 456,
                'email': 'nested@example.com'
            },
            'profile': {
                'name': 'Jane Smith',
                'age': 30
            }
        },
        'metadata': {
            'created': '2025-01-01',
            'version': 2
        }
    }


@dataclass
class User:
    """Sample dataclass for testing target type conversion."""
    id: int
    email: str
    name: str = "Unknown"


@pytest.fixture
def user_dataclass():
    """User dataclass for testing."""
    return User


@pytest.fixture
def sample_list_data():
    """Sample list data for testing batch operations."""
    return [
        {'id': 1, 'name': 'Alice', 'email': 'alice@test.com'},
        {'id': 2, 'name': 'Bob', 'email': 'bob@test.com'},
        {'id': 3, 'name': 'Charlie', 'email': 'charlie@test.com'}
    ]
