"""NdArray/Tensor extension type in Arrowbic.
"""
import itertools
from typing import Any, Dict, Iterable, List, Optional, Type, TypeVar

import numpy as np
import pyarrow as pa

from arrowbic.core.base_extension_type import BaseExtensionType
from arrowbic.core.extension_type_registry import ExtensionTypeRegistry, register_extension_type, register_item_pyclass

from .tensor_array import NdArrayGeneric, TensorArray

TItem = TypeVar("TItem")


def _check_tensor_storage_type(storage_type: pa.DataType) -> None:
    """Check the validity of the tensor storage type.

    Args:
        storage_type: Tensor storage type.
    Raises:
        TypeError: if the storage type is not a proper struct type with "data" and "shape" fields.
    """
    if storage_type == pa.null():
        return

    if not isinstance(storage_type, pa.StructType) or len(storage_type) != 2:
        raise TypeError(f"Tensor base storage type must be struct with two fields, not '{storage_type}'.")
    if storage_type[0].name != "data":
        raise TypeError(f"The first field of tensor storage type should be 'data', not '{storage_type[0].name}'.")
    if storage_type[1].name != "shape" or storage_type[1].type.value_type != pa.int64():
        raise TypeError(f"The second field of tensor storage type should be 'shape', not '{storage_type[1]}'.")


@register_extension_type
class TensorType(BaseExtensionType):
    """NdArray/Tensor extension type.

    Args:
        storage_type: Storage type to use for the Tensor type. Should be struct() or null().
        item_pyclass: Numpy array class to associate with the extension type.
        package_name: (Optional) package of the extension. `core` by default. Helps avoiding name collision.
    """

    def __init__(
        self,
        storage_type: Optional[pa.DataType] = None,
        item_pyclass: Optional[Type[Any]] = None,
        package_name: Optional[str] = None,
    ):
        super().__init__(storage_type, item_pyclass, package_name)
        # Checking the storage_type and item_pyclass.
        # NOTE: PyArrow crashing if check before super().__init__(...)
        _check_tensor_storage_type(self.storage_type)

    def __arrow_ext_class__(self) -> Type[TensorArray]:
        return TensorArray

    def __arrowbic_ext_metadata__(self) -> Dict[str, Any]:
        """Generate the TEnsor extension type metadata.

        Returns:
            Tensor extension type metadata dictionary.
        """
        metadata = super().__arrowbic_ext_metadata__()
        return metadata

    @classmethod
    def __arrowbic_ext_basename__(self) -> str:
        return "tensor"

    @classmethod
    def __arrowbic_priority__(cls) -> int:
        return 1

    @classmethod
    def __arrowbic_is_item_pyclass_supported__(cls, item_pyclass: Type[Any]) -> bool:
        # Support any sub-class of Numpy NdArray.
        return issubclass(item_pyclass, np.ndarray)

    @classmethod
    def __arrowbic_make_item_pyclass__(
        cls, storage_type: pa.DataType, ext_metadata: Dict[str, Any]
    ) -> Type[NdArrayGeneric]:
        """Returns Numpy NdArray standard class for storing array."""
        return np.ndarray

    @classmethod
    def __arrowbic_from_item_iterator__(
        cls,
        it_items: Iterable[Optional[TItem]],
        size: Optional[int] = None,
        registry: Optional[ExtensionTypeRegistry] = None,
    ) -> TensorArray:
        """Build the IntEnum extension array from a Python item iterator.

        Args:
            it_items: IntEnum items Python iterable.
            size: Optional size of the input iterable.
            registry: Optional registry where to find the extension type.
        Returns:
            Extension array, with the proper data.
        """
        if size is not None:
            it_items = itertools.islice(it_items, size)

        # Manually gathering the `data` and `shape` columns.
        arrays: List[Optional[NdArrayGeneric]] = []
        shapes: List[Any] = []
        for v in it_items:
            if v is None:
                arrays.append(None)
                shapes.append([])
            else:
                x = np.asarray(v)
                arrays.append(np.ravel(x))
                shapes.append(x.shape)
        # Build the raw Arrow columns + struct storage.
        data_arr = pa.array(arrays)
        shape_arr = pa.array(shapes, type=pa.list_(pa.int64(), -1))
        return TensorArray.make_from_data_shape_arrays(data_arr, shape_arr, registry=registry)


# Register at least Numpy array types per default.
register_item_pyclass(np.ndarray)
