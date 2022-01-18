from enum import IntEnum
from typing import Optional, TypeVar

from arrowbic.core.base_extension_array import BaseExtensionArray

TItem = TypeVar("TItem", bound=Optional[IntEnum])


class IntEnumArray(BaseExtensionArray[TItem]):
    """IntEnum extension array."""
