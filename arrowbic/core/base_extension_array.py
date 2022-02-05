"""Implementation of base extension array class used in Arrowbic.
"""
from typing import Any, Iterable, Iterator, List, Optional, Sequence, Type, TypeVar, Union, overload

import pyarrow as pa

TItem = TypeVar("TItem")
TArray = TypeVar("TArray", bound="BaseExtensionArray[Any]")


class BaseExtensionArray(pa.ExtensionArray, Sequence[Optional[TItem]]):
    """Base extension array, adding interface to make simple operations easier."""

    @classmethod
    def __arrowbic_ext_type_class__(cls) -> Type[pa.ExtensionType]:
        """Arrowbic extension type class associated with the extension array."""
        raise NotImplementedError()

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

    def to_pylist(self) -> List[Optional[TItem]]:
        """Convert to a list of Python items."""
        return list(self)

    def tolist(self) -> List[Optional[TItem]]:
        """Convert to a list of Python items. Alias of `to_pylist`"""
        return self.to_pylist()

    @classmethod
    def from_iterator(
        cls: Type[TArray],
        it_items: Iterable[Optional[TItem]],
        /,
        *,
        size: Optional[int] = None,
        registry: Optional[Any] = None,
    ) -> TArray:
        """Build the extension array from a Python item iterator.

        Args:
            it_items: Items Python iterable.
            size: Optional size of the input iterable.
            registry: Optional registry where to find the extension type.
        Returns:
            Extension array, with the proper data.
        """
        from .base_extension_type import BaseExtensionType

        ext_type_cls: BaseExtensionType = cls.__arrowbic_ext_type_class__()  # type:ignore
        arr = ext_type_cls.__arrowbic_from_item_iterator__(it_items, size=size, registry=registry)
        return arr
