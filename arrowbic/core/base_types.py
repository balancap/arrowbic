from typing import TYPE_CHECKING, Any, Dict

import numpy as np
import pyarrow as pa
from numpy.typing import DTypeLike

if TYPE_CHECKING:
    # MyPy fails if not provided with the full annotation.
    NdArrayGeneric = np.ndarray[Any, np.dtype[Any]]
else:
    # Full typing only supported in Python 3.9
    NdArrayGeneric = np.ndarray


_base_from_arrow_to_python_mapping: Dict[pa.DataType, DTypeLike] = {
    pa.null(): type(None),
    pa.bool_(): bool,
    pa.int8(): int,
    pa.int16(): int,
    pa.int32(): int,
    pa.int64(): int,
    pa.uint8(): int,
    pa.uint16(): int,
    pa.uint32(): int,
    pa.uint64(): int,
    pa.float16(): float,
    pa.float32(): float,
    pa.float64(): float,
    pa.string(): str,
    pa.utf8(): str,
    pa.binary(length=-1): bytes,
    # Using the Numpy datetime64 for timestamp/duration.
    pa.timestamp("s"): np.dtype("datetime64[s]"),
    pa.timestamp("ms"): np.dtype("datetime64[ms]"),
    pa.timestamp("us"): np.dtype("datetime64[us]"),
    pa.timestamp("ns"): np.dtype("datetime64[ns]"),
    pa.duration("s"): np.dtype("timedelta64[s]"),
    pa.duration("ms"): np.dtype("timedelta64[ms]"),
    pa.duration("us"): np.dtype("timedelta64[us]"),
    pa.duration("ns"): np.dtype("timedelta64[ns]"),
}
"""Mapping between supported base types and the Python (or Numpy dtype) equivalent.
"""


def is_supported_base_type(type: pa.DataType) -> bool:
    """Is the input type a supported base type?

    Args:
        type: PyArrow type (or Numpy dtype / Python class).
    Returns:
        Is it a supported base type?
    """
    return type in _base_from_arrow_to_python_mapping


def from_numpy_to_arrow_type(dtype: DTypeLike) -> pa.DataType:
    """Convert a Numpy dtype (or Python base class) to an equivalent Arrow type."""
    if isinstance(dtype, pa.DataType):
        return dtype

    # Let's handle a few corner cases!
    if isinstance(dtype, np.dtype) and dtype == np.dtype("O"):
        raise TypeError("Can not convert Numpy object dtype to Arrow type.")
    elif dtype is None or dtype == type(None):  # noqa: E721
        return pa.null()

    # Rely on PyArrow for the default.
    return pa.from_numpy_dtype(dtype)


def from_arrow_to_numpy_dtype(awtype: pa.DataType) -> DTypeLike:
    """Convert an Arrow type to an equivalent Numpy dtype."""
    if isinstance(awtype, np.dtype):
        return type

    # Corner cases. Weird choices of PyArrow to return dtype('O')
    if awtype is None or awtype == type(None):  # noqa: E721
        return type(None)
    elif pa.types.is_null(awtype):
        return type(None)
    elif pa.types.is_string(awtype):
        return np.dtype(str)
    elif pa.types.is_binary(awtype):
        return np.dtype(bytes)
    elif pa.types.is_timestamp(awtype):
        # PyArrow converting to "ns"?!
        return np.datetime64(0, awtype.unit).dtype
    elif pa.types.is_duration(awtype):
        # PyArrow converting to "ns"?!
        return np.timedelta64(0, awtype.unit).dtype
    return awtype.to_pandas_dtype()


def from_arrow_to_python_class(type: pa.DataType) -> DTypeLike:
    """Convert an Arrow type to an (almost) equivalent Python class.

    For now, Arrowbic is using Numpy dtype for timestamp and duration conversion, to keep
    the proper time unit information.
    """
    return _base_from_arrow_to_python_mapping[type]
