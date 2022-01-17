import itertools
from typing import Iterable, Optional, Tuple, TypeVar

T = TypeVar("T")


def first_valid_item_in_iterable(it_items: Iterable[Optional[T]]) -> Tuple[int, Optional[T], Iterable[Optional[T]]]:
    """Get the first valid/non-none item in an iterable.

    Args:
        it_items: Items iterable.
    Returns:
        Number of items consumed.
        First non-none item (or None if everything consumed).
        Iterable of all items.
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
