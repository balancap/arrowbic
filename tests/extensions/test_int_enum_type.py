import copy
import unittest
from enum import Enum, IntEnum

import pyarrow as pa

from arrowbic.core.extension_type_registry import _global_registry
from arrowbic.extensions import IntEnumArray, IntEnumType


class DummyIntEnum(IntEnum):
    Invalid = 1
    Valid = 2


class TestIntEnumType(unittest.TestCase):
    def setUp(self) -> None:
        # Start from the default global registry.
        self.registry = copy.deepcopy(_global_registry)
        self.registry.register_item_pyclass(DummyIntEnum)

    def test__int_enum_type__init__root_extension_type(self) -> None:
        ext_type = IntEnumType()
        assert ext_type.extension_name == "arrowbic.core.int_enum"
        assert ext_type.item_pyclass_name is None

    def test__int_enum_type__init__storage_type_check(self) -> None:
        with self.assertRaises(TypeError):
            IntEnumType(pa.int32(), DummyIntEnum)

    def test__int_enum_type__init__check_item_pyclass_is_int_enum(self) -> None:
        class DummyEnum(Enum):
            Invalid = 1

        with self.assertRaises(TypeError):
            IntEnumType(pa.int64(), DummyEnum)

    def test__int_enum_type__init__check_item_pyclass_unique_values(self) -> None:
        class DummyIntEnumBis(IntEnum):
            Invalid = 1
            Valid = 1

        with self.assertRaises(ValueError):
            IntEnumType(pa.int64(), DummyIntEnumBis)

    def test__int_enum_type__ext_metadata(self) -> None:
        ext_type = IntEnumType(pa.int64(), DummyIntEnum)
        metadata = ext_type.__arrowbic_ext_metadata__()

        assert metadata["extension_basename"] == "int_enum"
        assert metadata["item_pyclass_name"] == "DummyIntEnum"
        assert metadata["int_enum_fields"] == {"Invalid": 1, "Valid": 2}

    def test__int_enum_type__arrowbic_class_supported(self) -> None:
        assert IntEnumType.__arrowbic_is_item_pyclass_supported__(DummyIntEnum)
        assert not IntEnumType.__arrowbic_is_item_pyclass_supported__(bool)

    def test__int_enum_type__arrowbic_make_item_pyclass(self) -> None:
        ext_type = IntEnumType(pa.int64(), DummyIntEnum)
        metadata = ext_type.__arrowbic_ext_metadata__()
        int_enum_cls = IntEnumType.__arrowbic_make_item_pyclass__(pa.int64(), metadata)

        assert issubclass(int_enum_cls, IntEnum)
        assert [f.name for f in int_enum_cls] == ["Invalid", "Valid"]
        assert [f.value for f in int_enum_cls] == [1, 2]

    def test__int_enum_type__arrowbic_from_item_iterator__input_list(self) -> None:
        values = [None, DummyIntEnum.Invalid, DummyIntEnum.Valid, None]
        arr = IntEnumType.__arrowbic_from_item_iterator__(values, registry=self.registry)

        assert isinstance(arr, IntEnumArray)
        assert isinstance(arr.type, IntEnumType)
        assert len(arr) == len(values)
        assert list(arr) == values

    def test__int_enum_type__arrowbic_from_item_iterator__input_iterator(self) -> None:
        values = [None, DummyIntEnum.Invalid, DummyIntEnum.Valid, None, None]
        arr = IntEnumType.__arrowbic_from_item_iterator__(iter(values), size=4, registry=self.registry)

        assert isinstance(arr, IntEnumArray)
        assert isinstance(arr.type, IntEnumType)
        assert len(arr) == len(values) - 1
        assert list(arr) == values[:-1]
