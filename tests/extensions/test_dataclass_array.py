import copy
import unittest

import numpy as np
import numpy.testing as npt
import pyarrow as pa

from arrowbic.core.extension_type_registry import _global_registry
from arrowbic.core.utils import get_validity_array
from arrowbic.extensions import DataclassArray
from arrowbic.extensions.tensor_array import TensorArray

from .test_dataclass_type import DummyData, DummyIntEnum


class TestDataclassArray(unittest.TestCase):
    def setUp(self) -> None:
        # Start from the default global registry.
        self.registry = copy.deepcopy(_global_registry)
        self.registry.register_item_pyclass(DummyIntEnum)
        self.registry.register_item_pyclass(DummyData)

    def test__dataclass_array__get_item__none_element(self) -> None:
        items = [
            None,
            DummyData(DummyIntEnum.Invalid, np.array([1, 2, 3]), None, "name0"),
            None,
        ]
        arr = DataclassArray.from_iterator(items, registry=self.registry)

        assert len(arr) == 3
        assert arr[0] is None
        assert arr[2] is None

    def test__dataclass_array__get_item__valid_item(self) -> None:
        items = [
            None,
            DummyData(DummyIntEnum.Invalid, np.array([1, 2, 3]), None, "name0"),
            DummyData(DummyIntEnum.Valid, None, 3.0, "name2"),
        ]
        arr = DataclassArray.from_iterator(items, registry=self.registry)

        assert len(arr) == 3
        assert arr[2] == items[2]

        assert arr[1] is not None
        assert arr[1].data is not None
        npt.assert_array_equal(arr[1].data, items[1].data)  # type:ignore

    def test__dataclass_array__keys__proper_list(self) -> None:
        items = [
            None,
            DummyData(DummyIntEnum.Invalid, np.array([1, 2, 3]), None, "name0"),
            DummyData(DummyIntEnum.Valid, None, 3.0, "name2"),
        ]
        arr = DataclassArray.from_iterator(items, registry=self.registry)
        assert arr.keys() == ["type", "data", "score", "name"]

    def test__dataclass_array__getattr__proper_columns(self) -> None:
        items = [
            None,
            DummyData(DummyIntEnum.Invalid, np.array([1, 2, 3]), None, "name0"),
            DummyData(DummyIntEnum.Valid, None, 3.0, "name2"),
        ]
        arr = DataclassArray.from_iterator(items, registry=self.registry)

        # assert isinstance(arr.type, IntEnumArray)
        assert isinstance(arr.data, TensorArray)
        assert isinstance(arr.score, pa.FloatingPointArray)
        assert isinstance(arr.name, pa.StringArray)

    def test__dataclass_array__replace__no_inputs__return_same(self) -> None:
        items = [
            DummyData(DummyIntEnum.Invalid, np.array([1, 2, 3]), None, "name0"),
            DummyData(DummyIntEnum.Valid, None, 3.0, "name2"),
        ]
        arr_in = DataclassArray.from_iterator(items, registry=self.registry)
        arr_out = arr_in.replace()
        assert arr_out is arr_in

    def test__dataclass_array__replace__invalid_input_keys(self) -> None:
        items = [
            DummyData(DummyIntEnum.Invalid, np.array([1, 2, 3]), None, "name0"),
            DummyData(DummyIntEnum.Valid, None, 3.0, "name2"),
        ]
        arr_in = DataclassArray.from_iterator(items, registry=self.registry)
        with self.assertRaises(KeyError):
            arr_in.replace(test=np.array([1, 2]))

    def test__dataclass_array__replace__proper_fields_update(self) -> None:
        items = [
            None,
            DummyData(DummyIntEnum.Invalid, np.array([1, 2, 3]), None, "name0"),
            DummyData(DummyIntEnum.Valid, None, 3.0, "name2"),
        ]
        arr_in = DataclassArray.from_iterator(items, registry=self.registry)
        arr_out = arr_in.replace(score=np.array([4.0, 5.0, 6.0]), type=[DummyIntEnum.Invalid, DummyIntEnum.Valid, None])

        assert len(arr_out) == len(arr_in)
        assert get_validity_array(arr_out).to_pylist() == [False, True, True]  # type:ignore
        assert arr_out.type is arr_in.type
        assert arr_out.score.to_pylist() == [4.0, 5.0, 6.0]
        assert arr_out.storage.field(0).to_pylist() == [4.0, 5.0, 6.0]
