# ~/schematix/src/schematix/transforms/collections.py
"""
Collection transformation functions for lists, dicts, and iterables.
"""
from __future__ import annotations
import random, typing as t, itertools as it, collections as co

from schematix.core.transform import transform, Transform

# Basic Access Operations

@transform
def first(value: t.Any) -> t.Any:
    """Get first item from iterable."""
    if isinstance(value, (list, tuple)):
        return value[0] if value else None
    if isinstance(value, dict):
        return next(iter(value.values()), None)
    try:
        return next(iter(value), None)
    except TypeError:
        return value

@transform
def last(value: t.Any) -> t.Any:
    """Get last item from iterable."""
    if isinstance(value, (list, tuple)):
        return value[-1] if value else None
    if isinstance(value, dict):
        return list(value.values())[-1] if value else None
    try:
        items = list(value)
        return items[-1] if items else None
    except TypeError:
        return value

def nth(index: int, default: t.Any = None) -> Transform:
    """
    Get nth item from iterable.

    Args:
        index: Index to retrieve (supports negative indexing)
        default: Value to return if index is out of bounds

    Returns:
        Transform that gets nth item
    """
    @transform(name=f"nth({index})")
    def _nth(value: t.Any) -> t.Any:
        try:
            if isinstance(value, (list, tuple, str)):
                return value[index]
            if isinstance(value, dict):
                items = list(value.values())
                return items[index]
            items = list(value)
            return items[index]
        except (IndexError, TypeError, KeyError):
            return default
    return _nth

@transform
def length(value: t.Any) -> int:
    """Get length of collection."""
    try:
        return len(value)
    except TypeError:
        return 0

@transform
def isempty(value: t.Any) -> bool:
    """Check if collection is empty."""
    try:
        return len(value) == 0
    except TypeError:
        return True

# List Operations

@transform
def flatten(value: t.Any) -> t.List[t.Any]:
    """Flatten nested iterables into single list."""
    def _flattenrecursive(item):
        if isinstance(item, (str, bytes)):
            yield item
        else:
            try:
                for subitem in item:
                    yield from _flattenrecursive(subitem)
            except TypeError:
                yield item

    try:
        return list(_flattenrecursive(value))
    except:
        return [value] if value is not None else []

@transform
def unique(value: t.Any) -> t.List[t.Any]:
    """Remove duplicates while preserving order."""
    if isinstance(value, dict):
        return list(value.keys())
    try:
        seen = set()
        result = []
        for item in value:
            if item not in seen:
                seen.add(item)
                result.append(item)
        return result
    except (TypeError, AttributeError):
        return [value] if value is not None else []

@transform
def reverse(value: t.Any) -> t.Any:
    """Reverse collection."""
    if isinstance(value, (list, tuple)):
        return type(value)(reversed(value))
    if isinstance(value, str):
        return value[::-1]
    try:
        return list(reversed(list(value)))
    except TypeError:
        return value

@transform
def sort(value: t.Any) -> t.List[t.Any]:
    """Sort collection."""
    try:
        if isinstance(value, dict):
            return sorted(value.items())
        return sorted(value)
    except (TypeError, AttributeError):
        return [value] if value is not None else []

def sortby(key: t.Union[str, t.Callable], reverse: bool = False) -> Transform:
    """
    Sort collection by key function or attribute.

    Args:
        key: Key function or attribute name
        reverse: Whether to sort in reverse order

    Returns:
        Transform that sorts by key
    """
    @transform(name=f"sortby({key})")
    def _sortby(value: t.Any) -> t.List[t.Any]:
        try:
            if isinstance(key, str):
                # Sort by attribute
                keyfunc = lambda x: getattr(x, key, None) if hasattr(x, key) else x.get(key, None) if isinstance(x, dict) else None
            else:
                keyfunc = key

            if isinstance(value, dict):
                return sorted(value.items(), key=lambda x: keyfunc(x[1]), reverse=reverse)
            return sorted(value, key=keyfunc, reverse=reverse)
        except (TypeError, AttributeError):
            return [value] if value is not None else []
    return _sortby

@transform
def shuffle(value: t.Any) -> t.List[t.Any]:
    """Randomly shuffle collection."""
    try:
        items = list(value)
        random.shuffle(items)
        return items
    except (TypeError, AttributeError):
        return [value] if value is not None else []

# Filtering and Mapping

def filter(predicate: t.Callable[[t.Any], bool]) -> Transform:
    """
    Filter items that match predicate.

    Args:
        predicate: Function that returns True for items to keep

    Returns:
        Transform that filters items
    """
    @transform(name=f"filter({predicate.__name__ if hasattr(predicate, '__name__') else 'predicate'})")
    def _filter(value: t.Any) -> t.List[t.Any]:
        try:
            if isinstance(value, dict):
                return {k: v for k, v in value.items() if predicate(v)}
            return [item for item in value if predicate(item)]
        except (TypeError, AttributeError):
            return [value] if value is not None and predicate(value) else []
    return _filter

def map(func: t.Callable[[t.Any], t.Any]) -> Transform:
    """
    Apply function to all items.

    Args:
        func: Function to apply to each item

    Returns:
        Transform that maps function over items
    """
    @transform(name=f"map({func.__name__ if hasattr(func, '__name__') else 'func'})")
    def _map(value: t.Any) -> t.List[t.Any]:
        try:
            if isinstance(value, dict):
                return {k: func(v) for k, v in value.items()}
            return [func(item) for item in value]
        except (TypeError, AttributeError):
            return [func(value)] if value is not None else []
    return _map

def where(condition: t.Union[str, t.Callable]) -> Transform:
    """
    Filter dict items or objects by condition.

    Args:
        condition: Attribute name or function to test

    Returns:
        Transform that filters by condition
    """
    @transform(name=f"where({condition})")
    def _where(value: t.Any) -> t.Any:
        if isinstance(condition, str):
            # Filter by attribute existence or truthiness
            predicate = lambda x: bool(getattr(x, condition, None)) if hasattr(x, condition) else bool(x.get(condition)) if isinstance(x, dict) else False
        else:
            predicate = condition

        try:
            if isinstance(value, dict):
                return {k: v for k, v in value.items() if predicate(v)}
            return [item for item in value if predicate(item)]
        except (TypeError, AttributeError):
            return value if predicate(value) else None
    return _where

# Slicing and Chunking

def slice(start: t.Optional[int] = None, stop: t.Optional[int] = None, step: t.Optional[int] = None) -> Transform:
    """
    Slice collection.

    Args:
        start: Start index
        stop: Stop index
        step: Step size

    Returns:
        Transform that slices collection
    """
    @transform(name=f"slice({start}:{stop}:{step})")
    def _slice(value: t.Any) -> t.Any:
        try:
            if isinstance(value, (list, tuple, str)):
                return value[start:stop:step]
            items = list(value)
            return items[start:stop:step]
        except (TypeError, AttributeError):
            return value
    return _slice

def chunk(size: int) -> Transform:
    """
    Split collection into chunks of specified size.

    Args:
        size: Chunk size

    Returns:
        Transform that chunks collection
    """
    @transform(name=f"chunk({size})")
    def _chunk(value: t.Any) -> t.List[t.List[t.Any]]:
        try:
            items = list(value)
            return [items[i:i + size] for i in range(0, len(items), size)]
        except (TypeError, AttributeError):
            return [[value]] if value is not None else []
    return _chunk

def take(count: int) -> Transform:
    """
    Take first n items.

    Args:
        count: Number of items to take

    Returns:
        Transform that takes first n items
    """
    @transform(name=f"take({count})")
    def _take(value: t.Any) -> t.List[t.Any]:
        try:
            return list(it.islice(value, count))
        except (TypeError, AttributeError):
            return [value] if value is not None and count > 0 else []
    return _take

def skip(count: int) -> Transform:
    """
    Skip first n items.

    Args:
        count: Number of items to skip

    Returns:
        Transform that skips first n items
    """
    @transform(name=f"skip({count})")
    def _skip(value: t.Any) -> t.List[t.Any]:
        try:
            return list(it.islice(value, count, None))
        except (TypeError, AttributeError):
            return [] if count > 0 else [value] if value is not None else []
    return _skip

# Dictionary Operations

@transform
def keys(value: t.Any) -> t.List[t.Any]:
    """Get dictionary keys as list."""
    if isinstance(value, dict):
        return list(value.keys())
    return []

@transform
def values(value: t.Any) -> t.List[t.Any]:
    """Get dictionary values as list."""
    if isinstance(value, dict):
        return list(value.values())
    return []

@transform
def items(value: t.Any) -> t.List[t.Tuple[t.Any, t.Any]]:
    """Get dictionary items as list of tuples."""
    if isinstance(value, dict):
        return list(value.items())
    return []

def get(key: t.Any, default: t.Any = None) -> Transform:
    """
    Get value from dict by key.

    Args:
        key: Key to retrieve
        default: Default value if key not found

    Returns:
        Transform that gets value by key
    """
    @transform(name=f"get({key!r})")
    def _get(value: t.Any) -> t.Any:
        if isinstance(value, dict):
            return value.get(key, default)
        elif hasattr(value, key):
            return getattr(value, key, default)
        return default
    return _get

def pluck(key: t.Any) -> Transform:
    """
    Extract key from each dict in collection.

    Args:
        key: Key to extract from each dict

    Returns:
        Transform that plucks key from each item
    """
    @transform(name=f"pluck({key!r})")
    def _pluck(value: t.Any) -> t.List[t.Any]:
        try:
            result = []
            for item in value:
                if isinstance(item, dict):
                    result.append(item.get(key))
                elif hasattr(item, key):
                    result.append(getattr(item, key))
                else:
                    result.append(None)
            return result
        except (TypeError, AttributeError):
            return []
    return _pluck

# Aggregation Operations

@transform
def sum(value: t.Any) -> t.Union[int, float]:
    """Sum numeric values in collection."""
    import builtins
    try:
        if isinstance(value, dict):
            return builtins.sum(v for v in value.values() if isinstance(v, (int, float)))
        return builtins.sum(x for x in value if isinstance(x, (int, float)))
    except (TypeError, AttributeError):
        return 0

@transform
def count(value: t.Any) -> int:
    """Count items in collection."""
    return length(value)

def countby(key: t.Union[str, t.Callable]) -> Transform:
    """
    Count occurrences by key function or attribute.

    Args:
        key: Key function or attribute name

    Returns:
        Transform that counts by key
    """
    @transform(name=f"countby({key})")
    def _countby(value: t.Any) -> t.Dict[t.Any, int]:
        try:
            if isinstance(key, str):
                keyfunc = lambda x: getattr(x, key, None) if hasattr(x, key) else x.get(key, None) if isinstance(x, dict) else None
            else:
                keyfunc = key

            counter = co.Counter()
            for item in value:
                keyval = keyfunc(item)
                counter[keyval] += 1
            return dict(counter)
        except (TypeError, AttributeError):
            return {}
    return _countby

def groupby(key: t.Union[str, t.Callable]) -> Transform:
    """
    Group items by key function or attribute.

    Args:
        key: Key function or attribute name

    Returns:
        Transform that groups by key
    """
    @transform(name=f"groupby({key})")
    def _groupby(value: t.Any) -> t.Dict[t.Any, t.List[t.Any]]:
        try:
            if isinstance(key, str):
                keyfunc = lambda x: getattr(x, key, None) if hasattr(x, key) else x.get(key, None) if isinstance(x, dict) else None
            else:
                keyfunc = key

            groups = co.defaultdict(list)
            for item in value:
                keyval = keyfunc(item)
                groups[keyval].append(item)
            return dict(groups)
        except (TypeError, AttributeError):
            return {}
    return _groupby

# Set Operations

@transform
def toset(value: t.Any) -> t.Set[t.Any]:
    """Convert to set."""
    try:
        if isinstance(value, dict):
            return set(value.keys())
        return set(value)
    except (TypeError, AttributeError):
        return {value} if value is not None else set()

def union(other: t.Any) -> Transform:
    """
    Union with another collection.

    Args:
        other: Collection to union with

    Returns:
        Transform that computes union
    """
    @transform(name=f"union({other})")
    def _union(value: t.Any) -> t.Set[t.Any]:
        try:
            set1 = toset(value)
            set2 = toset(other)
            return set1 | set2
        except:
            return toset(value)
    return _union

def intersection(other: t.Any) -> Transform:
    """
    Intersection with another collection.

    Args:
        other: Collection to intersect with

    Returns:
        Transform that computes intersection
    """
    @transform(name=f"intersection({other})")
    def _intersection(value: t.Any) -> t.Set[t.Any]:
        try:
            set1 = toset(value)
            set2 = toset(other)
            return set1 & set2
        except:
            return set()
    return _intersection

def difference(other: t.Any) -> Transform:
    """
    Difference from another collection.

    Args:
        other: Collection to subtract

    Returns:
        Transform that computes difference
    """
    @transform(name=f"difference({other})")
    def _difference(value: t.Any) -> t.Set[t.Any]:
        try:
            set1 = toset(value)
            set2 = toset(other)
            return set1 - set2
        except:
            return toset(value)
    return _difference

# List Modification

def append(item: t.Any) -> Transform:
    """
    Append item to collection.

    Args:
        item: Item to append

    Returns:
        Transform that appends item
    """
    @transform(name=f"append({item!r})")
    def _append(value: t.Any) -> t.List[t.Any]:
        try:
            items = list(value)
            items.append(item)
            return items
        except (TypeError, AttributeError):
            return [value, item] if value is not None else [item]
    return _append

def prepend(item: t.Any) -> Transform:
    """
    Prepend item to collection.

    Args:
        item: Item to prepend

    Returns:
        Transform that prepends item
    """
    @transform(name=f"prepend({item!r})")
    def _prepend(value: t.Any) -> t.List[t.Any]:
        try:
            items = list(value)
            items.insert(0, item)
            return items
        except (TypeError, AttributeError):
            return [item, value] if value is not None else [item]
    return _prepend

def extend(other: t.Any) -> Transform:
    """
    Extend collection with another collection.

    Args:
        other: Collection to extend with

    Returns:
        Transform that extends collection
    """
    @transform(name=f"extend({other})")
    def _extend(value: t.Any) -> t.List[t.Any]:
        try:
            items = list(value)
            items.extend(other)
            return items
        except (TypeError, AttributeError):
            try:
                return [value] + list(other)
            except:
                return [value, other] if value is not None else [other]
    return _extend
