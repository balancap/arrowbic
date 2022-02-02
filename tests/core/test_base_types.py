import numpy as np
import pyarrow as pa
import pytest

import arrowbic.extensions
from arrowbic.core.base_types import (
    from_arrow_to_numpy_dtype,
    from_arrow_to_python_class,
    from_numpy_to_arrow_type,
    is_supported_base_type,
)


def test__is_supported_base_type__proper_result() -> None:
    assert not is_supported_base_type(arrowbic.extensions.IntEnumType())
    assert not is_supported_base_type(arrowbic.extensions.TensorType())


def test__from_numpy_to_arrow_type__np_dtype__proper_coverage() -> None:
    assert from_numpy_to_arrow_type(None) == pa.null()
    assert from_numpy_to_arrow_type(type(None)) == pa.null()

    assert from_numpy_to_arrow_type(np.bool_) == pa.bool_()
    assert from_numpy_to_arrow_type(np.int8) == pa.int8()
    assert from_numpy_to_arrow_type(np.float32) == pa.float32()

    assert from_numpy_to_arrow_type(np.dtype(str)) == pa.string()
    assert from_numpy_to_arrow_type(np.dtype(bytes)) == pa.binary(-1)

    assert from_numpy_to_arrow_type(np.dtype("datetime64[s]")) == pa.timestamp("s")
    assert from_numpy_to_arrow_type(np.dtype("timedelta64[ns]")) == pa.duration("ns")

    with pytest.raises(TypeError):
        from_numpy_to_arrow_type(np.dtype("O"))


def test__from_numpy_to_arrow_type__python_class__proper_coverage() -> None:
    assert from_numpy_to_arrow_type(None) == pa.null()
    assert from_numpy_to_arrow_type(type(None)) == pa.null()

    assert from_numpy_to_arrow_type(bool) == pa.bool_()
    assert from_numpy_to_arrow_type(int) == pa.int64()
    assert from_numpy_to_arrow_type(float) == pa.float64()

    assert from_numpy_to_arrow_type(str) == pa.string()
    assert from_numpy_to_arrow_type(bytes) == pa.binary(-1)


def test__from_arrow_to_numpy_dtype__proper_coverage() -> None:
    assert from_arrow_to_numpy_dtype(None) == type(None)  # noqa: E721
    assert from_arrow_to_numpy_dtype(type(None)) == type(None)  # noqa: E721
    assert from_arrow_to_numpy_dtype(pa.null()) == type(None)  # noqa: E721

    assert from_arrow_to_numpy_dtype(pa.bool_()) == np.bool_
    assert from_arrow_to_numpy_dtype(pa.uint8()) == np.uint8
    assert from_arrow_to_numpy_dtype(pa.float32()) == np.float32

    assert from_arrow_to_numpy_dtype(pa.string()) == np.dtype(str)
    assert from_arrow_to_numpy_dtype(pa.binary(-1)) == np.dtype(bytes)

    assert from_arrow_to_numpy_dtype(pa.timestamp("us")) == np.dtype("datetime64[us]")
    assert from_arrow_to_numpy_dtype(pa.duration("ns")) == np.dtype("timedelta64[ns]")


def test__from_arrow_to_python_class__proper_coverage() -> None:
    assert from_arrow_to_python_class(pa.null()) == type(None)  # noqa: E721
    assert from_arrow_to_python_class(pa.float32()) == float  # noqa: E721
    assert from_arrow_to_python_class(pa.int32()) == int  # noqa: E721

    assert from_arrow_to_python_class(pa.string()) == str  # noqa: E721
    assert from_arrow_to_python_class(pa.binary(-1)) == bytes  # noqa: E721

    assert from_arrow_to_python_class(pa.timestamp("us")) == np.dtype("datetime64[us]")
    assert from_arrow_to_python_class(pa.duration("ns")) == np.dtype("timedelta64[ns]")
