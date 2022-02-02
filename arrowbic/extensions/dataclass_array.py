"""Dataclass extension array implementation.
"""
from typing import List, Optional, Type, TypeVar

import pyarrow as pa

from arrowbic.core.array_ops import get_pyitem
from arrowbic.core.base_extension_array import BaseExtensionArray
from arrowbic.core.base_extension_type import BaseExtensionType

TItem = TypeVar("TItem")


class DataclassArray(BaseExtensionArray[TItem]):
    """Generic dataclass array.

    This class can be sub-classed in order to get better typing in common IDE!
    """

    @classmethod
    def __arrowbic_ext_type_class__(cls) -> Type[BaseExtensionType]:
        from .dataclass_type import DataclassType

        return DataclassType

    def __arrowbic_getitem__(self, index: int) -> Optional[TItem]:
        """Arrowbic __getitem__ interface, to retrieve a single IntEnum item in an array.

        Args:
            index: Index of the item to retrieve.
        Returns:
            Item (or None if null entry).
        """
        raw_data = self.storage[index]
        if not raw_data.is_valid:
            return None

        # Extract the raw fields values, and the build the item dataclass object.
        values = {f.name: get_pyitem(self.storage.field(c), index) for c, f in enumerate(self.storage.type)}
        item_pyclass = self.type.item_pyclass
        item = item_pyclass(**values)
        return item

    def keys(self) -> List[str]:
        """Get the list of keys/fields in the dataclass Arrowbic array.

        Returns:
            List of the keys.
        """
        return [f.name for f in self.storage.type]

    def __getattr__(self, key: str) -> pa.Array:
        """Implement __getattr__ for the dataclass Arrowbic extension array.

        With the implementation of `__getattr__`, one can directly access individual
        field columns, e.g. `arr.field` (when there is no conflict with the array API).

        In case of name conflict, one can use instead the key access `arr["field"]`.

        Args:
            key: Column field key.
        Returns:
            Dataclass field array.
        """
        keys = self.keys()
        if key in keys:
            return self.storage.field(keys.index(key))
        raise KeyError(f"Unknown field '{key}' in the Arrowbic dataclass extension array. Available columns: {keys}.")
