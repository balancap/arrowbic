"""Arrowbic extension type main registry implementation.
"""
import logging
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union

import pyarrow as pa

from .base_extension_type import BaseExtensionType

TItem = TypeVar("TItem")
TExtType = TypeVar("TExtType", bound=BaseExtensionType)


class ExtensionTypeRegistry:
    """The Arrowbic extension type registry is wrapping the PyArrow extension registry, with additional
    functionalities to support properly Arrowbic extension type.

    In particular, on the contrary to PyArrow, the Arrowbic registry is making the difference between two
    categories of extension types:
        - `Root` extension types: root instance of an extension type, i.e. not attached to a specific Python item class. These objects
            are properly registered in PyArrow (if the sync. input flag is True).
        - Other extension type instances, with an item Python class associated: these are cached in the Arrowbic registry, for faster acccess,
            but not registered in PyArrow (as they keep the same PyArrow extension name as the formers).

    Args:
        sync_with_pyarrow: Synchronize with PyArrow (i.e. register/unregister in the global PyArrow registry as well).
    """

    def __init__(self, sync_with_pyarrow: bool = False):
        self._sync_with_pyarrow = sync_with_pyarrow
        # Root extension types, i.e. not attached to a particular item Python class.
        self._root_extension_types: Dict[str, BaseExtensionType] = {}
        # Cache associating item Python classes to extension types (with all variations of storage type).
        self._item_pyclasses_cache: Dict[Type[Any], Dict[pa.DataType, BaseExtensionType]] = {}

    def register_root_extension_type(self, extension_type: BaseExtensionType) -> None:
        """Register a (root) extension type in an Arrowbic registry.

        Args:
            extension_type: Extension type to add to the registry.
        Raises:
            TypeError: If the extension type is not compatible with Arrowbic, or not a root extension type.
        """
        # Check a couple of things!
        if not isinstance(extension_type, BaseExtensionType):
            raise TypeError(f"Can not register in Arrowbic the extension type '{extension_type}'.")
        if extension_type.item_pyclass is not None:
            raise TypeError("Can only registered the `root` extension type, i.e. with no item Python class associated.")
        extension_name = extension_type.extension_name
        if extension_name in self._root_extension_types:
            raise ValueError(f"The extension type '{extension_name}' is already registered in Arrowbic.")

        # Insert the root extension type, i.e. without item Python class associated.
        self._root_extension_types[extension_name] = extension_type
        # Re-order the extension types per decreasing Arrowbic priority.
        self._root_extension_types = dict(
            sorted(
                self._root_extension_types.items(),
                key=lambda x: -x[1].__arrowbic_priority__(),
            )
        )
        if self._sync_with_pyarrow:
            pa.register_extension_type(extension_type)

    def register_item_pyclass(self, item_pyclass: Type[Any]) -> BaseExtensionType:
        """Add an item Python class in the registry (with future caching of extension types associated to it).

        Args:
            item_pyclass: Item Python class.
        Returns:
            Root Arrowbic extension type associated with the Python class.
        Raises:
            KeyError: if no Arrowbic extension type found compatible with the Python class.
        """
        if item_pyclass in self._item_pyclasses_cache:
            logging.warning(f"The item Python class '{item_pyclass}' has already been registered in Arrowbic.")
            return self._item_pyclasses_cache[item_pyclass][pa.null()]

        root_ext_type = self._associate_item_pyclass_to_root_extension_type(item_pyclass)
        # Default entry, with the null storage type corresponding to the root extension type.
        self._item_pyclasses_cache[item_pyclass] = {pa.null(): root_ext_type}
        return root_ext_type

    def unregister_item_pyclass(self, item_pyclass: Type[Any]) -> None:
        """Unregister a Python item class from the registry.

        Args:
            item_pyclass: Item Python class to unregister.
        """
        self._item_pyclasses_cache.pop(item_pyclass)

    def find_extension_type(
        self, item_pyclass: Type[Any], storage_type: Optional[pa.DataType] = None
    ) -> BaseExtensionType:
        """Find (or make if not yet cached) the extension type corresponding to an item Python class and a storage type.

        Args:
            item_pyclass: Item Python class to associate to an extension type.
            storage_type: Optional storage type to use. Root extension type returned if None.
        Returns:
            Arrowbic extension type corresponding to the inputs.
        Raises:
            KeyError: if the item Python class was not registered.
        """
        if item_pyclass not in self._item_pyclasses_cache:
            raise KeyError(f"The item Python class '{item_pyclass}' is not registered in Arrowbic.")
        item_pyclass_types_cache = self._item_pyclasses_cache[item_pyclass]
        root_ext_type = item_pyclass_types_cache[pa.null()]
        if storage_type is None:
            return root_ext_type
        if storage_type in item_pyclass_types_cache:
            return item_pyclass_types_cache[storage_type]

        # Generate the proper extension type when not existing.
        ext_type = type(root_ext_type)(
            storage_type=storage_type,
            item_pyclass=item_pyclass,
            package_name=root_ext_type.package_name,
        )
        item_pyclass_types_cache[storage_type] = ext_type
        return ext_type

    def _associate_item_pyclass_to_root_extension_type(self, item_pyclass: Type[Any]) -> BaseExtensionType:
        """Find the root extension type to associate to an item Python class.

        Args:
            item_pyclass: Item Python class.
        Returns:
            Root Arrowbic extension type matching the item Python class.
        Raises:
            KeyError: if no matching extension type is found.
        """
        for extension_type in self._root_extension_types.values():
            if extension_type.__arrowbic_is_item_pyclass_supported__(item_pyclass):
                return extension_type
        raise KeyError(f"Could not find any Arrowbic extension type to associate to the Python class '{item_pyclass}'.")

    @property
    def root_extension_types(self) -> List[BaseExtensionType]:
        """Get all the root registered extension types."""
        return list(self._root_extension_types.values())


_global_registry = ExtensionTypeRegistry(sync_with_pyarrow=True)
"""Global Arrowbic registry, synchronize with PyArrow.
"""


def register_extension_type(
    extension_type_cls: Type[TExtType] = None,
    *,
    package_name: Optional[str] = None,
    registry: Optional[ExtensionTypeRegistry] = None,
) -> Union[Type[TExtType], Callable[[Type[TExtType]], Type[TExtType]]]:
    """Extension type class decorator: registering the extension type class in Arrowbic.

    Args:
        package_name: Optional package name to use in the extension name.
        registry: Registry to use. Global one by default.
    """
    reg = registry if registry is not None else _global_registry

    def wrap(_extension_type_cls: Type[TExtType]) -> Type[TExtType]:
        # Build the default/root instance of the extension type.
        ext_type = _extension_type_cls(
            storage_type=None,
            item_pyclass=None,
            package_name=package_name,
        )
        reg.register_root_extension_type(ext_type)
        return _extension_type_cls

    # Decorator called with parens: register_extension_type(...)
    if extension_type_cls is None:
        return wrap
    # Called without parens.
    return wrap(extension_type_cls)


def register_item_pyclass(
    item_pyclass: Type[TItem] = None,
    *,
    registry: Optional[ExtensionTypeRegistry] = None,
) -> Union[Type[TItem], Callable[[Type[TItem]], Type[TItem]]]:
    """Item Python class decorator: registering the item Python class in Arrowbic.

    The Arrowbic registry is caching all extension type instances and the association to
    item Python classes.

    Args:
        registry: Registry to use. Global one by default.
    """
    reg = registry if registry is not None else _global_registry

    def wrap(_item_cls: Type[TItem]) -> Type[TItem]:
        reg.register_item_pyclass(_item_cls)
        return _item_cls

    # Decorator called with parens: register_item_pyclass(...)
    if item_pyclass is None:
        return wrap
    # Called without parens.
    return wrap(item_pyclass)


def unregister_item_pyclass(item_pyclass: Type[TItem], *, registry: Optional[ExtensionTypeRegistry] = None) -> None:
    """Unregister item Python class from the global Arrowbic registry."""
    registry = registry or _global_registry
    registry.unregister_item_pyclass(item_pyclass)


def find_registry_extension_type(
    item_pyclass: Type[TItem],
    storage_type: Optional[pa.DataType] = None,
    *,
    registry: Optional[ExtensionTypeRegistry] = None,
) -> BaseExtensionType:
    """Find an extension type in the Arrowbic registry.

    Args:
        item_pyclass: Item Python class to find in the registry.
        storage_type: Storage type to use for the extension type.
        registry: Optional registry to use.
    Returns:
        Extension type from the registry.
    Raises:
        KeyError: If the item Python class was not found in the registry.
    """
    registry = registry or _global_registry
    return registry.find_extension_type(item_pyclass, storage_type)
