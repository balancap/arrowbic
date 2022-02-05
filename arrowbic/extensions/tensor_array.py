"""NdArray/Tensor array extension in Arrowbic.
"""
from typing import Iterable, Optional, Type, TypeVar

import numpy as np
import pyarrow as pa

from arrowbic.core.base_extension_array import BaseExtensionArray
from arrowbic.core.base_extension_type import BaseExtensionType
from arrowbic.core.base_types import NdArrayGeneric
from arrowbic.core.extension_type_registry import ExtensionTypeRegistry, find_registry_extension_type

TItem = TypeVar("TItem")
TArray = TypeVar("TArray", bound="TensorArray")


class TensorArray(BaseExtensionArray[NdArrayGeneric]):
    """NdArray/Tensor extension array."""

    @classmethod
    def __arrowbic_ext_type_class__(cls) -> Type[BaseExtensionType]:
        from .tensor_type import TensorType

        return TensorType

    def __arrowbic_getitem__(self, index: int) -> Optional[NdArrayGeneric]:
        """Arrowbic __getitem__ interface, to retrieve a single Numpy NdArray item in an array.

        Args:
            index: Index of the item to retrieve.
        Returns:
            Item (or None if null entry).
        """
        raw_data = self.storage.field(0)[index]
        if not raw_data.is_valid:
            return None

        # Slicing directly the raw Numpy data.
        raw_values = self.storage.field(0).values.to_numpy(zero_copy_only=True)
        raw_offsets = self.storage.field(0).offsets.to_numpy(zero_copy_only=True)

        shape = self.storage.field(1)[index].as_py()
        data = raw_values[raw_offsets[index] : raw_offsets[index + 1]].reshape(shape)
        return data

    @classmethod
    def make_from_data_shape_arrays(
        cls: Type[TArray],
        data_arr: pa.ListArray,
        shape_arr: pa.ListArray,
        *,
        mask: Optional[pa.BooleanArray] = None,
        registry: Optional[ExtensionTypeRegistry] = None,
    ) -> TArray:
        """Build a Tensor extension array from raw data and shape Arrow arrays (as flat list).

        Args:
            data_arr: Flat data Arrow array.
            shape_arr: Flat shape Arrow array.
            mask: Optional boolean mask array.
            registry: Optional Arrowbic registry to use.
        Returns:
            Tensor extension array.
        """
        storage_arr = pa.StructArray.from_arrays([data_arr, shape_arr], ["data", "shape"], mask=mask)
        ext_tensor_type = find_registry_extension_type(np.ndarray, storage_arr.type, registry=registry)
        ext_tensor_arr = cls.from_storage(ext_tensor_type, storage_arr)
        return ext_tensor_arr

    @classmethod
    def from_iterator(
        cls: Type[TArray],
        it_items: Iterable[Optional[TItem]],
        /,
        *,
        size: Optional[int] = None,
        registry: Optional[ExtensionTypeRegistry] = None,
    ) -> TArray:
        """Build the extension array from a Python item iterator.

        Args:
            it_items: Items Python iterable.
            size: Optional size of the input iterable.
            registry: Optional registry where to find the extension type.
        Returns:
            Extension array, with the proper data.
        """
        return super().from_iterator(it_items, size=size, registry=registry)  # type:ignore

    @classmethod
    def from_tensor(cls: Type[TArray], arr: NdArrayGeneric) -> TArray:
        """Build a tensor array from a single tensor, the first dimension being the array dimension.

        Args:
            arr: Data tensor (N0, N1, ...)
        Returns:
            Tensor array of length N0, with tensors of shape (N1, ...)
        """
        arr = np.asarray(arr)
        if arr.ndim < 2:
            raise ValueError(f"Input Numpy array with too few dimensions: '{arr.shape}'.")

        N = arr.shape[0]
        item_shape = arr.shape[1:]
        item_size = np.prod(item_shape)
        # Data array.
        data_values = pa.array(np.ravel(arr))
        data_offsets = pa.array(np.arange(0, N * item_size + 1, item_size, dtype=np.int64))
        data_arr = pa.ListArray.from_arrays(data_offsets, data_values)
        # Shape array.
        shape_arr = pa.array([item_shape] * N)
        return cls.make_from_data_shape_arrays(data_arr, shape_arr)
