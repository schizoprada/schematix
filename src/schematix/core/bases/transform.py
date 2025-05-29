# ~/schematix/src/schematix/core/bases/transform.py
"""
Transform base class & composition system.
"""
from __future__ import annotations
import abc, typing as t, functools as fn

class BaseTransform(abc.ABC):
    """
    Abstract base class for all transform types.

    Provides the core interface and operator overloading for transform composition.
    Follows the same patterns as BaseField with __constructs__ and operator overloading.
    """
    __constructs__: set[str] = {'name', 'description'}

    def __init__(
        self,
        name: t.Optional[str] = None,
        description: t.Optional[str] = None,
        **kwargs
    ) -> None:
        self.name = name
        self.description = description
        self._kwargs = kwargs

    @abc.abstractmethod
    def apply(self, value: t.Any, context: t.Optional[t.Dict[str, t.Any]] = None) -> t.Any:
        """
        Apply the transformation to a value.

        Args:
            value: Value to transform
            context: Optional context dict (full source data for context-aware transforms)

        Returns:
            Transformed value
        """
        pass

    def validate(self, value: t.Any) -> t.Any:
        """
        Validate input value before transformation.

        Default implementation returns value unchanged.
        Subclasses can override for type-specific validation.
        """
        return value

    def __call__(self, value: t.Any, context: t.Optional[t.Dict[str, t.Any]] = None) -> t.Any:
        """Make transforms callable"""
        return self.apply(value, context)

    ## Operator Overloads ##

    def __rshift__(self, other: 'BaseTransform') -> 'PipelineTransform':
        """
        Pipeline operator: transform1 >> transform2
        Apply transform1, then transform2 to the result.
        """
        return PipelineTransform(transforms=[self, other])

    def __or__(self, other: 'BaseTransform') -> 'FallbackTransform':
        """
        Fallback operator: primary | fallback
        Try primary transform, use fallback if it fails.
        """
        return FallbackTransform(primary=self, backup=other)

    def __and__(self, other: 'BaseTransform') -> 'ParallelTransform':
        """
        Parallel operator: transform1 & transform2
        Apply both transforms and combine results.
        """
        return ParallelTransform(transforms=[self, other])

    ## Method Chaining Equivalents ##

    def then(self, other: 'BaseTransform') -> 'PipelineTransform':
        """Method chaining equivalent of >> operator"""
        return self.__rshift__(other)

    def fallback(self, other: 'BaseTransform') -> 'FallbackTransform':
        """Method chaining equivalent of | operator"""
        return self.__or__(other)

    def parallel(self, other: 'BaseTransform') -> 'ParallelTransform':
        """Method chaining equivalent of & operator"""
        return self.__and__(other)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name})"

class Transform(BaseTransform):
    """
    Concrete transform implementation that wraps a callable.

    This is the main transform class for creating transforms from functions.
    """
    __constructs__ = (BaseTransform.__constructs__ | {'func', 'contextaware'})

    def __init__(
        self,
        func: t.Callable,
        contextaware: bool = False,
        name: t.Optional[str] = None,
        description: t.Optional[str] = None,
        **kwargs
    ) -> None:
        """
        Initialize transform with a callable function.

        Args:
            func: Function to apply for transformation
            name: Optional name for the transform
            description: Optional description
            contextaware: Whether function expects (value, context) or just (value)
        """
        super().__init__(name=name, description=description, **kwargs)
        self.func = func
        self.contextaware = contextaware

        # auto-set name from function if not provided
        if (self.name is None) and hasattr(func, '__name__'):
            self.name = func.__name__

    def apply(self, value: t.Any, context: t.Optional[t.Dict[str, t.Any]] = None) -> t.Any:
        """
        Apply the wrapped function to the value.

        Args:
            value: Value to transform
            context: Optional context dict

        Returns:
            Transformed value
        """
        validated = self.validate(value)
        if self.contextaware:
            context = (context or {})
            return self.func(validated, context)
        return self.func(validated)

class PipelineTransform(BaseTransform):
    """
    Transform that applies multiple transforms in sequence.

    Result of the >> operator: transform1 >> transform2 >> transform3
    """
    __constructs__ = (BaseTransform.__constructs__ | {'transforms'})

    def __init__(
        self,
        transforms: t.List[BaseTransform],
        name: t.Optional[str] = None,
        description: t.Optional[str] = None,
        **kwargs
    ) -> None:
        """
        Initialize pipeline transform.

        Args:
            transforms: List of transforms to apply in sequence
            name: Optional name for the pipeline
            description: Optional description
        """
        if not transforms:
            raise ValueError("PipelineTransform requires at least one transform")

        if not isinstance(transforms, (list, tuple)):
            raise ValueError("'transforms' must be a list or tuple")

        transforms = list(transforms)
        name = (name or f"Pipeline({len(transforms)} transforms)")
        super().__init__(name=name, description=description)
        self.transforms = transforms

    def apply(self, value: t.Any, context: t.Optional[t.Dict[str, t.Any]] = None) -> t.Any:
        """
        Apply all transforms in sequence.

        Args:
            value: Initial value
            context: Optional context dict

        Returns:
            Final transformed value after all transforms
        """
        result = value

        for transform in self.transforms:
            result = transform.apply(result, context)

        return result

    def add(self, transform: BaseTransform) -> 'PipelineTransform':
        """
        Add another transform to the end of the pipeline.

        Args:
            transform: Transform to add

        Returns:
            New PipelineTransform with added transform
        """
        return PipelineTransform(
            transforms=self.transforms + [transform],
            name=self.name,
            description=self.description
        )

    def __rshift__(self, other: BaseTransform) -> 'PipelineTransform':
        """Extend pipeline with another transform."""
        if isinstance(other, PipelineTransform):
            return PipelineTransform(
                transforms=self.transforms + other.transforms
            )
        else:
            return PipelineTransform(
                transforms=self.transforms + [other]
            )

    def __repr__(self) -> str:
        names = [(tr.name or str(tr)) for tr in self.transforms]
        return f"PipelineTransform([{' >> '.join(names)}])"

class FallbackTransform(BaseTransform):
    """
    Transform that tries primary transform first, falls back to secondary if it fails.

    Result of the | operator: primary_transform | fallback_transform
    """
    __constructs__ = (BaseTransform.__constructs__ | {'primary', 'backup'})

    def __init__(
        self,
        primary: BaseTransform,
        backup: BaseTransform,
        name: t.Optional[str] = None,
        description: t.Optional[str] = None,
        **kwargs
    ) -> None:
        """
        Initialize fallback transform.

        Args:
            primary: Primary transform to try first
            backup: Fallback transform if primary fails
            name: Optional name
            description: Optional description
        """
        name = (name or f"Fallback({primary.name} | {backup.name})")
        super().__init__(name=name, description=description)
        self.primary = primary
        self.backup = backup

    def apply(self, value: t.Any, context: t.Optional[t.Dict[str, t.Any]] = None) -> t.Any:
        """
        Try primary transform, use fallback if it fails.

        Args:
            value: Value to transform
            context: Optional context dict

        Returns:
            Result from primary or fallback transform
        """

        try:
            return self.primary.apply(value, context)
        except Exception:
            return self.backup.apply(value, context)

    def __repr__(self) -> str:
        return f"FallbackTransform({self.primary!r} | {self.backup!r})"

class ParallelTransform(BaseTransform):
    """
    Transform that applies multiple transforms to the same value and combines results.

    Result of the & operator: transform1 & transform2 & transform3
    """
    __constructs__ = (BaseTransform.__constructs__ | {'transforms', 'combiner'})

    def __init__(
        self,
        transforms: t.List[BaseTransform],
        combiner: t.Optional[t.Callable[[t.List[t.Any]], t.Any]] = None,
        name: t.Optional[str] = None,
        description: t.Optional[str] = None,
        **kwargs
    ) -> None:
        """
        Initialize parallel transform.

        Args:
            transforms: List of transforms to apply in parallel
            combiner: Function to combine results (default: return list of results)
            name: Optional name
            description: Optional description
        """
        if not transforms:
            raise ValueError("ParallelTransform requires at least one transform")

        if not isinstance(transforms, (list, tuple)):
            raise ValueError("'transforms' must be a list or tuple")

        transforms = list(transforms)
        name = (name or f"Parallel({len(transforms)} transforms)")

        super().__init__(name=name, description=description)
        self.transforms = transforms
        self.combiner = (combiner or (lambda results: results))

    def apply(self, value: t.Any, context: t.Optional[t.Dict[str, t.Any]] = None) -> t.Any:
        """
        Apply all transforms to the same value and combine results.

        Args:
            value: Value to transform
            context: Optional context dict

        Returns:
            Combined result from all transforms
        """
        results = []

        for transform in self.transforms:
            result = transform.apply(value, context)
            results.append(result)

        return self.combiner(results)

    def add(self, transform: BaseTransform) -> 'ParallelTransform':
        """
        Add another transform to run in parallel.

        Args:
            transform: Transform to add

        Returns:
            New ParallelTransform with added transform
        """
        return ParallelTransform(
            transforms=self.transforms + [transform],
            combiner=self.combiner,
            name=self.name,
            description=self.description
        )

    def __and__(self, other: BaseTransform) -> 'ParallelTransform':
        """Extend parallel execution with another transform."""
        if isinstance(other, ParallelTransform):
            return ParallelTransform(
                transforms=self.transforms + other.transforms,
                combiner=self.combiner
            )
        else:
            return ParallelTransform(
                transforms=self.transforms + [other],
                combiner=self.combiner
            )

    def __repr__(self) -> str:
        names = [tr.name or str(tr) for tr in self.transforms]
        return f"ParallelTransform([{' & '.join(names)}])"
