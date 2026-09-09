import ctypes
from numpy import ndarray


class Vector2:
    """Represent a 2D integer coordinate vector."""

    def __init__(self, x: int = 0, y: int = 0) -> None:
        """Initialize 2D vector coordinates.

        Args:
            x: Horizontal coordinate.
            y: Vertical coordinate.
        """
        self.x: int = x
        self.y: int = y


def get_ptr(pixel_tab: ndarray) -> ctypes.c_void_p:
    """Return a ctypes void pointer to a numpy array buffer.

    Args:
        pixel_tab: Numpy array holding pixel data.

    Returns:
        ctypes.c_void_p: Pointer to the underlying memory buffer.
    """
    return ctypes.cast(pixel_tab.ctypes.data, ctypes.c_void_p)
