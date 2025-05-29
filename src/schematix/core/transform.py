# ~/schematix/src/schematix/core/transform.py
"""
Utility functions for creating transforms
"""
from __future__ import annotations
import typing as t

from schematix.core.bases.transform import (
    BaseTransform,
    Transform,
    PipelineTransform,
    FallbackTransform,
    ParallelTransform
)

def transform(
    func: t.Optional[t.Callable] = None,
    *,
    name: t.Optional[str] = None,
    description: t.Optional[str] = None,
    contextaware: bool = False
) -> t.Union[Transform, t.Callable[[t.Callable], Transform]]:
    """
    Decorator/factory for creating Transform instances.

    Can be used as:
    1. Decorator: @transform
    2. Decorator with args: @transform(name="mytransform")
    3. Factory: transform(myfunction)

    Args:
        func: Function to wrap (when used as factory)
        name: Optional name for the transform
        description: Optional description
        contextaware: Whether function expects (value, context) arguments

    Returns:
        Transform instance or decorator function
    """
    def decorator(f: t.Callable) -> Transform:
        return Transform(
            func=f,
            name=name,
            description=description,
            contextaware=contextaware
        )

    if func is None:
        # Used as @transform() or @transform(name="...")
        return decorator
    else:
        # Used as @transform or transform(func)
        return decorator(func)


def pipeline(*transforms: BaseTransform) -> PipelineTransform:
    """
    Create a pipeline transform from multiple transforms.

    Args:
        *transforms: Transforms to chain together

    Returns:
        PipelineTransform instance
    """
    return PipelineTransform(list(transforms))


def fallback(primary: BaseTransform, backup: BaseTransform) -> FallbackTransform:
    """
    Create a fallback transform.

    Args:
        primary: Primary transform to try
        backup: Backup transform if primary fails

    Returns:
        FallbackTransform instance
    """
    return FallbackTransform(primary, backup)


def parallel(*transforms: BaseTransform, combiner: t.Optional[t.Callable] = None) -> ParallelTransform:
    """
    Create a parallel transform from multiple transforms.

    Args:
        *transforms: Transforms to run in parallel
        combiner: Optional function to combine results

    Returns:
        ParallelTransform instance
    """
    return ParallelTransform(list(transforms), combiner=combiner)


# Context-aware transform utilities

def multifield(fields: t.List[str], func: t.Callable) -> Transform:
    """
    Create a context-aware transform that accesses multiple fields from source data.

    Args:
        fields: List of field names to extract from context
        func: Function that takes the extracted field values as arguments

    Returns:
        Context-aware Transform instance
    """
    def contextfunc(value: t.Any, context: t.Dict[str, t.Any]) -> t.Any:
        fieldvalues = [context.get(field) for field in fields]
        return func(*fieldvalues)

    return Transform(
        func=contextfunc,
        contextaware=True,
        name=f"multifield({', '.join(fields)})"
    )


def conditional(condition: t.Callable[[t.Any], bool],
                truetransform: BaseTransform,
                falsetransform: t.Optional[BaseTransform] = None) -> Transform:
    """
    Create a conditional transform that applies different transforms based on a condition.

    Args:
        condition: Function that returns True/False based on input value
        truetransform: Transform to apply if condition is True
        falsetransform: Transform to apply if condition is False (optional)

    Returns:
        Transform instance with conditional logic
    """
    def conditionalfunc(value: t.Any, context: t.Optional[t.Dict[str, t.Any]] = None) -> t.Any:
        if condition(value):
            return truetransform.apply(value, context)
        elif falsetransform:
            return falsetransform.apply(value, context)
        else:
            return value

    return Transform(
        func=conditionalfunc,
        contextaware=True,
        name=f"conditional({truetransform.name}, {falsetransform.name if falsetransform else 'identity'})"
    )
