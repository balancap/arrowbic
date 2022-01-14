# Arrowbic

<!-- ![CI](https://github.com/balancap/arrowbic/workflows/Run%20tests/badge.svg?branch=main)
[![codecov](https://codecov.io/gh/balancap/arrowbic/branch/main/graph/badge.svg)](https://codecov.io/gh/balancap/arrowbic) -->

Pythonic [Apache Arrow](https://arrow.apache.org/)

Apache Arrow is an increasingly adopted standard for columnar memory format (and serialization in Parquet, Features, ... formats). *Arrowbic* is allowing you to write efficient data applications, in a Pythonic way, while being backed by Arrow memory layout and optimized operations.

## Why use Arrowbic?

In many data algorithms, there is a design choice to be made of whether to take as input a vector of objects (row oriented storage) or an object of vectors (column oriented storage). While Python makes it easy to write function using the first representation (i.e. typically passing a `list` of objects), there is no easy Pythonic way to write the latter.

Pandas is a great library for data science, but is not necessarily the proper tool to write data production code. On the other hand, Arrow aims to provide the standard for columnar memory representation, but its Python bindings *PyArrow* are quite low level. *Arrowbic* aims to bridge the gap between *PyArrow* and the modern way of writing Python: declare `dataclasses`, use type hints, ...

## Quickstart

### Installation

Install using ```pip install -U arrowbic```.

### Example

How to use a simple `dataclass` definition with `Arrowbic`:

```python
import arrowbic
import pyarrow as pa
import pyarrow.parquet as pq

from dataclasses import dataclass
from enum import IntEnum


@arrowbic.register_item_pyclass
class ItemType(IntEnum):
    Unknown = 0
    Valid = 1
    Invalid = 2


@arrowbic.register_item_pyclass
@dataclass
class DataItem:
    name: str
    size: int
    price: float
    type: ItemType = ItemType.Unknown

# Create an Arrow array from a list of objects.
arr = arrowbic.array([DataItem("stock", idx, idx * 0.1) for idx in range(5)])

# Access individual Arrow columns directly.
print(arr.size, arr.price)

# Use PyArrow ops for sorting, filtering, ...
mask = np.array([True, False, True, False, False])
arr_filtered = arr.filter(mask)
arr_sorted = arr.sort(["price"])

# Replace a column with new values.
# NOTE: new Arrow array generated, as by convention the former are always immutable.
arr_updated = arr.replace(size=[1, 2, 3, 4, 5])

# Use PyArrow serialization in Parquet.
t = pa.table({"data": arr})
pq.write_table(t, "data.pq")
```

We refer the advanced tutorial on how to customize the Arrow extension array to support additional methods (TODO).

## Supported Python types

Arrowbic is supporting only a subset of common Python types. More specifically:
* Base Python types: `int`, `float`, `str` and `bytes`;
* `Enum` and `IntEnum`;
* Numpy base dtypes (including `datetime64` and `timedelta64`);
* Python `dataclass`;
* Numpy arrays;

The library can be extended by users to support additional specific types (see the technical design section).

## Technical design

*Arrowbic* is built on top of [PyArrow extension types](https://arrow.apache.org/docs/python/extending_types.html). Every supported Python type is implemented a custom extension type register in *PyArrow* (and *Arrowbic*). We refer to the [design page](docs/design.md) for more information on the standard extension type interface defined in *Arrowbic*.
