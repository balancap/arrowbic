import unittest

import numpy as np
import pyarrow as pa

from arrowbic.extensions import TensorArray


class TestTensorArray(unittest.TestCase):
    def test__tensor_array__get_item__none_element(self) -> None:
        values = [None, [1, 2, 3], None, [[4.0, 5.0], [6.0, 7.0]]]
        arr = TensorArray.from_iterator(values)

        assert isinstance(arr, TensorArray)
        assert arr[0] is None

    def test__tensor_array__get_item__ndarray_element(self) -> None:
        values = [None, [1, 2, 3], None, [[4.0, 5.0], [6.0, 7.0], [8.0, 9.0]]]
        arr = TensorArray.from_iterator(values)

        assert isinstance(arr, TensorArray)
        assert isinstance(arr[3], np.ndarray)
        assert len(arr) == 4
        assert arr.null_count == 2

        assert arr[3].shape == (3, 2)
        assert arr[3].tolist() == values[3]

    def test__tensor_array__from_tensor__proper_result(self) -> None:
        values = np.random.rand(3, 4, 5).astype(np.float32)
        arr = TensorArray.from_tensor(values)

        assert isinstance(arr, TensorArray)
        assert len(arr) == 3
        assert arr.null_count == 0

        assert arr.type.storage_type[0].type == pa.list_(pa.float32(), -1)
        assert arr.type.storage_type[1].type == pa.list_(pa.int64(), -1)
        # Proper data & shape.
        assert arr.storage.field(0)[1].as_py() == np.ravel(values[1]).tolist()
        assert arr.storage.field(1)[1].as_py() == [4, 5]

    def test__tensor_array__from_tensor__not_enough_dimensions(self) -> None:
        values = np.random.rand(3).astype(np.float32)
        with self.assertRaises(ValueError):
            TensorArray.from_tensor(values)
