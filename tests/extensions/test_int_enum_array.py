import unittest
from enum import IntEnum

from arrowbic.core.extension_type_registry import register_item_pyclass, unregister_item_pyclass
from arrowbic.extensions import IntEnumArray


class DummyIntEnum(IntEnum):
    Invalid = 1
    Valid = 2


class TestIntEnumArray(unittest.TestCase):
    def setUp(self) -> None:
        register_item_pyclass(DummyIntEnum)

    def tearDown(self) -> None:
        unregister_item_pyclass(DummyIntEnum)

    def test__int_enum_array__get_item__int_index__proper_result(self) -> None:
        values = [None, DummyIntEnum.Invalid, DummyIntEnum.Valid, None, None]
        arr = IntEnumArray.from_iterator(values)

        assert arr[0] is None
        assert arr[1] == DummyIntEnum.Invalid
        assert type(arr[1]) is DummyIntEnum

    def test__int_enum_array__iter__proper_result(self) -> None:
        values_in = [None, DummyIntEnum.Invalid, DummyIntEnum.Valid, None, None]
        arr = IntEnumArray.from_iterator(values_in)
        values_out = list(arr)
        assert values_out == values_in
