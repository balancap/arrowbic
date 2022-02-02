import itertools
from typing import Any, Dict, Iterable, List, Optional, Tuple, TypeVar, overload

import immutables

from .base_types import NdArrayGeneric

T = TypeVar("T")
U = TypeVar("U")


# Mypy overloads. Helps the typing check, and IDE integration.
@overload
def first_valid_item_in_iterable(it_items: List[Optional[T]]) -> Tuple[int, Optional[T], List[Optional[T]]]:
    pass


@overload
def first_valid_item_in_iterable(it_items: NdArrayGeneric) -> Tuple[int, Optional[T], NdArrayGeneric]:
    pass


@overload
def first_valid_item_in_iterable(it_items: Iterable[Optional[T]]) -> Tuple[int, Optional[T], Iterable[Optional[T]]]:
    pass


def first_valid_item_in_iterable(it_items: Iterable[Optional[T]]) -> Tuple[int, Optional[T], Iterable[Optional[T]]]:
    """Get the first valid/non-none item in an iterable.

    Args:
        it_items: Items iterable.
    Returns:
        Number of items consumed.
        First non-none item (or None if everything consumed).
        Iterable of all items (same as input if it is a sequence type).
    """
    idx = 0
    consumed_values = []
    is_random_access = hasattr(it_items, "__getitem__")
    for v in it_items:
        consumed_values.append(v)
        if v is not None:
            # Need to prepend consumed items if not a random access iterable.
            if not is_random_access:
                it_items = itertools.chain(iter(consumed_values), it_items)
            return (idx, v, it_items)
        idx += 1
    return (idx, None, consumed_values)


@overload
def as_immutable(obj: List[T]) -> Tuple[T, ...]:
    ...


@overload
def as_immutable(obj: Tuple[T, ...]) -> Tuple[T, ...]:
    ...


@overload
def as_immutable(obj: Dict[T, U]) -> Dict[T, U]:
    ...


@overload
def as_immutable(obj: int) -> int:
    ...


@overload
def as_immutable(obj: float) -> float:
    ...


@overload
def as_immutable(obj: str) -> str:
    ...


@overload
def as_immutable(obj: bytes) -> bytes:
    ...


@overload
def as_immutable(obj: None) -> None:
    ...


def as_immutable(obj: Any) -> Any:
    """Convert to an equivalent immutable Python object.

    Args:
        obj: Python object.
    Returns:
        Immutable Python equivalent.
    Raises:
        TypeError: if can not convert the input to an equivalent immutable object.
    """
    if isinstance(obj, (type(None), int, float, bytes, str)):
        return obj
    elif isinstance(obj, (tuple, list)):
        return tuple(obj)
    elif isinstance(obj, dict):
        return immutables.Map({k: as_immutable(v) for k, v in obj.items()})
    raise TypeError(f"Can not convert to immutable the object '{obj}'.")
