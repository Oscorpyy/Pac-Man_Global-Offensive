import ctypes
from numpy import ndarray

class Vector2:
    def __init__(self, x: int = 0, y: int = 0) -> None:
        self.x: int = x
        self.y: int = y

def get_ptr(pixel_tab: ndarray) -> ctypes.c_void_p:
    return ctypes.cast(pixel_tab.ctypes.data, ctypes.c_void_p)
