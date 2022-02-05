"""Dataclass extension type implementation.
"""
import dataclasses
import itertools
from typing import Any, Dict, Iterable, Optional, Tuple, Type, TypeVar

import pyarrow as pa
from typing_inspect import is_optional_type

from arrowbic.core.base_extension_type import BaseExtensionType
from arrowbic.core.base_types import from_arrow_to_python_class, is_supported_base_type
from arrowbic.core.extension_type_registry import (
    ExtensionTypeRegistry,
    find_registry_extension_type,
    register_extension_type,
)
from arrowbic.core.utils import first_valid_item_in_iterable

from .dataclass_array import DataclassArray

TItem = TypeVar("TItem")


def _check_dataclass_storage_type(storage_type: pa.DataType) -> None:
    """Check the storage type corresponding to the expected storage for a dataclass extension type.

    Args:
        storage_type: Arrow storage type to check.
    Raises:
        TypeError: if the input type is not a proper dataclass storage type.
    """
    if storage_type == pa.null():
        return
    if not isinstance(storage_type, pa.StructType):
        raise TypeError("The Arrow storage type of a dataclass extension type should be `StructType`.")


def _check_dataclass_item_pyclass(item_pyclass: Optional[Type[Any]], registry: Optional[ExtensionTypeRegistry]) -> None:
    """Check an input Python class is a supported dataclass definition.

    TODO: check if the dataclass field are supported, i.e.:
        - Field types is a base type or part of the Arrowbic registry;
        - Checking generic used are supported (Optional, Union, List, ...)

    Args:
        item_pyclass: Item Python class.
        registry: Arrowbic registry to use.
    """
    if item_pyclass is None:
        return
    if not dataclasses.is_dataclass(item_pyclass):
        raise TypeError(f"The input item Python class is not a dataclass: {item_pyclass}.")


def _from_arrow_field_to_dataclass_field(field: pa.Field) -> Tuple[str, Type[Any], dataclasses.Field]:  # type:ignore
    """Convert a PyArrow field to dataclass field.

    Args:
        field: PyArrow field.
    Returns:
        Tuple [name, Python class, dataclass field].
    """
    # TODO: support nullable parameter, as an optional.
    if is_supported_base_type(field.type):
        item_pyclass: Type[Any] = from_arrow_to_python_class(field.type)  # type:ignore
        return (field.name, item_pyclass, dataclasses.field())
    elif isinstance(field.type, BaseExtensionType) and field.type.item_pyclass is not None:
        return (field.name, field.type.item_pyclass, dataclasses.field())

    raise TypeError(f"Could not convert PyArrow field '{field}' to equivalent dataclass field.")


@register_extension_type
class DataclassType(BaseExtensionType):
    """Dataclass extension type.

    This extension type is supporting any dataclass definition, as long as all fields are
    supported in Arrowbic (base type or registered Python class).

    Args:
        storage_type: Storage type to use for the Tensor type. Should be struct(...) or null().
        item_pyclass: Any dataclass Python class.
        package_name: (Optional) package of the extension. `core` by default. Helps avoiding name collision.
        registry: Optional Arrowbic registry (global one by default).
    """

    def __init__(
        self,
        storage_type: Optional[pa.DataType] = None,
        item_pyclass: Optional[Type[Any]] = None,
        package_name: Optional[str] = None,
        *,
        registry: Optional[ExtensionTypeRegistry] = None,
    ):
        super().__init__(storage_type, item_pyclass, package_name, registry=registry)
        # Checking the storage_type and item_pyclass.
        # NOTE: PyArrow crashing if check before super().__init__(...)
        _check_dataclass_storage_type(self.storage_type)
        _check_dataclass_item_pyclass(self.item_pyclass, None)

    def __arrow_ext_class__(self) -> Type[DataclassArray[Any]]:
        return DataclassArray

    def __arrowbic_ext_metadata__(self) -> Dict[str, Any]:
        """Generate the Dataclass extension type metadata.

        Returns:
            Dataclass extension type metadata dictionary.
        """
        metadata = super().__arrowbic_ext_metadata__()
        fields = []
        if self.item_pyclass is not None:
            # Serialize the dataclass definition.
            fields = [
                {"name": f.name, "nullable": is_optional_type(f.type)} for f in dataclasses.fields(self.item_pyclass)
            ]
        metadata["fields"] = fields
        return metadata

    @classmethod
    def __arrowbic_ext_basename__(self) -> str:
        return "dataclass"

    @classmethod
    def __arrowbic_priority__(cls) -> int:
        return 1

    @classmethod
    def __arrowbic_is_item_pyclass_supported__(cls, item_pyclass: Type[Any]) -> bool:
        """Is a Python class supported: returns True for any dataclass."""
        # Support any dataclass definition.
        return dataclasses.is_dataclass(item_pyclass)

    @classmethod
    def __arrowbic_make_item_pyclass__(cls, storage_type: pa.DataType, ext_metadata: Dict[str, Any]) -> Type[Any]:
        """Returns dataclass definition from storage type and metadata.

        Args:
            storage_type: Storage type to use to build the dataclass definition.
            ext_metadata: Extension metadata.
        Returns:
            Item Python dataclass.
        Raises:
            TypeError: if the input storage type is not valid.
        """
        _check_dataclass_storage_type(storage_type)
        if storage_type == pa.null():
            raise TypeError("Can not build a dataclass definition from an Arrow null datatype.")

        item_pyclass_name = ext_metadata["item_pyclass_name"]
        fields = [_from_arrow_field_to_dataclass_field(f) for f in storage_type]
        item_pyclass = dataclasses.make_dataclass(item_pyclass_name, fields)
        return item_pyclass

    @classmethod
    def __arrowbic_from_item_iterator__(
        cls,
        it_items: Iterable[Optional[TItem]],
        /,
        *,
        size: Optional[int] = None,
        registry: Optional[ExtensionTypeRegistry] = None,
    ) -> DataclassArray[TItem]:
        """Build the IntEnum extension array from a Python item iterator.

        Args:
            it_items: IntEnum items Python iterable.
            size: Optional size of the input iterable.
            registry: Optional registry where to find the extension type.
        Returns:
            Extension array, with the proper data.
        """
        from arrowbic.core.array_ops import array as make_array

        if size is not None:
            it_items = itertools.islice(it_items, size)
        # TODO: more efficient way than consuming the full iterator?
        items = list(it_items)
        _, first_item, items = first_valid_item_in_iterable(items)
        # Null array directly!
        if first_item is None:
            return pa.nulls(len(items))

        dc_field_infos = {f.name: f for f in dataclasses.fields(first_item)}
        # Build individual field arrays.
        field_arrays: Dict[str, pa.Array] = {
            k: make_array([v.__dict__[k] if v is not None else None for v in items]) for k in dc_field_infos.keys()
        }
        # Struct array, with boolean mask.
        mask = pa.array([v is None for v in items], type=pa.bool_())
        aw_field_infos = [pa.field(name=k, type=arr.type, nullable=True) for k, arr in field_arrays.items()]
        storage_arr = pa.StructArray.from_arrays(list(field_arrays.values()), fields=aw_field_infos, mask=mask)

        # Build the extension array, using registry extension type cache if existing.
        ext_dc_type = find_registry_extension_type(type(first_item), storage_arr.type, registry=registry)
        ext_dc_arr = DataclassArray.from_storage(ext_dc_type, storage_arr)
        return ext_dc_arr
