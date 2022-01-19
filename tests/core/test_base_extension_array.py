import unittest

import pyarrow as pa

from .test_base_extension_type import DummyData, DummyExtensionArray, DummyExtensionType


class TestBaseExtensionArray(unittest.TestCase):
    def test__base_extension_array__from_storage(self) -> None:
        ext_type = DummyExtensionType(pa.int32(), DummyData)
        arr = DummyExtensionArray.from_storage(ext_type, pa.array([1, 2, 3], type=pa.int32()))

        assert isinstance(arr, DummyExtensionArray)
        assert len(arr) == 3
        assert list(arr) == [DummyData(1), DummyData(2), DummyData(3)]

    def test__base_extension_array__from_iterator__input_list(self) -> None:
        values = [DummyData(1), DummyData(2), DummyData(3)]
        arr = DummyExtensionArray.from_iterator(values)

        assert isinstance(arr, DummyExtensionArray)
        assert len(arr) == 3
        assert list(arr) == [DummyData(1), DummyData(2), DummyData(3)]
