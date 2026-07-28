import ctypes
from numpy import ndarray

def get_ptr(pixel_tab: ndarray) -> ctypes.c_void_p:
    return ctypes.cast(pixel_tab.ctypes.data, ctypes.c_void_p)
