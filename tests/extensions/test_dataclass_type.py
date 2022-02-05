import copy
import dataclasses
import unittest
from enum import IntEnum
from typing import Optional

import numpy as np
import numpy.testing as npt
import pyarrow as pa

from arrowbic.core.base_types import NdArrayGeneric
from arrowbic.core.extension_type_registry import _global_registry
from arrowbic.extensions import DataclassArray, DataclassType
from arrowbic.extensions.dataclass_type import _from_arrow_field_to_dataclass_field


class DummyIntEnum(IntEnum):
    Invalid = 1
    Valid = 2


@dataclasses.dataclass
class DummyData:
    type: DummyIntEnum
    data: Optional[NdArrayGeneric]
    score: Optional[float]
    name: str


class TestSimpleDataclassType(unittest.TestCase):
    def setUp(self) -> None:
        # Start from the default global registry.
        self.registry = copy.deepcopy(_global_registry)
        self.registry.register_item_pyclass(DummyIntEnum)
        self.registry.register_item_pyclass(DummyData)

    def test__dataclass_type__root_extension_type__proper_properties(self) -> None:
        root_ext_type = DataclassType()
        assert root_ext_type.extension_name == "arrowbic.core.dataclass"
        assert root_ext_type.storage_type == pa.null()

    def test__dataclass_type__init__not_a_proper_storage_type(self) -> None:
        with self.assertRaises(TypeError):
            DataclassType(pa.int32())

    def test__dataclass_type__init__not_a_proper_python_dataclass(self) -> None:
        with self.assertRaises(TypeError):
            DataclassType(pa.struct({"data": pa.int32()}), int)

    def test__dataclass_type__is_supported(self) -> None:
        assert DataclassType.__arrowbic_is_item_pyclass_supported__(DummyData)
        assert not DataclassType.__arrowbic_is_item_pyclass_supported__(int)
        assert not DataclassType.__arrowbic_is_item_pyclass_supported__(str)
        assert not DataclassType.__arrowbic_is_item_pyclass_supported__(DummyIntEnum)

    def test__dataclass_type__ext_metadata__proper_result(self) -> None:
        ext_type = DataclassType(pa.null(), DummyData)
        metadata = ext_type.__arrowbic_ext_metadata__()

        assert isinstance(metadata, dict)
        assert metadata["extension_basename"] == "dataclass"
        assert metadata["item_pyclass_name"] == "DummyData"

        fields = metadata["fields"]
        assert len(fields) == 4
        assert fields == [
            {"name": "type", "nullable": False},
            {"name": "data", "nullable": True},
            {"name": "score", "nullable": True},
            {"name": "name", "nullable": False},
        ]

    def test__dataclass_type__arrowbic_make_item_pyclass__proper_result(self) -> None:
        storage_type = pa.struct(
            {
                "type": self.registry.find_extension_type(DummyIntEnum, pa.int64()),
                "data": self.registry.find_extension_type(
                    np.ndarray, pa.struct({"data": pa.list_(pa.float32(), -1), "shape": pa.list_(pa.int64(), -1)})
                ),
                "score": pa.float32(),
                "name": pa.string(),
            }
        )
        ext_metadata = {"item_pyclass_name": "DummyDataBis"}
        item_pyclass = DataclassType.__arrowbic_make_item_pyclass__(storage_type, ext_metadata)

        assert dataclasses.is_dataclass(item_pyclass)
        assert item_pyclass.__name__ == "DummyDataBis"
        fields = dataclasses.fields(item_pyclass)
        assert len(fields) == 4
        assert fields[0].type == DummyIntEnum
        assert fields[1].type == np.ndarray
        assert fields[2].type == float
        assert fields[3].type == str

    def test__dataclass_type__from_arrow_field_to_dataclass_field__base_type(self) -> None:
        name, pyclass, dc_field = _from_arrow_field_to_dataclass_field(pa.field("field", pa.int32(), nullable=True))
        assert name == "field"
        assert pyclass is int
        assert isinstance(dc_field, dataclasses.Field)

    def test__dataclass_type__from_arrow_field_to_dataclass_field__extension_type(self) -> None:
        name, pyclass, dc_field = _from_arrow_field_to_dataclass_field(
            pa.field("field", self.registry.find_extension_type(DummyIntEnum, pa.int64()), nullable=True)
        )
        assert name == "field"
        assert pyclass is DummyIntEnum
        assert isinstance(dc_field, dataclasses.Field)

    def test__dataclass_type__from_iterator__none_only(self) -> None:
        values = [None, None, None, None]
        arr: pa.NullArray = DataclassType.__arrowbic_from_item_iterator__(iter(values), size=3, registry=self.registry)

        assert isinstance(arr, pa.NullArray)
        assert arr.type == pa.null()
        assert len(arr) == 3

    def test__dataclass_type__from_iterator__common_items__without_none(self) -> None:
        items = [
            DummyData(DummyIntEnum.Invalid, np.array([1, 2, 3]), 1.0, "name0"),
            DummyData(DummyIntEnum.Valid, np.array([4, 5, 6]), 2.0, "name1"),
        ]
        arr = DataclassType.__arrowbic_from_item_iterator__(items, registry=self.registry)

        assert isinstance(arr, DataclassArray)
        assert isinstance(arr.type, DataclassType)
        assert arr.type.extension_basename == "dataclass"

        assert arr.null_count == 0
        assert arr.storage.field(0).to_pylist() == [DummyIntEnum.Invalid, DummyIntEnum.Valid]
        assert arr.storage.field(2).to_pylist() == [1.0, 2.0]
        assert arr.storage.field(3).to_pylist() == ["name0", "name1"]

        arrays = arr.storage.field(1).to_pylist()
        assert len(arrays) == 2
        npt.assert_array_equal(arrays[0], [1, 2, 3])  # type:ignore
        npt.assert_array_equal(arrays[1], [4, 5, 6])  # type:ignore

    def test__dataclass_type__from_iterator__common_items__with_none(self) -> None:
        items = [
            None,
            DummyData(DummyIntEnum.Invalid, np.array([1, 2, 3]), None, "name0"),
            DummyData(DummyIntEnum.Valid, None, 2.0, "name1"),
            None,
            DummyData(DummyIntEnum.Valid, None, 3.0, "name2"),
        ]
        arr = DataclassType.__arrowbic_from_item_iterator__(items, registry=self.registry)

        assert isinstance(arr, DataclassArray)
        assert arr.null_count == 2
        assert arr[0] is None
        assert arr[3] is None

        arrays = arr.storage.field(1).to_pylist()
        print(arrays)
        # Proper null count on field arrays.
        assert arr.storage.field(0).null_count == 2
        assert arr.storage.field(1).null_count == 4
        assert arr.storage.field(2).null_count == 3
        assert arr.storage.field(3).null_count == 2
