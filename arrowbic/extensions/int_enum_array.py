from typing import Optional, TypeVar

from arrowbic.core.base_extension_array import BaseExtensionArray

TItem = TypeVar("TItem")


class IntEnumArray(BaseExtensionArray[TItem]):
    """IntEnum extension array."""

    def __arrowbic_getitem__(self, index: int) -> Optional[TItem]:
        """Arrowbic __getitem__ interface, to retrieve a single IntEnum item in an array.

        Args:
            index: Index of the item to retrieve.
        Returns:
            Item (or None if null entry).
        """
        item_pyclass = self.type.item_pyclass
        raw_value = self.storage[index].as_py()
        value = item_pyclass(raw_value) if raw_value is not None else None
        return value
