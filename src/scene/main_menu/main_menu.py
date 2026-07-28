import sdl2
from src.drawing_methods import draw_rect_full, clear_background
from src.scene.helper import get_ptr
import numpy as np

class MainMenu:
    def __init__(self, renderer, width: int, height: int) -> None:
        self.renderer = renderer
        self.width = width
        self.background = sdl2.SDL_CreateTexture(
            renderer,
            sdl2.SDL_PIXELFORMAT_ARGB8888,
            sdl2.SDL_TEXTUREACCESS_STREAMING,
            width,
            height
        )
        self.test_x: int = 10
        self.pixels = np.zeros((height, width), dtype=np.uint32)
        self.pitch_background = width * 4
        self.blue = 0xFF0000FF
        self.red = 0xFFFF0000


    def draw_background(self) -> None:
        clear_background(self.pixels, self.blue)
        draw_rect_full(self.pixels, 15, 15, self.red, x=self.test_x, y=0)
        pixel_ptr = get_ptr(self.pixels)
        sdl2.SDL_UpdateTexture(self.background, None, pixel_ptr, self.pitch_background)
        sdl2.SDL_RenderCopy(self.renderer, self.background, None, None)
        sdl2.SDL_RenderPresent(self.renderer)
        self.test_x += 10
        if self.test_x >= self.width:
            self.test_x = 10


    def draw_main_menu(self) -> None:
        self.draw_background()
