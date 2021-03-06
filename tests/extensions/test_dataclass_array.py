import copy
import unittest

import numpy as np
import numpy.testing as npt
import pyarrow as pa

from arrowbic.core.extension_type_registry import _global_registry
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
