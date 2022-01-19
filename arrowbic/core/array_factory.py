"""Array factory method. Extending with PyArrow, and adding more typing.
"""
from typing import Iterable, Optional, TypeVar

import pyarrow as pa

from .base_extension_array import BaseExtensionArray
from .extension_type_registry import find_registry_extension_type
from .utils import first_valid_item_in_iterable

TItem = TypeVar("TItem")


def array(obj: Iterable[Optional[TItem]], size: Optional[int] = None) -> BaseExtensionArray[TItem]:
    """Generic `array` factory method, extending PyArrow `array`.

    Args:
        obj: Any iterable, compatible with PyArrow or Arrowbic.
        size: Optional size of the input iterable.
    Returns:
        Arrowbic array (or PyArrow array in the base type case).
    """
    consumed_size, first_item, obj = first_valid_item_in_iterable(obj)
    # No item which is not null.
    if first_item is None:
        size = min(size, consumed_size) if size is not None else consumed_size
        return pa.nulls(size)

    item_pyclass = type(first_item)
    try:
        # Is the first item Python class in the Arrowbic registry?
        root_ext_type = find_registry_extension_type(item_pyclass)
        arr = root_ext_type.__arrowbic_from_item_iterator__(obj, size=size)
        return arr
    except KeyError:
        # Default case: try to use PyArrow
        arr = pa.array(obj, size=size)
        return arr


def asarray(obj: Iterable[Optional[TItem]], size: Optional[int] = None) -> BaseExtensionArray[TItem]:
    """Generic `asarray` factory method, converting to an array if not already the case.

    Args:
        obj: Any iterable, compatible with PyArrow or Arrowbic. Or already PyArrow array.
        size: Optional size of the input iterable.
    Returns:
        Arrowbic array (or PyArrow array in the base type case).
    """
    if isinstance(obj, pa.Array):
        return obj
    return array(obj, size=size)
