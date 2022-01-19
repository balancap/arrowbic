"""Implementation of base extension array class used in Arrowbic.
"""
from typing import Any, Iterator, Optional, Sequence, TypeVar, Union, overload

import pyarrow as pa

TItem = TypeVar("TItem")
TArray = TypeVar("TArray", bound="BaseExtensionArray[Any]")


class BaseExtensionArray(pa.ExtensionArray, Sequence[Optional[TItem]]):
    """Base extension array, adding interface to make simple operations easier."""

    def __arrowbic_getitem__(self, index: int) -> Optional[TItem]:
        """Arrowbic __getitem__ interface, to retrieve a single Python item in an array.

        Args:
            index: Index of the item to retrieve.
        Returns:
            Item (or None if null entry).
        """
        raise NotImplementedError()

    def __iter__(self) -> Iterator[Optional[TItem]]:
        """Default iterator implementation on Arrowbic extension arrays."""
        return (self.__arrowbic_getitem__(idx) for idx in range(len(self)))

    @overload
    def __getitem__(self, index: int) -> Optional[TItem]:
        ...

    @overload
    def __getitem__(self: TArray, index: slice) -> TArray:
        ...

    def __getitem__(self: TArray, index: Union[int, slice]) -> Union[Optional[TItem], TArray]:
        """Slice an Arrowbic extension array (or get a single item).

        Args:
            key: Integer or slice. NOTE: for slicing, we rely fully on PyArrow implementation, which
                may end up copy part of the input array.
        Returns:
            Sliced Arrowbic array or Python item object.
        """
        if isinstance(index, slice):
            # Use PyArrow directly for slicing.
            raw_array = self.storage[index]
            return self.from_storage(self.type, raw_array)
        elif isinstance(index, int):
            return self.__arrowbic_getitem__(index)
        else:
            raise TypeError(f"Unsupported key type '{index}' in Arrowbic array __getitem__.")
