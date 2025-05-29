# Schematix

[![PyPI version](https://badge.fury.io/py/schematix.svg)](https://badge.fury.io/py/schematix)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-173%20passed-green.svg)](https://github.com/schizoprada/schematix)

A Python library for **declarative data mapping and transformation** that emphasizes reusability and composability. Define your target schemas once and bind them to different data sources with intuitive operator overloading.

## ✨ Key Features

- 🎯 **Reusable Schema Definitions** - Define once, use across multiple data sources
- 🔧 **Intuitive Operators** - `>>`, `|`, `&`, `@`, `+` for elegant data transformations
- 🏗️ **Type Agnostic** - Works with dicts, dataclasses, Pydantic models, any attributable objects
- 🧩 **Composable Architecture** - Mix and match field types and transformations
- 🛡️ **Comprehensive Validation** - Built-in error handling and validation
- 📊 **Batch Processing** - Transform lists of data efficiently
- 🎨 **Clean API** - Readable, maintainable transformation code

## 🚀 Quick Start

### Installation

```bash
pip install schematix
```

### Basic Usage

```python
from schematix import Schema, Field

# Define your target schema
class UserSchema(Schema):
    id = Field(source='user_id')
    email = Field(source='email_address', required=True)
    name = Field(source='first_name') + Field(source='last_name')

# Transform data
data = {
    'user_id': 123,
    'email_address': 'john@example.com',
    'first_name': 'John',
    'last_name': 'Doe'
}

user = UserSchema().transform(data)
# Result: {'id': 123, 'email': 'john@example.com', 'name': 'John Doe'}
```

## 🎭 Operator Magic

Schematix provides intuitive operators for common transformation patterns:

### Pipeline (`>>`) - Connect source to target
```python
source_field >> target_field  # Extract from source, assign to target
```

### Fallback (`|`) - Try alternatives
```python
Field(source='email') | Field(source='contact_email')  # Try email, fallback to contact_email
```

### Combine (`&`) - Merge multiple fields
```python
user_fields = Field(source='name') & Field(source='email') & Field(source='age')
```

### Nested (`@`) - Apply to nested data
```python
Field(source='name') @ 'user.profile'  # Extract name from data.user.profile.name
```

### Accumulate (`+`) - Smart value combination
```python
Field(source='first') + Field(source='last')  # "John" + "Doe" = "John Doe"
Field(source='price') + Field(source='tax')   # 100 + 15 = 115
```

## 🏗️ Advanced Usage

### Schema Binding for Multiple Data Sources

```python
class UserSchema(Schema):
    id = Field()
    email = Field(required=True)
    name = Field()

# Bind to different data sources
reddit_users = UserSchema().bind({
    'id': 'user_id',
    'email': 'email_addr',
    'name': ('username', str.title)  # Extract username and titlecase it
})

api_users = UserSchema().bind({
    'id': 'uid',
    'email': 'contact.email',
    'name': lambda data: f"{data['first']} {data['last']}"
})

# Transform from different sources
reddit_user = reddit_users.transform(reddit_data)
api_user = api_users.transform(api_data)
```

### Enhanced Field Types

```python
from schematix import SourceField, TargetField

# SourceField with fallbacks and conditions
email = SourceField(
    source='primary_email',
    fallbacks=['secondary_email', 'contact.email'],
    condition=lambda data: data.get('active', True)
)

# TargetField with formatting and multiple targets
name = TargetField(
    target='display_name',
    formatter=str.title,
    additionaltargets=['full_name', 'user_name']
)
```

### Target Type Conversion

```python
from dataclasses import dataclass

@dataclass
class User:
    id: int
    email: str
    name: str

# Convert directly to dataclass
user_obj = UserSchema().transform(data, typetarget=User)
print(type(user_obj))  # <class '__main__.User'>
```

### Schema Composition

```python
# Merge schemas
BaseUserSchema = Schema.merge(ContactSchema, ProfileSchema)

# Copy with modifications
ExtendedUserSchema = BaseUserSchema.copy(
    created_at=Field(source='registration_date'),
    is_premium=Field(source='account_type', transform=lambda x: x == 'premium')
)

# Create subsets
PublicUserSchema = ExtendedUserSchema.subset('id', 'name', 'email')
```

## 🔧 Real-World Examples

### API Response Transformation
```python
# GitHub API to internal user format
class GitHubUserSchema(Schema):
    id = Field(source='id')
    username = Field(source='login')
    name = Field(source='name') | Field(source='login')  # Fallback to login
    email = Field(source='email')
    repos = Field(source='public_repos', default=0)
    profile = Field(source='html_url')

github_user = GitHubUserSchema().transform(github_api_response)
```

### Web Scraping Normalization
```python
# Normalize product data from different e-commerce sites
class ProductSchema(Schema):
    name = Field()
    price = Field(transform=lambda x: float(x.replace('$', '')))
    rating = Field(default=0.0)

# Site-specific bindings
amazon_products = ProductSchema().bind({
    'name': 'title',
    'price': 'price.amount',
    'rating': 'averageRating'
})

ebay_products = ProductSchema().bind({
    'name': 'itemTitle',
    'price': 'currentPrice.value',
    'rating': ('feedbackScore', lambda x: x / 100)  # Convert to 0-5 scale
})
```

### ETL Pipeline
```python
# Database to data warehouse transformation
class AnalyticsUserSchema(Schema):
    user_id = Field(source='id', required=True)
    signup_date = Field(source='created_at', transform=parse_date)
    lifetime_value = Field(source='orders', transform=calculate_ltv)
    segment = (
        Field(source='total_spent', transform=lambda x: 'premium' if x > 1000 else 'standard') |
        Field(default='unknown')
    )

# Batch processing
users = AnalyticsUserSchema().transformplural(user_records)
```

## 📊 Error Handling & Validation

```python
# Comprehensive validation
errors = UserSchema().validate(data)
if errors:
    print(f"Validation errors: {errors}")

# Field-level error handling with fallbacks
safe_extraction = (
    Field(source='primary_source', required=True) |
    Field(source='backup_source') |
    Field(default='fallback_value')
)
```

### Decorator Style (Alternative Syntax)

```python
import schematix as sx

# Define fields using decorators
@sx.field
class UserID:
    source = 'user_id'
    required = True

@sx.field.accumulated
class FullName:
    fields = [
        sx.Field(source='first_name'),
        sx.Field(source='last_name')
    ]

# Define schema using decorator
@sx.schema
class UserSchema:
    id = UserID
    email = sx.Field(source='email_address', required=True)
    name = FullName

# Same transformation capability
user = UserSchema().transform(data)
```

## 🔄 Transform System

Schematix now includes a powerful transform system for data processing pipelines:

### Intuitive Transform Composition
```python
from schematix.transforms import text, numbers, common

# Pipeline composition with >> operator
name_cleaner = text.strip >> text.title >> text.normalizewhitespace

# Fallback logic with | operator
safe_number = numbers.to.int | numbers.constant(0)

# Parallel processing with & operator
multi_format = numbers.format.currency & numbers.format.percent

# Real-world cleaning pipeline
email_processor = common.clean.email >> common.validate.email
```

### Comprehensive Transform Library
- **Text**: String manipulation, regex, encoding, formatting (35+ transforms)
- **Numbers**: Math operations, formatting, validation (30+ transforms)
- **Dates**: Parsing, formatting, timezone handling (40+ transforms)
- **Collections**: List/dict operations, filtering, aggregation (25+ transforms)
- **Validation**: Format checking, cleaning, requirements (20+ transforms)
- **Common**: Pre-built patterns for real-world use cases (25+ transforms)

### Advanced Features
```python
# Context-aware transforms
full_name = transforms.multifield(['first_name', 'last_name'],
                                 lambda f, l: f"{f} {l}")

# Conditional transforms
format_price = transforms.conditional(
    lambda x: x > 100,
    numbers.format.currency(),
    numbers.format.commas()
)

# Safe operations with fallbacks
safe_clean = common.clean.safe.email(default="unknown@example.com")
```

### Transform + Schema Integration
```python
# Use transforms in field definitions
class UserSchema(Schema):
    name = Field(source='full_name', transform=text.strip >> text.title)
    email = Field(source='email_addr', transform=common.clean.email)
    price = Field(source='amount', transform=numbers.to.float >> numbers.format.currency)

# Or use the short aliases
import schematix as sx

class ProductSchema(sx.Schema):
    title = sx.Field(source='name', transform=sx.x.txt.title)
    cost = sx.Field(source='price', transform=sx.x.num.format.currency())
```


## 🛠️ Development Status

Schematix is actively developed and production-ready:

- ✅ **173 passing tests** with comprehensive coverage
- ✅ **Type hints** throughout for excellent IDE support
- ✅ **Detailed documentation** and examples
- ✅ **Semantic versioning** and changelog
- ✅ **MIT License** - use freely in commercial projects

## 📚 Documentation

- [Getting Started Guide](docs/getting-started.md)
- [API Reference](docs/api-reference.md)
- [Field Types](docs/field-types.md)
- [Schema Composition](docs/schema-composition.md)
- [Advanced Patterns](docs/advanced-patterns.md)
- [Migration Guide](docs/migration.md)

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🔗 Links

- **PyPI**: https://pypi.org/project/schematix/
- **Repository**: https://github.com/schizoprada/schematix
- **Documentation**: https://schematix.readthedocs.io
- **Issues**: https://github.com/schizoprada/schematix/issues
