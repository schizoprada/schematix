# ~/schematix/src/schematix/__init__.py
"""
Schematix: A Python library for declarative data mapping and transformation.

Schematix provides an object-oriented approach to data transformation that emphasizes
reusability and composability. Define target schemas once and bind them to different
data sources with source-specific extraction and transformation logic.
"""

__version__ = "0.2.0"
__author__ = "Joel Yisrael"
__email__ = "schizoprada@gmail.com"
__license__ = "MIT"
__url__ = "https://github.com/schizoprada/schematix"

# Version info tuple for programmatic access
VERSION = tuple(map(int, __version__.split('.')))

# Core imports will be added as we build the library
# from .fields import Field
# from .schemas import Schema
# from .binding import Binding
# from .transformers import Transform

__all__ = [
    "__version__",
    "__author__",
    "__email__",
    "__license__",
    "__url__",
    "VERSION",
    # Core classes will be added here
    # "Field",
    # "Schema",
    # "Binding",
    # "Transform",
]
