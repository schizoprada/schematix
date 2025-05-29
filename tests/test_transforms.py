# ~/schematix/tests/test_transforms.py
"""
Tests for the core transform system: BaseTransform, composition, operators.
"""
import pytest
from schematix.core.bases.transform import (
    BaseTransform, Transform, PipelineTransform,
    FallbackTransform, ParallelTransform
)
from schematix.core.transform import (
    transform, pipeline, fallback, parallel,
    multifield, conditional
)


class TestBaseTransform:
    """Test BaseTransform abstract base class."""

    def test_concrete_transform_creation(self):
        """Test creating a concrete Transform instance."""
        def double(x):
            return x * 2

        t = Transform(func=double, name="double")
        assert t.name == "double"
        assert t.apply(5) == 10
        assert t(5) == 10  # callable interface

    def test_transform_validation(self):
        """Test transform validation method."""
        def identity(x):
            return x

        class ValidatingTransform(Transform):
            def validate(self, value):
                if value < 0:
                    raise ValueError("Must be non-negative")
                return value

        t = ValidatingTransform(func=identity)
        assert t.apply(5) == 5

        with pytest.raises(ValueError, match="Must be non-negative"):
            t.apply(-1)

    def test_transform_auto_naming(self):
        """Test automatic naming from function name."""
        def my_transform(x):
            return x

        t = Transform(func=my_transform)
        assert t.name == "my_transform"


class TestTransformComposition:
    """Test transform composition and operators."""

    def test_pipeline_operator(self):
        """Test >> operator for pipeline composition."""
        t1 = Transform(func=lambda x: x * 2, name="double")
        t2 = Transform(func=lambda x: x + 1, name="plus_one")

        pipeline_t = t1 >> t2
        assert isinstance(pipeline_t, PipelineTransform)
        assert pipeline_t.apply(5) == 11  # (5 * 2) + 1

    def test_fallback_operator(self):
        """Test | operator for fallback composition."""
        def fail_transform(x):
            if x == "fail":
                raise ValueError("Failed")
            return x.upper()

        def backup_transform(x):
            return "BACKUP"

        t1 = Transform(func=fail_transform, name="primary")
        t2 = Transform(func=backup_transform, name="backup")

        fallback_t = t1 | t2
        assert isinstance(fallback_t, FallbackTransform)
        assert fallback_t.apply("hello") == "HELLO"  # primary succeeds
        assert fallback_t.apply("fail") == "BACKUP"  # fallback used

    def test_parallel_operator(self):
        """Test & operator for parallel composition."""
        t1 = Transform(func=lambda x: x * 2, name="double")
        t2 = Transform(func=lambda x: x + 1, name="plus_one")

        parallel_t = t1 & t2
        assert isinstance(parallel_t, ParallelTransform)
        result = parallel_t.apply(5)
        assert result == [10, 6]  # [5*2, 5+1]

    def test_method_chaining(self):
        """Test method chaining equivalents of operators."""
        t1 = Transform(func=lambda x: x * 2, name="double")
        t2 = Transform(func=lambda x: x + 1, name="plus_one")

        # Test then() method
        pipeline_t = t1.then(t2)
        assert isinstance(pipeline_t, PipelineTransform)
        assert pipeline_t.apply(5) == 11

        # Test fallback() method
        fallback_t = t1.fallback(t2)
        assert isinstance(fallback_t, FallbackTransform)

        # Test parallel() method
        parallel_t = t1.parallel(t2)
        assert isinstance(parallel_t, ParallelTransform)


class TestPipelineTransform:
    """Test PipelineTransform composition."""

    def test_pipeline_creation(self):
        """Test creating pipeline transforms."""
        t1 = Transform(func=lambda x: x * 2)
        t2 = Transform(func=lambda x: x + 1)
        t3 = Transform(func=lambda x: x ** 2)

        p = PipelineTransform([t1, t2, t3])
        # ((5 * 2) + 1) ** 2 = 11 ** 2 = 121
        assert p.apply(5) == 121

    def test_pipeline_extension(self):
        """Test extending pipelines with more transforms."""
        t1 = Transform(func=lambda x: x * 2)
        t2 = Transform(func=lambda x: x + 1)
        t3 = Transform(func=lambda x: x ** 2)

        p1 = PipelineTransform([t1, t2])
        p2 = p1 >> t3

        assert p2.apply(5) == 121  # ((5 * 2) + 1) ** 2

    def test_pipeline_add_method(self):
        """Test add() method for pipelines."""
        t1 = Transform(func=lambda x: x * 2)
        t2 = Transform(func=lambda x: x + 1)

        p1 = PipelineTransform([t1])
        p2 = p1.add(t2)

        assert p2.apply(5) == 11  # (5 * 2) + 1

    def test_empty_pipeline_error(self):
        """Test that empty pipeline raises error."""
        with pytest.raises(ValueError, match="requires at least one transform"):
            PipelineTransform([])


class TestFallbackTransform:
    """Test FallbackTransform composition."""

    def test_fallback_success_primary(self):
        """Test fallback when primary succeeds."""
        primary = Transform(func=lambda x: x.upper())
        backup = Transform(func=lambda x: "BACKUP")

        f = FallbackTransform(primary, backup)
        assert f.apply("hello") == "HELLO"

    def test_fallback_uses_backup(self):
        """Test fallback when primary fails."""
        def failing_transform(x):
            raise ValueError("Primary failed")

        primary = Transform(func=failing_transform)
        backup = Transform(func=lambda x: "BACKUP")

        f = FallbackTransform(primary, backup)
        assert f.apply("anything") == "BACKUP"

    def test_fallback_with_context(self):
        """Test fallback with context-aware transforms."""
        def context_transform(value, context):
            return context.get("key", "DEFAULT")

        primary = Transform(func=lambda x: x / 0)  # Will fail
        backup = Transform(func=context_transform, contextaware=True)

        f = FallbackTransform(primary, backup)
        result = f.apply(10, {"key": "FROM_CONTEXT"})
        assert result == "FROM_CONTEXT"


class TestParallelTransform:
    """Test ParallelTransform composition."""

    def test_parallel_default_combiner(self):
        """Test parallel with default list combiner."""
        t1 = Transform(func=lambda x: x * 2)
        t2 = Transform(func=lambda x: x + 1)
        t3 = Transform(func=lambda x: x ** 2)

        p = ParallelTransform([t1, t2, t3])
        result = p.apply(5)
        assert result == [10, 6, 25]  # [5*2, 5+1, 5**2]

    def test_parallel_custom_combiner(self):
        """Test parallel with custom combiner function."""
        t1 = Transform(func=lambda x: x * 2)
        t2 = Transform(func=lambda x: x + 1)

        # Combiner that sums results
        p = ParallelTransform([t1, t2], combiner=sum)
        result = p.apply(5)
        assert result == 16  # (5*2) + (5+1) = 10 + 6

    def test_parallel_extension(self):
        """Test extending parallel transforms."""
        t1 = Transform(func=lambda x: x * 2)
        t2 = Transform(func=lambda x: x + 1)
        t3 = Transform(func=lambda x: x ** 2)

        p1 = ParallelTransform([t1, t2])
        p2 = p1 & t3

        result = p2.apply(5)
        assert result == [10, 6, 25]

    def test_empty_parallel_error(self):
        """Test that empty parallel raises error."""
        with pytest.raises(ValueError, match="requires at least one transform"):
            ParallelTransform([])


class TestTransformDecorator:
    """Test @transform decorator and factory functions."""

    def test_transform_decorator_simple(self):
        """Test @transform as simple decorator."""
        @transform
        def double(x):
            return x * 2

        assert isinstance(double, Transform)
        assert double.apply(5) == 10
        assert double.name == "double"

    def test_transform_decorator_with_args(self):
        """Test @transform with arguments."""
        @transform(name="custom_name", description="A custom transform")
        def triple(x):
            return x * 3

        assert isinstance(triple, Transform)
        assert triple.name == "custom_name"
        assert triple.description == "A custom transform"
        assert triple.apply(5) == 15

    def test_transform_factory_function(self):
        """Test transform() as factory function."""
        def quadruple(x):
            return x * 4

        t = transform(quadruple, name="quad")
        assert isinstance(t, Transform)
        assert t.name == "quad"
        assert t.apply(5) == 20

    def test_context_aware_transform(self):
        """Test context-aware transforms."""
        @transform(contextaware=True)
        def context_transform(value, context):
            multiplier = context.get("multiplier", 1)
            return value * multiplier

        result = context_transform.apply(5, {"multiplier": 3})
        assert result == 15

        # Test without context
        result = context_transform.apply(5)
        assert result == 5  # Uses default multiplier=1


class TestFactoryFunctions:
    """Test utility factory functions."""

    def test_pipeline_factory(self):
        """Test pipeline() factory function."""
        t1 = Transform(func=lambda x: x * 2)
        t2 = Transform(func=lambda x: x + 1)

        p = pipeline(t1, t2)
        assert isinstance(p, PipelineTransform)
        assert p.apply(5) == 11

    def test_fallback_factory(self):
        """Test fallback() factory function."""
        t1 = Transform(func=lambda x: x / 0)  # Will fail
        t2 = Transform(func=lambda x: "BACKUP")

        f = fallback(t1, t2)
        assert isinstance(f, FallbackTransform)
        assert f.apply(5) == "BACKUP"

    def test_parallel_factory(self):
        """Test parallel() factory function."""
        t1 = Transform(func=lambda x: x * 2)
        t2 = Transform(func=lambda x: x + 1)

        p = parallel(t1, t2)
        assert isinstance(p, ParallelTransform)
        assert p.apply(5) == [10, 6]

    def test_parallel_factory_with_combiner(self):
        """Test parallel() factory with custom combiner."""
        t1 = Transform(func=lambda x: x * 2)
        t2 = Transform(func=lambda x: x + 1)

        p = parallel(t1, t2, combiner=sum)
        assert p.apply(5) == 16  # (5*2) + (5+1)


class TestContextAwareTransforms:
    """Test context-aware transform utilities."""

    def test_multifield_transform(self):
        """Test multifield() utility function."""
        def combine_name(first, last):
            return f"{first} {last}"

        t = multifield(['first_name', 'last_name'], combine_name)
        context = {'first_name': 'John', 'last_name': 'Doe'}

        result = t.apply("ignored", context)
        assert result == "John Doe"

    def test_conditional_transform(self):
        """Test conditional() utility function."""
        def is_positive(x):
            return x > 0

        positive_t = Transform(func=lambda x: f"positive: {x}")
        negative_t = Transform(func=lambda x: f"negative: {x}")

        t = conditional(is_positive, positive_t, negative_t)

        assert t.apply(5) == "positive: 5"
        assert t.apply(-3) == "negative: -3"

    def test_conditional_without_false_transform(self):
        """Test conditional transform without false branch."""
        def is_even(x):
            return x % 2 == 0

        even_t = Transform(func=lambda x: f"even: {x}")

        t = conditional(is_even, even_t)

        assert t.apply(4) == "even: 4"
        assert t.apply(5) == 5  # Returns original value


class TestErrorHandling:
    """Test error handling in transforms."""

    def test_transform_validation_error(self):
        """Test validation errors in transforms."""
        def validate_positive(x):
            if x <= 0:
                raise ValueError("Must be positive")
            return x

        class ValidatingTransform(Transform):
            def validate(self, value):
                return validate_positive(value)

        t = ValidatingTransform(func=lambda x: x * 2)

        assert t.apply(5) == 10

        with pytest.raises(ValueError, match="Must be positive"):
            t.apply(-1)

    def test_pipeline_error_propagation(self):
        """Test error propagation in pipelines."""
        def fail_on_zero(x):
            if x == 0:
                raise ValueError("Cannot be zero")
            return x * 2

        t1 = Transform(func=lambda x: x - 5)  # 5 - 5 = 0
        t2 = Transform(func=fail_on_zero)

        p = t1 >> t2

        with pytest.raises(ValueError, match="Cannot be zero"):
            p.apply(5)

    def test_fallback_error_handling(self):
        """Test that fallback handles errors properly."""
        def always_fail(x):
            raise RuntimeError("Always fails")

        def always_succeed(x):
            return "SUCCESS"

        primary = Transform(func=always_fail)
        backup = Transform(func=always_succeed)

        f = primary | backup
        assert f.apply("anything") == "SUCCESS"


class TestTransformRepresentation:
    """Test string representations of transforms."""

    def test_transform_repr(self):
        """Test Transform __repr__ method."""
        t = Transform(func=lambda x: x, name="test_transform")
        repr_str = repr(t)
        assert "Transform" in repr_str
        assert "test_transform" in repr_str

    def test_pipeline_repr(self):
        """Test PipelineTransform __repr__ method."""
        t1 = Transform(func=lambda x: x, name="first")
        t2 = Transform(func=lambda x: x, name="second")

        p = t1 >> t2
        repr_str = repr(p)
        assert "PipelineTransform" in repr_str
        assert "first >> second" in repr_str

    def test_fallback_repr(self):
        """Test FallbackTransform __repr__ method."""
        t1 = Transform(func=lambda x: x, name="primary")
        t2 = Transform(func=lambda x: x, name="backup")

        f = t1 | t2
        repr_str = repr(f)
        assert "FallbackTransform" in repr_str
        assert "primary" in repr_str and "backup" in repr_str

    def test_parallel_repr(self):
        """Test ParallelTransform __repr__ method."""
        t1 = Transform(func=lambda x: x, name="first")
        t2 = Transform(func=lambda x: x, name="second")

        p = t1 & t2
        repr_str = repr(p)
        assert "ParallelTransform" in repr_str
        assert "first & second" in repr_str


class TestComplexComposition:
    """Test complex transform compositions."""

    def test_nested_composition(self):
        """Test deeply nested transform compositions."""
        # Create a complex transform: (double >> add_one) | (triple & square)
        double = Transform(func=lambda x: x * 2, name="double")
        add_one = Transform(func=lambda x: x + 1, name="add_one")
        triple = Transform(func=lambda x: x * 3, name="triple")
        square = Transform(func=lambda x: x ** 2, name="square")

        complex_t = (double >> add_one) | (triple & square)

        # Should use the pipeline (double >> add_one) since it won't fail
        result = complex_t.apply(5)
        assert result == 11  # (5 * 2) + 1

    def test_mixed_operators(self):
        """Test mixing different operators in one expression."""
        t1 = Transform(func=lambda x: x * 2)
        t2 = Transform(func=lambda x: x + 1)
        t3 = Transform(func=lambda x: x ** 2)
        t4 = Transform(func=lambda x: x - 3)

        # Complex: (t1 >> t2) & (t3 >> t4)
        complex_t = (t1 >> t2) & (t3 >> t4)

        result = complex_t.apply(5)
        # Left side: (5 * 2) + 1 = 11
        # Right side: (5 ** 2) - 3 = 22
        assert result == [11, 22]

    def test_context_in_complex_composition(self):
        """Test context passing through complex compositions."""
        def context_multiply(value, context):
            return value * context.get("factor", 1)

        def context_add(value, context):
            return value + context.get("offset", 0)

        t1 = Transform(func=context_multiply, contextaware=True)
        t2 = Transform(func=context_add, contextaware=True)

        pipeline_t = t1 >> t2
        context = {"factor": 3, "offset": 10}

        result = pipeline_t.apply(5, context)
        assert result == 25  # (5 * 3) + 10


if __name__ == "__main__":
    pytest.main([__file__])
