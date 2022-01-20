"""IntEnum extension type in Arrowbic.
"""
from enum import IntEnum
from typing import Any, Dict, Iterable, Optional, Type, TypeVar

import pyarrow as pa

from arrowbic.core.base_extension_type import BaseExtensionType
from arrowbic.core.extension_type_registry import (
    ExtensionTypeRegistry,
    find_registry_extension_type,
    register_extension_type,
)
from arrowbic.core.utils import first_valid_item_in_iterable

from .int_enum_array import IntEnumArray

TItem = TypeVar("TItem")


@register_extension_type
class IntEnumType(BaseExtensionType):
    """IntEnum Arrowbic extension type.

    This extension type enables the support in Arrowbic of standard Python IntEnum,
    storing the raw values directly at as a int64 array.

    Args:
        storage_type: Storage type to use for this instance.
        item_pyclass: IntEnum class to associate with the extension type.
        package_name: (Optional) package of the extension. `core` by default. Helps avoiding name collision.
    """

    def __init__(
        self,
        storage_type: Optional[pa.DataType] = None,
        item_pyclass: Optional[Type[Any]] = None,
        package_name: Optional[str] = None,
    ):
        super().__init__(storage_type, item_pyclass, package_name)
        # Checking the storage type. TODO: make it valid with any integer type.
        # NOTE: PyArrow crashing if check before super().__init__(...)
        is_valid_storage = self.storage_type == pa.null() or self.storage_type == pa.int64()
        if not is_valid_storage:
            raise TypeError(f"Invalid Arrow storage type for an IntEnum extension type: {self.storage_type}.")

    def __arrow_ext_class__(self) -> Type[IntEnumArray[Any]]:
        return IntEnumArray

    def __arrowbic_ext_metadata__(self) -> Dict[str, Any]:
        """Generate the IntEnum extension type metadata, with the full IntEnum
        definition.

        Returns:
            IntEnum extension type metadata dictionary.
        """
        metadata = super().__arrowbic_ext_metadata__()
        # IntEnum definition if provided in the extension type.
        item_pyclass: Type[IntEnum] = self.item_pyclass  # type: ignore
        if item_pyclass is not None:
            metadata["int_enum_fields"] = {v.name: v.value for v in item_pyclass}
        return metadata

    @classmethod
    def __arrowbic_ext_basename__(self) -> str:
        return "int_enum"

    @classmethod
    def __arrowbic_priority__(cls) -> int:
        return 1

    @classmethod
    def __arrowbic_is_item_pyclass_supported__(cls, item_pyclass: Type[Any]) -> bool:
        # Support any sub-class of IntEnum by default.
        return issubclass(item_pyclass, IntEnum)

    @classmethod
    def __arrowbic_make_item_pyclass__(cls, storage_type: pa.DataType, ext_metadata: Dict[str, Any]) -> Type[IntEnum]:
        """Generate the Python IntEnum class from the Arrow storage type and extension metadata.

        Args:
            storage_type: Storage type used.
            ext_metadata: IntEnum extension metadata.
        Returns:
            IntEnum Python class
        """
        name = ext_metadata["item_pyclass_name"]
        int_enum_cls = IntEnum(name, ext_metadata["int_enum_fields"])  # type: ignore
        return int_enum_cls

    @classmethod
    def __arrowbic_from_item_iterator__(
        cls,
        it_items: Iterable[Optional[TItem]],
        size: Optional[int] = None,
        registry: Optional[ExtensionTypeRegistry] = None,
    ) -> IntEnumArray[TItem]:
        """Build the IntEnum extension array from a Python item iterator.

        Args:
            it_items: IntEnum items Python iterable.
            size: Optional size of the input iterable.
            registry: Optional registry where to find the extension type.
        Returns:
            Extension array, with the proper data.
        """
        consumed_size, first_item, it_items = first_valid_item_in_iterable(it_items)
        if it_items is None:
            size = min(size, consumed_size) if size is not None else consumed_size
            return pa.nulls(size)

        item_pyclass = type(first_item)
        # TODO: choose optimal integer storage depending on IntEnum definition.
        storage_type = pa.int64()
        ext_enum_type = find_registry_extension_type(item_pyclass, storage_type, registry=registry)
        # Build the IntEnum array.
        storage_arr = pa.array(it_items, size=size)
        arr = IntEnumArray.from_storage(ext_enum_type, storage_arr)
        return arr
