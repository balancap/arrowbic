import unittest
from typing import Type, TypeVar

import pyarrow as pa

from arrowbic.core.base_extension_type import BaseExtensionType
from arrowbic.core.extension_type_registry import (
    ExtensionTypeRegistry,
    find_registry_extension_type,
    register_extension_type,
    register_item_pyclass,
)

TItem = TypeVar("TItem")


class DummyData:
    pass


class DummyExtensionType(BaseExtensionType):
    @classmethod
    def __arrowbic_ext_basename__(cls) -> str:
        return "DummyExtType"

    @classmethod
    def __arrowbic_priority__(cls) -> int:
        return 0

    @classmethod
    def __arrowbic_is_item_pyclass_supported__(cls, item_pyclass: Type[TItem]) -> bool:
        return issubclass(item_pyclass, DummyData)


class TestExtensionTypeRegistryBase(unittest.TestCase):
    def test__ext_type_registry__register_root_extension_type__proper_collection_update(
        self,
    ) -> None:
        registry = ExtensionTypeRegistry()
        extension_type = DummyExtensionType(None, None, None)
        registry.register_root_extension_type(extension_type)

        assert registry.root_extension_types == [extension_type]

    def test__ext_type_registry__register_root_extension_type__proper_input_check(
        self,
    ) -> None:
        registry = ExtensionTypeRegistry()
        with self.assertRaises(TypeError):
            registry.register_root_extension_type(pa.float32())
        with self.assertRaises(TypeError):
            registry.register_root_extension_type(DummyExtensionType(None, DummyData))

    def test__ext_type_registry__register_root_extension_type__type_already_in_registry(
        self,
    ) -> None:
        registry = ExtensionTypeRegistry()
        extension_type = DummyExtensionType(None, None, None)
        registry.register_root_extension_type(extension_type)
        with self.assertRaises(ValueError):
            registry.register_root_extension_type(extension_type)

    def test__ext_type_registry__register_root_extension_type__proper_priority_ordering(
        self,
    ) -> None:
        class DummyExtensionTypeBis(BaseExtensionType):
            @classmethod
            def __arrowbic_ext_basename__(cls) -> str:
                return "DummyExtType2"

            @classmethod
            def __arrowbic_priority__(cls) -> int:
                return 10

        registry = ExtensionTypeRegistry()
        extension_type1 = DummyExtensionType(None, None, None)
        extension_type2 = DummyExtensionTypeBis(None, None, None)

        registry.register_root_extension_type(extension_type1)
        registry.register_root_extension_type(extension_type2)
        # Decreasing order of priority.
        assert registry.root_extension_types == [extension_type2, extension_type1]

    def test__ext_type_registry__register_item_pyclass__proper_root_extension_type(
        self,
    ) -> None:
        registry = ExtensionTypeRegistry()
        root_extension_type = DummyExtensionType(None, None, None)
        registry.register_root_extension_type(root_extension_type)

        root_ext_type = registry.register_item_pyclass(DummyData)
        assert root_ext_type is root_extension_type

    def test__ext_type_registry__register_item_pyclass__key_error_if_no_extension_type_found(
        self,
    ) -> None:
        registry = ExtensionTypeRegistry()
        with self.assertRaises(KeyError):
            registry.register_item_pyclass(DummyData)

    def test__ext_type_registry__find_extension_type__no_storage_type(self) -> None:
        registry = ExtensionTypeRegistry()
        root_extension_type = DummyExtensionType(None, None, None)
        registry.register_root_extension_type(root_extension_type)
        registry.register_item_pyclass(DummyData)

        ext_type = registry.find_extension_type(DummyData)
        assert ext_type is root_extension_type

    def test__ext_type_registry__find_extension_type__with_storage_type(self) -> None:
        registry = ExtensionTypeRegistry()
        root_extension_type = DummyExtensionType(None, None, None)
        registry.register_root_extension_type(root_extension_type)
        registry.register_item_pyclass(DummyData)

        ext_type = registry.find_extension_type(DummyData, pa.float32())
        assert ext_type.storage_type == pa.float32()
        assert ext_type.extension_name == root_extension_type.extension_name

    def test__ext_type_registry__find_extension_type__proper_caching(self) -> None:
        registry = ExtensionTypeRegistry()
        root_extension_type = DummyExtensionType(None, None, None)
        registry.register_root_extension_type(root_extension_type)
        registry.register_item_pyclass(DummyData)

        ext_type0 = registry.find_extension_type(DummyData, pa.float32())
        ext_type1 = registry.find_extension_type(DummyData, pa.float32())
        assert ext_type1 is ext_type0

    def test__register_item_pyclass__decorator_properly_working(self) -> None:
        registry = ExtensionTypeRegistry()
        root_extension_type = DummyExtensionType(None, None, None)
        registry.register_root_extension_type(root_extension_type)

        @register_item_pyclass(registry=registry)  # type:ignore
        class DummyDataBis(DummyData):
            pass

        assert registry.find_extension_type(DummyDataBis) is root_extension_type

    def test__register_extension_type__decorator_properly_working(self) -> None:
        registry = ExtensionTypeRegistry()

        @register_extension_type(package_name="pkg", registry=registry)  # type:ignore
        class DummyExtTypeBis(DummyExtensionType):
            pass

        ext_type = registry.register_item_pyclass(DummyData)
        assert isinstance(ext_type, DummyExtTypeBis)
        assert ext_type.extension_name == DummyExtTypeBis(None, None, "pkg").extension_name

    def test__find_registry_extension_type__proper_ext_type(self) -> None:
        registry = ExtensionTypeRegistry()
        root_extension_type = DummyExtensionType(None, None, None)
        registry.register_root_extension_type(root_extension_type)
        registry.register_item_pyclass(DummyData)

        ext_type = find_registry_extension_type(DummyData, registry=registry)
        assert ext_type is root_extension_type
