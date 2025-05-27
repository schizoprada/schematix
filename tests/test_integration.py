# ~/schematix/tests/test_integration.py
"""Integration tests for complete workflows."""
import pytest
from dataclasses import dataclass
from typing import List, Dict, Any
from schematix import Schema, Field, SourceField, TargetField


@dataclass
class User:
    """Sample user dataclass for integration testing."""
    id: int
    email: str
    name: str
    profile: Dict[str, Any] = None


@dataclass
class Company:
    """Sample company dataclass."""
    id: int
    name: str
    employees: List[User] = None


class TestCompleteWorkflows:
    """Test complete data transformation workflows."""

    def test_simple_api_transformation(self):
        """Test transforming API response to internal format."""
        # Simulate API response
        api_data = {
            'user_id': 12345,
            'email_address': 'john.doe@company.com',
            'first_name': 'John',
            'last_name': 'Doe',
            'account_type': 'premium',
            'last_login': '2025-01-15T10:30:00Z'
        }

        # Define transformation schema
        class UserSchema(Schema):
            id = Field(source='user_id')
            email = Field(source='email_address', required=True)
            name = Field(source='first_name') + Field(source='last_name')
            account = Field(source='account_type', transform=str.upper)
            lastlogin = Field(source='last_login')

        # Transform data
        schema = UserSchema()
        result = schema.transform(api_data)

        assert result['id'] == 12345
        assert result['email'] == 'john.doe@company.com'
        assert result['name'] == 'John Doe'  # Accumulated
        assert result['account'] == 'PREMIUM'  # Transformed
        assert result['lastlogin'] == '2025-01-15T10:30:00Z'

    def test_web_scraping_normalization(self):
        """Test normalizing web scraping data from multiple sources."""
        # Simulate data from different websites
        reddit_data = {
            'username': 'john_dev',
            'email_addr': 'john@reddit.com',
            'post_karma': 1500,
            'comment_karma': 800,
            'account_created': '2020-01-15'
        }

        twitter_data = {
            'handle': '@johndoe',
            'display_name': 'John Developer',
            'followers_count': 250,
            'tweets_count': 180,
            'member_since': '2019-05-20'
        }

        # Define base user schema
        class BaseUserSchema(Schema):
            username = Field()
            email = Field(required=True)
            displayname = Field()
            joindate = Field()

        # Bind to different sources
        reddit_bound = BaseUserSchema().bind({
            'username': 'username',
            'email': 'email_addr',
            'displayname': 'username',  # Use username as display name
            'joindate': 'account_created'
        })

        twitter_bound = BaseUserSchema().bind({
            'username': 'handle',
            'email': ('display_name', lambda name: f"{name.lower().replace(' ', '')}@twitter.com"),
            'displayname': 'display_name',
            'joindate': 'member_since'
        })

        # Transform both sources
        reddit_user = reddit_bound.transform(reddit_data)
        twitter_user = twitter_bound.transform(twitter_data)

        # Verify Reddit transformation
        assert reddit_user['username'] == 'john_dev'
        assert reddit_user['email'] == 'john@reddit.com'
        assert reddit_user['displayname'] == 'john_dev'
        assert reddit_user['joindate'] == '2020-01-15'

        # Verify Twitter transformation
        assert twitter_user['username'] == '@johndoe'
        assert twitter_user['email'] == 'johndeveloper@twitter.com'
        assert twitter_user['displayname'] == 'John Developer'
        assert twitter_user['joindate'] == '2019-05-20'

    def test_etl_pipeline_with_fallbacks(self):
        """Test ETL pipeline with fallback data sources."""
        # Simulate incomplete data sources
        primary_source = {
            'id': 123,
            'primary_email': 'user@primary.com',
            'full_name': 'John Smith'
        }

        backup_source = {
            'user_id': 123,
            'backup_email': 'user@backup.com',
            'first_name': 'John',
            'last_name': 'Smith',
            'phone': '555-0123'
        }

        # Schema with fallback logic
        class RobustUserSchema(Schema):
            id = Field(source='id') | Field(source='user_id')
            email = (Field(source='primary_email') |
                    Field(source='backup_email') |
                    Field(source='contact_email'))
            name = (Field(source='full_name') |
                   (Field(source='first_name') + Field(source='last_name')))
            phone = Field(source='phone', default='N/A')

        # Test with primary source (should use primary values)
        schema = RobustUserSchema()
        result = schema.transform(primary_source)

        assert result['id'] == 123
        assert result['email'] == 'user@primary.com'  # Primary email
        assert result['name'] == 'John Smith'  # Full name
        assert result['phone'] == 'N/A'  # Default

        # Test with backup source (should use fallback values)
        result = schema.transform(backup_source)

        assert result['id'] == 123  # From user_id fallback
        assert result['email'] == 'user@backup.com'  # Backup email
        assert result['name'] == 'John Smith'  # Accumulated from first + last
        assert result['phone'] == '555-0123'  # From backup source

    def test_nested_data_transformation(self):
        """Test transformation of deeply nested data structures."""
        # Simulate complex nested API response
        complex_data = {
            'company': {
                'info': {
                    'id': 999,
                    'legal_name': 'TechCorp Inc.',
                    'trade_name': 'TechCorp'
                },
                'contact': {
                    'headquarters': {
                        'address': '123 Tech Street',
                        'city': 'San Francisco',
                        'country': 'USA'
                    },
                    'communication': {
                        'main_email': 'info@techcorp.com',
                        'support_email': 'support@techcorp.com'
                    }
                }
            },
            'employees': [
                {
                    'personal': {'id': 1, 'name': 'Alice Johnson'},
                    'work': {'title': 'Engineer', 'department': 'R&D'}
                },
                {
                    'personal': {'id': 2, 'name': 'Bob Wilson'},
                    'work': {'title': 'Manager', 'department': 'Sales'}
                }
            ]
        }

        # Schema for nested company data
        class CompanySchema(Schema):
            id = Field(source='id') @ 'company.info'
            name = Field(source='trade_name') @ 'company.info'
            legalname = Field(source='legal_name') @ 'company.info'
            address = Field(source='address') @ 'company.contact.headquarters'
            city = Field(source='city') @ 'company.contact.headquarters'
            email = Field(source='main_email') @ 'company.contact.communication'

        # Transform company data
        schema = CompanySchema()
        result = schema.transform(complex_data)

        assert result['id'] == 999
        assert result['name'] == 'TechCorp'
        assert result['legalname'] == 'TechCorp Inc.'
        assert result['address'] == '123 Tech Street'
        assert result['city'] == 'San Francisco'
        assert result['email'] == 'info@techcorp.com'

    def test_schema_composition_and_reuse(self):
        """Test composing and reusing schema components."""
        # Base schemas for common patterns
        class TimestampSchema(Schema):
            created = Field(source='created_at', transform=lambda x: x[:10])  # Date only
            modified = Field(source='updated_at', transform=lambda x: x[:10])

        class ContactSchema(Schema):
            email = Field(source='email', required=True)
            phone = Field(source='phone_number', default='N/A')

        # Compose schemas
        UserSchema = Schema.Merge(TimestampSchema, ContactSchema)
        UserSchema = UserSchema.Copy(
            id=Field(source='user_id'),
            name=Field(source='full_name'),
            active=Field(source='is_active', default=True)
        )

        # Test data
        user_data = {
            'user_id': 456,
            'full_name': 'Jane Doe',
            'email': 'jane@example.com',
            'phone_number': '555-9876',
            'is_active': False,
            'created_at': '2025-01-01T10:00:00Z',
            'updated_at': '2025-01-15T15:30:00Z'
        }

        # Transform using composed schema
        schema = UserSchema()
        result = schema.transform(user_data)

        assert result['id'] == 456
        assert result['name'] == 'Jane Doe'
        assert result['email'] == 'jane@example.com'
        assert result['phone'] == '555-9876'
        assert result['active'] is False
        assert result['created'] == '2025-01-01'  # Transformed
        assert result['modified'] == '2025-01-15'  # Transformed

    def test_dataclass_target_conversion(self):
        """Test converting to dataclass target types."""
        # Source data
        api_response = {
            'user_id': 789,
            'email_address': 'test@dataclass.com',
            'display_name': 'Test User',
            'user_profile': {
                'bio': 'I am a test user',
                'location': 'Test City'
            }
        }

        # Schema for dataclass conversion
        class UserSchema(Schema):
            id = Field(source='user_id')
            email = Field(source='email_address')
            name = Field(source='display_name')
            profile = Field(source='user_profile')

        # Transform to dataclass
        schema = UserSchema()
        user_obj = schema.transform(api_response, typetarget=User)

        assert isinstance(user_obj, User)
        assert user_obj.id == 789
        assert user_obj.email == 'test@dataclass.com'
        assert user_obj.name == 'Test User'
        assert user_obj.profile['bio'] == 'I am a test user'

    def test_batch_processing(self):
        """Test batch processing of multiple data items."""
        # Batch of user records
        user_batch = [
            {'uid': 1, 'email': 'user1@test.com', 'fname': 'Alice', 'lname': 'Smith'},
            {'uid': 2, 'email': 'user2@test.com', 'fname': 'Bob', 'lname': 'Jones'},
            {'uid': 3, 'email': 'user3@test.com', 'fname': 'Carol', 'lname': 'Brown'},
        ]

        # Schema for batch processing
        class BatchUserSchema(Schema):
            id = Field(source='uid')
            email = Field(source='email')
            fullname = Field(source='fname') + Field(source='lname')

        # Process batch
        schema = BatchUserSchema()
        results = schema.transformplural(user_batch)

        assert len(results) == 3
        assert results[0]['fullname'] == 'Alice Smith'
        assert results[1]['fullname'] == 'Bob Jones'
        assert results[2]['fullname'] == 'Carol Brown'

        # All should have required structure
        for result in results:
            assert 'id' in result
            assert 'email' in result
            assert 'fullname' in result

    def test_error_handling_and_recovery(self):
        """Test error handling and recovery strategies."""
        # Data with some problematic records
        mixed_data = [
            {'id': 1, 'email': 'good@example.com', 'name': 'Good User'},
            {'id': 2, 'name': 'Missing Email User'},  # Missing required email
            {'id': 3, 'email': 'another@example.com', 'name': 'Another Good User'},
        ]

        # Schema with required field
        class StrictSchema(Schema):
            id = Field(source='id', required=True)
            email = Field(source='email', required=True)
            name = Field(source='name', default='Unknown')

        schema = StrictSchema()

        # Test individual validation
        errors = schema.validate(mixed_data[1])  # Missing email
        assert 'email' in errors
        assert 'id' not in errors
        assert 'name' not in errors

        # Test batch processing with error handling
        successful_results = []
        failed_items = []

        for i, item in enumerate(mixed_data):
            try:
                result = schema.transform(item)
                successful_results.append(result)
            except ValueError as e:
                failed_items.append((i, item, str(e)))

        assert len(successful_results) == 2  # Two good records
        assert len(failed_items) == 1  # One failed record
        assert failed_items[0][0] == 1  # Index of failed item
