import sdl2
import ctypes
from src.drawing_methods import put_pixels, draw_rect_full

class MainMenu:
    def __init__(self, renderer, width: int, height: int) -> None:
        self.renderer = renderer
        self.background = sdl2.SDL_CreateTexture(
            renderer,
            sdl2.SDL_PIXELFORMAT_ARGB8888,
            sdl2.SDL_TEXTUREACCESS_STREAMING,
            width,
            height
        )
        self.pixel_array_type = ctypes.c_uint32 * (width * height)
        self.pixels = self.pixel_array_type()
        blue = 0xFF0000FF
        red = 0xFFFF0000
        draw_rect_full(self.pixels, width, height, width, height, blue)
        draw_rect_full(self.pixels, width, height, 50, 60, red, start_y=15, start_x=45)
        put_pixels(self.pixels, 100, 50, width, height, red)
        self.pitch_background = width * ctypes.sizeof(ctypes.c_uint32)

    def draw_background(self) -> None:
        sdl2.SDL_UpdateTexture(self.background, None, self.pixels, self.pitch_background)
        sdl2.SDL_RenderCopy(self.renderer, self.background, None, None)
        sdl2.SDL_RenderPresent(self.renderer)
