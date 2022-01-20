"""Implementation of base extension type class used in Arrowbic.
"""
import json
from typing import Any, Dict, Iterable, Optional, Type, TypeVar

import pyarrow as pa

from .base_extension_array import BaseExtensionArray

TItem = TypeVar("TItem")


def make_extension_name(extension_basename: str, package_name: str) -> str:
    """Make a full Arrowbic extension name.

    Args:
        extension_basename: Extension basename.
        package_name: Package name.
    Returns:
        Extension fullname.
    """
    extension_name = f"arrowbic.{package_name}.{extension_basename}"
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
        package_name: (Optional) package of the extension. `core` by default. Helps avoiding name collision.
    """

    def __init__(
        self,
        storage_type: Optional[pa.DataType] = None,
        item_pyclass: Optional[Type[Any]] = None,
        package_name: Optional[str] = None,
    ):
        self._package_name: str = package_name or "core"
        self._item_pyclass = item_pyclass

        # Generate the full extension name for PyArrow extension registry.
        extension_name = make_extension_name(self.extension_basename, self._package_name)
        storage_type = storage_type if storage_type is not None else pa.null()
        pa.ExtensionType.__init__(self, storage_type, extension_name)

    @property
    def extension_name(self) -> str:
        """Get the extension full name."""
        return super().extension_name

    @property
    def extension_basename(self) -> str:
        """Get the extension base name (i.e. casual name)."""
        return self.__arrowbic_ext_basename__()

    @property
    def package_name(self) -> str:
        """Get the package name used for the full extension name."""
        return self._package_name

    @property
    def item_pyclass(self) -> Optional[Type[Any]]:
        """Get the item Python class associated with the extension type.

        None if the extension type instance is a root instance.
        """
        return self._item_pyclass

    @property
    def item_pyclass_name(self) -> Optional[str]:
        """Get the item Python class name. None if no item class."""
        item_pyclass_name = self._item_pyclass.__name__ if self._item_pyclass is not None else None
        return item_pyclass_name

    # Arrowbic interface.
    def __arrowbic_ext_metadata__(self) -> Dict[str, Any]:
        """Base extension metadata. This is the minimal metadata information stored
        for any Arrowbic extension type.

        Returns:
            Extension type metadata dictionary.
        """
        metadata = {
            "extension_basename": self.extension_basename,
            "package_name": self.package_name,
            "item_pyclass_name": self.item_pyclass_name,
        }
        return metadata

    @classmethod
    def __arrowbic_ext_basename__(self) -> str:
        """Defines the standard basename of the extension type class."""
        raise NotImplementedError()

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
    def __arrowbic_make_item_pyclass__(cls, storage_type: pa.DataType, ext_metadata: Dict[str, Any]) -> Type[Any]:
        """Generate the Python item class from the Arrow storage type and extension metadata.

        Args:
            storage_type: Storage type used.
            ext_metadata: Extension metadata.
        Returns:
            Generated Python item class compatible with the storage type and metadata.
        """
        raise NotImplementedError()

    @classmethod
    def __arrowbic_from_item_iterator__(
        cls, it_items: Iterable[Optional[TItem]], size: Optional[int] = None, registry: Optional[Any] = None
    ) -> BaseExtensionArray[TItem]:
        """Build the extension array from a Python item iterator.

        Args:
            it_items: Items Python iterable.
            size: Optional size of the input iterable.
            registry: Optional registry where to find the extension type.
        Returns:
            Extension array, with the proper data.
        """
        raise NotImplementedError()

    # PyArrow extension interface, implemented using Arrowbic methods.
    def __arrow_ext_serialize__(self) -> bytes:
        """Standard Arrow(bic) serialization of the extension type metadata.

        By default, to keep the serialized metadata potentially compatible with all
        Arrow backends, the metadata Arrowbic dictionary is encoded using JSON.
        """
        ext_metadata = self.__arrowbic_ext_metadata__()
        return json.dumps(ext_metadata).encode()

    @classmethod
    def __arrow_ext_deserialize__(cls, storage_type: pa.DataType, serialized: bytes) -> "BaseExtensionType":
        """Deserialization of Arrowbic extension type based on the storage type and the metadata.

        Args:
            storage_type: Arrow storage type.
            serialized: Extension metadata serialized.
        Returns:
            Arrowbic extension type instance deserialized.
        """
        raise NotImplementedError()
