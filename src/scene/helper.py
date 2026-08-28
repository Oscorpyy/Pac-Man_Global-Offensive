import ctypes
from numpy import ndarray

class Vector2:
    def __init__(self) -> None:
        self.x: int = 0
        self.y: int = 0

def get_ptr(pixel_tab: ndarray) -> ctypes.c_void_p:
    return ctypes.cast(pixel_tab.ctypes.data, ctypes.c_void_p)
