"""Implementation of base extension array class used in Arrowbic.
"""
from typing import Optional, Sequence, TypeVar

import pyarrow as pa

TItem = TypeVar("TItem")


class BaseExtensionArray(pa.ExtensionArray, Sequence[Optional[TItem]]):
    """Base extension array, adding interface to make simple operations easier."""
