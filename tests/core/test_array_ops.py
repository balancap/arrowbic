import unittest
from enum import IntEnum

import numpy as np
import pyarrow as pa

from arrowbic.core.array_ops import array as ab_array
from arrowbic.core.array_ops import asarray as ab_asarray
from arrowbic.core.array_ops import get_pyitem
from arrowbic.core.extension_type_registry import register_item_pyclass, unregister_item_pyclass
from arrowbic.extensions import IntEnumArray


class DummyIntEnum(IntEnum):
    Invalid = 1
    Valid = 2


class TestArrowbicArraysOps(unittest.TestCase):
    def setUp(self) -> None:
        register_item_pyclass(DummyIntEnum)

    def tearDown(self) -> None:
        unregister_item_pyclass(DummyIntEnum)

    def test__array__int_list_input__proper_array(self) -> None:
        arr = ab_array([1, 2, None, 4])
        assert isinstance(arr, pa.Int64Array)
        assert len(arr) == 4
        assert arr.to_pylist() == [1, 2, None, 4]

    def test__array__int_iterator_input__proper_array(self) -> None:
        arr = ab_array(iter([None, 2, None, 4]), size=3)
        assert isinstance(arr, pa.Int64Array)
        assert len(arr) == 3
        assert arr.to_pylist() == [None, 2, None]

    def test__array__numpy_input__proper_array(self) -> None:
        arr: pa.Int64Array = ab_array(np.array([1, 2, 3, 4]))
        assert isinstance(arr, pa.Int64Array)
        assert len(arr) == 4

    def test__array__int_enum_input__proper_array(self) -> None:
        values = [DummyIntEnum.Invalid, None, DummyIntEnum.Valid]
        arr = ab_array(values)
        assert isinstance(arr, IntEnumArray)
        assert len(arr) == 3
        assert list(arr) == values

    def test__asarray__int_enum_input__proper_array(self) -> None:
        values = [DummyIntEnum.Invalid, None, DummyIntEnum.Valid]
        arr = ab_asarray(values)
        assert isinstance(arr, IntEnumArray)
        assert len(arr) == 3
        assert list(arr) == values

    def test__asarray__pyarrow_array__proper_array(self) -> None:
        values = [DummyIntEnum.Invalid, None, DummyIntEnum.Valid]
        arr_in = ab_array(values)
        arr_out = ab_asarray(arr_in)
        assert isinstance(arr_out, IntEnumArray)
        assert arr_out is arr_in

    def test__get_pyitem__pyarrow_simple_array__proper_value(self) -> None:
        arr = pa.array([None, 10, 3, None, 5])
        assert isinstance(get_pyitem(arr, 1), int)
        assert get_pyitem(arr, 1) == 10
        assert get_pyitem(arr, 0) is None

    def test__get_pyitem__arrowbic_array__proper_value(self) -> None:
        values = [DummyIntEnum.Invalid, None, DummyIntEnum.Valid]
        arr = ab_asarray(values)
        assert isinstance(get_pyitem(arr, 0), DummyIntEnum)
        assert get_pyitem(arr, 0) == DummyIntEnum.Invalid
        assert get_pyitem(arr, 1) is None
