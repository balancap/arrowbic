# Arrowbic technical design

*Arrowbic* is built on top of *PyArrow* extension types, extending the standard API defined in the later.
Every extension type registered in the library must follow the following minimal interface:

```python
import pyarrow as pa
import arrowbic


class MyExtensionArray(arrowbic.BaseExtensionArray):
    """A custom extension array allows to implement custom interface, improving the usability of the
    extension array in common Python code.

    The `BaseExtensionArray` is already extending the `ExtensionArray` API from PyArrow, adding common
    methods to filter, ...
    """


@arrowbic.register_extension_type
class MyExtensionType(arrowbic.BaseExtensionType):
    def __init__(self, storage_type: pa.DataType = None, item_pyclass: Type[Any] = None, extension_array_cls: pa.ExtensionArray = MyExtensionArray):
        """Constructor of an extension type instance.

        The default constructor with no arguments should also return the same default extension type instance, used
        for registering in PyArrow. Other instances with non-none arguments are cached by Arrowbic internally, such
        that PyArrow/Arrowbic does not constantly re-deserialize them.

        Args:
            storage_type: Storage type to use for this instance.
            item_pyclass: Item Python class to associate with the extension type.
            extension_array_cls: Extension array class.
        """
        pass

    def __arrowbic_ext_metadata__(self) -> Dict[str, Any]:
        """Extract the metadata of the extension type.

        Returns:
            Extension type metadata dictionary.
        """
        return super().__arrowbic_ext_metadata__()

    @classmethod
    def __arrowbic_priority__(cls) -> int:
        """Defines the ordering in the Arrowbic registry, used for finding the extension type
        matching a Python class.

        Returns:
            Integer priority, used in the registry ordering. Zero by default.
        """
        return 0

    @classmethod
    def __arrowbic_is_item_pyclass_supported__(cls, item_pyclass: Type[Any]) -> bool:
        """Is the extension type supporting/compatible with an item Python class?

        Args:
            item_pyclass: Item Python class.
        Returns:
            Is the class supported by the extension type?
        """
        raise NotImplementedError()

    @classmethod
    def __arrowbic_make_item_pyclass__(cls, storage_type: pa.DataType, ext_metadata: Dict[str, Any]) -> Type[Any]:
        """Generate the Python item class from the Arrow storage type and extension metadata.

        Args:
            storage_type: Storage type used.
            ext_metadata: Extension metadata.
        Returns:
            Generated Python item class compatible with the storage type and metadata.
        """
        raise NotImplementedError()

    def __arrowbic_from_item_iterator__(self, it_items: Iterator[Any]) -> pa.ExtensionArray:
        """Build the extension array from a Python item iterator.

        Args:
            it_items: Items Python iterator.
        Returns:
            Extension array, with the proper data.
        """
        raise NotImplementedError()
```

The additional interface is required for *Arrowbic* to provide these functionalities:
* Generic `arrowbic.array` factory method: this method must be able to associate a Python class to extension type in order to build the adequate array. Then, the extension type must know how to build in practice the extension array from a collection of Python items;
* Deserialize *Arrowbic* arrays serialized by a different module or/and service. It is fairly common for data to be serialized, either in file format or raw IPC format, and then deserialize in a service/program which was no knowledge of the item Python classes registered and used in the first place. Hence, *Arrowbic* extension type are required to be able to re-generate a valid Python item class from the Arrow storage type and the extension metadata;
