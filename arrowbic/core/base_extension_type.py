"""Implementation of base extension type class used in Arrowbic.
"""
import json
from typing import Any, Dict, Iterator, Optional, Type

import pyarrow as pa


def make_extension_name(
    extension_basename: str, module_name: str, item_pyclass_name: Optional[str]
) -> str:
    """Make a full Arrowbic extension name.

    Args:
        extension_basename: Extension basename.
        module_name: Module name.
        item_pyclass_name: Optional Python item class name.
    Returns:
        Extension fullname.
    """
    extension_name = f"arrowbic.{module_name}.{extension_basename}"
    if item_pyclass_name is not None and len(item_pyclass_name) > 0:
        extension_name += f".{item_pyclass_name}"
    return extension_name


class BaseExtensionType(pa.ExtensionType):
    """Base class for all Arrowbic extension type.

    This class must be the parent class of any extension type registered in Arrowbic. It defines the standard
    interface that should be implemented, and also provides a few additional useful methods compared to PyArrow extension type.

    The Arrowbic standard interface enables the library to:
    - Associate a Python item instance to an extension type from the registry;
    - Build an Arrowbic extension array from an iterator of Python items;
    - Dynamically re-generate the item Python class definition from the metadata and Arrow storage type;

    Args:
        storage_type: Storage type to use for this instance.
        item_pyclass: Item Python class to associate with the extension type.
        extension_name: Base extension name.
        module_name: (Optional) module of the extension. `core` by default. Helps avoiding name collision.
    """

    def __init__(
        self,
        storage_type: pa.DataType,
        item_pyclass: Optional[Type[Any]],
        extension_basename: str,
        module_name: Optional[str] = None,
    ):
        self._extension_basename: str = extension_basename
        self._module_name: str = module_name or "core"
        self._item_pyclass = item_pyclass

        # Generate the full extension name for PyArrow extension registry.
        self._item_pyclass_name = (
            item_pyclass.__name__ if item_pyclass is not None else None
        )
        extension_name = make_extension_name(
            self._extension_basename, self._module_name, self._item_pyclass_name
        )
        pa.ExtensionType.__init__(self, storage_type, extension_name)

    @property
    def extension_basename(self) -> str:
        """Get the extension base name (i.e. casual name)."""
        return self._extension_basename

    @property
    def module_name(self) -> str:
        """Get the module name used for the full extension name."""
        return self._module_name

    @property
    def item_pyclass(self) -> Optional[Type[Any]]:
        """Get the item Python class associated with the extension type."""
        return self._item_pyclass

    def __arrowbic_ext_metadata__(self) -> Dict[str, Any]:
        """Base extension metadata. This is the minimal metadata information stored
        for any Arrowbic extension type.

        Returns:
            Extension type metadata dictionary.
        """
        metadata = {
            "extension_basename": self._extension_basename,
            "module_name": self._module_name,
            "item_pyclass_name": self._item_pyclass_name,
        }
        return metadata

    @classmethod
    def __arrowbic_priority__(cls) -> int:
        """Defines the ordering in the Arrowbic registry, used for finding the extension type
        matching a Python class.

        Returns:
            Integer priority, used in the registry ordering. Zero by default.
        """
        return 0

    @classmethod
    def __arrowbic_is_item_pyclass_supported__(cls, item_pyclass: Type[Any]) -> bool:
        """Is the extension type supporting/compatible with an item Python class?

        Args:
            item_pyclass: Item Python class.
        Returns:
            Is the class supported by the extension type?
        """
        raise NotImplementedError()

    @classmethod
    def __arrowbic_make_item_pyclass__(
        cls, storage_type: pa.DataType, ext_metadata: Dict[str, Any]
    ) -> Type[Any]:
        """Generate the Python item class from the Arrow storage type and extension metadata.

        Args:
            storage_type: Storage type used.
            ext_metadata: Extension metadata.
        Returns:
            Generated Python item class compatible with the storage type and metadata.
        """
        raise NotImplementedError()

    def __arrowbic_from_item_iterator__(
        self, it_items: Iterator[Any]
    ) -> pa.ExtensionArray:
        """Build the extension array from a Python item iterator.

        Args:
            it_items: Items Python iterator.
        Returns:
            Extension array, with the proper data.
        """
        raise NotImplementedError()

    def __arrow_ext_serialize__(self) -> bytes:
        """Standard Arrow(bic) serialization of the extension type metadata.

        By default, to keep the serialized metadata potentially compatible with all
        Arrow backends, the metadata Arrowbic dictionary is encoded using JSON.
        """
        ext_metadata = self.__arrowbic_ext_metadata__()
        return json.dumps(ext_metadata).encode()

    @classmethod
    def __arrow_ext_deserialize__(
        cls, storage_type: pa.DataType, serialized: bytes
    ) -> "BaseExtensionType":
        """Deserialization of Arrowbic extension type based on the storage type and the metadata.

        Args:
            storage_type: Arrow storage type.
            serialized: Extension metadata serialized.
        Returns:
            Arrowbic extension type instance deserialized.
        """
        raise NotImplementedError()
