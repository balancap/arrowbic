import unittest

import numpy as np
import pyarrow as pa

from arrowbic.extensions import TensorArray, TensorType


class TestTensorType(unittest.TestCase):
    def test__tensor_type__default_init__proper_type(self) -> None:
        ext_type = TensorType()
        assert ext_type.storage_type == pa.null()
        assert ext_type.extension_name == "arrowbic.core.tensor"

    def test__tensor_type__init__invalid_storage_type(self) -> None:
        with self.assertRaises(TypeError):
            TensorType(pa.float32())
        with self.assertRaises(TypeError):
            TensorType(pa.struct({"data": pa.list_(pa.float32(), -1)}))
        with self.assertRaises(TypeError):
            TensorType(pa.struct({"data": pa.list_(pa.float32(), -1), "shape": pa.list_(pa.int32(), -1)}))

    def test__tensor_type__arrow_ext_class__tensor_array(self) -> None:
        ext_type = TensorType()
        assert ext_type.__arrow_ext_class__() is TensorArray

    def test__tensor_type__arrowbic_ext_metadata__proper_dict(self) -> None:
        ext_type = TensorType(None, np.ndarray)
        metadata = ext_type.__arrowbic_ext_metadata__()
        assert len(metadata) == 3
        assert metadata["extension_basename"] == "tensor"
        assert metadata["item_pyclass_name"] == "ndarray"
        assert metadata["package_name"] == "core"

    def test__tensor_type__arrowbic_item_pyclass__numpy_ndarray(self) -> None:
        assert TensorType.__arrowbic_make_item_pyclass__(None, {}) is np.ndarray
        assert TensorType.__arrowbic_is_item_pyclass_supported__(np.ndarray)

    def test__tensor_type__arrowbic_from_iterator__list_of_list_input__proper_result(self) -> None:
        values = [None, [1, 2, 3], None, [[4.0, 5.0], [6.0, 7.0]]]
        arr = TensorType.__arrowbic_from_item_iterator__(values)

        assert isinstance(arr, TensorArray)
        assert len(arr) == 4
        assert arr.null_count == 2
        assert arr.type.storage_type[0].type == pa.list_(pa.float64(), -1)
        assert arr.type.storage_type[1].type == pa.list_(pa.int64(), -1)

        # None items in the storage.
        assert arr.storage.field(0)[0].as_py() is None
        assert arr.storage.field(1)[0].as_py() == []
        assert arr.storage.field(0)[2].as_py() is None
        assert arr.storage.field(1)[2].as_py() == []
        # Data items.
        assert arr.storage.field(0)[1].as_py() == [1.0, 2.0, 3.0]
        assert arr.storage.field(1)[1].as_py() == [3]
        assert arr.storage.field(0)[3].as_py() == [4.0, 5.0, 6.0, 7.0]
        assert arr.storage.field(1)[3].as_py() == [2, 2]

    def test__tensor_type__arrowbic_from_iterator__ndarray_input__proper_result(self) -> None:
        values = np.random.rand(3, 4, 5).astype(np.float32)
        arr = TensorType.__arrowbic_from_item_iterator__(values)

        assert isinstance(arr, TensorArray)
        assert len(arr) == 3
        assert arr.type.storage_type[0].type == pa.list_(pa.float32(), -1)
        assert arr.type.storage_type[1].type == pa.list_(pa.int64(), -1)
        # Proper data & shape.
        assert arr.storage.field(0)[1].as_py() == np.ravel(values[1]).tolist()
        assert arr.storage.field(1)[1].as_py() == [4, 5]
