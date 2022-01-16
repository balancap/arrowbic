"""Implementation of base extension array class used in Arrowbic.
"""
import pyarrow as pa


class BaseExtensionArray(pa.ExtensionArray):
    """Base extension array, adding interface to make simple operations easier."""
