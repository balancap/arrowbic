"""Dataclass extension array implementation.
"""
from typing import Any, Dict, List, Optional, Type, TypeVar

import numpy as np
import pyarrow as pa

from arrowbic.core.array_ops import get_pyitem
from arrowbic.core.base_extension_array import BaseExtensionArray
from arrowbic.core.base_extension_type import BaseExtensionType
from arrowbic.core.utils import get_validity_array

TItem = TypeVar("TItem")
TExtArray = TypeVar("TExtArray", bound="DataclassArray")  # type:ignore


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

    def replace(self: TExtArray, **kwargs: Any) -> TExtArray:
        """Replace columns in a dataclass array.

        NOTE: as per convention PyArrow arrays are immutable, this method build a new extension
        array with updated columns.

        Args:
            kwargs: Columns to replace.
        Returns:
            Extension array with updated arrays.
        Raises:
            KeyError: if the input keys does not correspond to dataclass fields.
            TypeError: ...
        """
        from arrowbic.core.array_ops import asarray

        if len(kwargs) == 0:
            return self

        arr_keys = set(self.keys())
        in_keys = set(kwargs.keys())
        if len(in_keys - arr_keys) > 0:
            raise KeyError(f"The input keys do not correspond to dataclass fields: '{in_keys-arr_keys}'.")

        # Combine input and existing column arrays.
        in_arrs: Dict[str, pa.Array] = {k: asarray(v) for k, v in kwargs.items()}
        print(in_arrs)
        print(kwargs)

        field_arrays: Dict[str, pa.Array] = {
            f.name: in_arrs.get(f.name, self.storage.field(idx)) for idx, f in enumerate(self.storage.type)
        }
        # TODO: fix this mess between validity and mask array in PyArrow!!!
        validity_array = get_validity_array(self)
        mask_array = None
        if validity_array is not None:
            mask_array = pa.array(np.logical_not(validity_array.to_numpy(zero_copy_only=False)), type=pa.bool_())

        # Re-build the storage struct array from the new values.
        aw_field_infos = [pa.field(name=k, type=arr.type, nullable=True) for k, arr in field_arrays.items()]
        storage_arr = pa.StructArray.from_arrays(list(field_arrays.values()), fields=aw_field_infos, mask=mask_array)

        # By default: try keeping the same extension type. Rebuild only if necessary. No access to registry for caching.
        ext_dc_type = self.type
        if self.storage.type != storage_arr.type:
            ext_dc_type = type(self.type)(storage_arr.type, ext_dc_type.item_pyclass, ext_dc_type.package_name)
        ext_dc_arr = DataclassArray.from_storage(ext_dc_type, storage_arr)
        return ext_dc_arr
