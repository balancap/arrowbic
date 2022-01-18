import json
import unittest
from typing import TypeVar

import pyarrow as pa

from arrowbic.core.base_extension_type import BaseExtensionType, make_extension_name

TItem = TypeVar("TItem")


class DummyData:
    pass


class DummyExtensionType(BaseExtensionType[TItem]):
    @classmethod
    def __arrowbic_ext_basename__(cls) -> str:
        return "DummyExtType"


def test__make_extension_name__proper_result() -> None:
    name = make_extension_name("MyExtension", "package")
    assert name == "arrowbic.package.MyExtension"


class TestBaseExtensionType(unittest.TestCase):
    def test__base_extension_type__init__proper_properties_set(self) -> None:
        ext_type = DummyExtensionType(pa.float32(), DummyData, "MyPackage")
        assert ext_type.extension_name == "arrowbic.MyPackage.DummyExtType"
        assert ext_type.extension_basename == "DummyExtType"
        assert ext_type.package_name == "MyPackage"
        assert ext_type.item_pyclass is DummyData

    def test__base_extension_type__init__default_package_name(self) -> None:
        ext_type = DummyExtensionType(pa.float32(), DummyData)
        assert ext_type.package_name == "core"

    def test__base_extension_type__arrowbic_ext_metadata__proper_result(self) -> None:
        ext_type = DummyExtensionType(pa.float32(), DummyData, "MyPackage")
        ext_metadata = ext_type.__arrowbic_ext_metadata__()

        assert isinstance(ext_metadata, dict)
        assert ext_metadata["extension_basename"] == "DummyExtType"
        assert ext_metadata["package_name"] == "MyPackage"
        assert ext_metadata["item_pyclass_name"] == "DummyData"

    def test__base_extension_type__arrow_ext_serialize__proper_json_encoding(self) -> None:
        ext_type = DummyExtensionType(pa.float32(), DummyData, "MyPackage")
        ext_metadata = ext_type.__arrowbic_ext_metadata__()
        ext_serialized = ext_type.__arrow_ext_serialize__()
        assert json.loads(ext_serialized.decode()) == ext_metadata
