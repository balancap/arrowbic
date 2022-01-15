import json
import unittest

import pyarrow as pa

from arrowbic.core.base_extension_type import BaseExtensionType, make_extension_name


class DummyData:
    pass


def test__make_extension_name__with_item_pyclass__proper_result():
    name = make_extension_name("MyExtension", "module", "DummyData")
    assert name == "arrowbic.module.MyExtension.DummyData"


def test__make_extension_name__without_item_pyclass__proper_result():
    name = make_extension_name("MyExtension", "module", None)
    assert name == "arrowbic.module.MyExtension"


class TestBaseExtensionType(unittest.TestCase):
    def test__base_extension_type__init__proper_properties_set(self):
        ext_type = BaseExtensionType(pa.float32(), DummyData, "MyExtension", "MyModule")
        assert ext_type.extension_name == "arrowbic.MyModule.MyExtension.DummyData"
        assert ext_type.extension_basename == "MyExtension"
        assert ext_type.module_name == "MyModule"
        assert ext_type.item_pyclass is DummyData

    def test__base_extension_type__init__default_module_name(self):
        ext_type = BaseExtensionType(pa.float32(), DummyData, "MyExtension")
        assert ext_type.module_name == "core"

    def test__base_extension_type__arrowbic_ext_metadata__proper_result(self):
        ext_type = BaseExtensionType(pa.float32(), DummyData, "MyExtension", "MyModule")
        ext_metadata = ext_type.__arrowbic_ext_metadata__()

        assert isinstance(ext_metadata, dict)
        assert ext_metadata["extension_basename"] == "MyExtension"
        assert ext_metadata["module_name"] == "MyModule"
        assert ext_metadata["item_pyclass_name"] == "DummyData"

    def test__base_extension_type__arrow_ext_serialize__proper_json_encoding(self):
        ext_type = BaseExtensionType(pa.float32(), DummyData, "MyExtension", "MyModule")
        ext_metadata = ext_type.__arrowbic_ext_metadata__()
        ext_serialized = ext_type.__arrow_ext_serialize__()
        assert json.loads(ext_serialized.decode()) == ext_metadata
