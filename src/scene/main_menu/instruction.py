import sdl2
import numpy as np
from src.color import Color
from src.scene.helper import get_ptr
from src.drawing_methods import (
    draw_rect_full,
    clear_background,
    draw_text,
    draw_sprite_sheet,
    Button,
    draw_rect_not_full,
    draw_sin_a
)


class InstructionWindow():
    def __init__(self, main_widow_width: int, main_widow_height: int, renderer, pixels: np.ndarray, font) -> None:
        self.m_width = main_widow_width
        self.m_height = main_widow_height
        self.pitch_background = self.m_width * 4
        self.renderer = renderer
        self.background = sdl2.SDL_CreateTexture(
            renderer,
            sdl2.SDL_PIXELFORMAT_ARGB8888,
            sdl2.SDL_TEXTUREACCESS_STREAMING,
            self.m_width,
            self.m_height
        )
        self.pixels = pixels
        self.font = font
        # self.btn_settings: list = [
        #     Button(self.renderer, self.pixels, self.font, int(self.width * 0.25), self.height // 3, 160, 50, Color.BLACK, Color.GREEN, self.next_scene, b"back"),
        # ]

    def clean_up(self) -> None:
        sdl2.SDL_DestroyTexture(self.background)
    
    def draw_instructions(self, time: float, bg: int) -> None:
        clear_background(self.pixels, bg)
        draw_sin_a(self.pixels, self.m_width, self.m_height, int(self.m_height * 0.5), 50, 0.01, 100, Color.ST_WHITE, time)
        draw_sin_a(self.pixels, self.m_width, self.m_height, int(self.m_height * 0.5), 50, -0.02, 60, Color.ST_WHITE, time)
        settings_background_x = self.m_width // 2
        settings_background_y = self.m_height // 2
        settings_pos_x = settings_background_x // 2
        settings_pos_y = settings_background_y // 2
        draw_rect_full(self.pixels, settings_background_x, settings_background_y, Color.BLACK, settings_pos_x, settings_pos_y)
        draw_rect_not_full(self.pixels, settings_background_x, settings_background_y, Color.WHITE, 5,settings_pos_x, settings_pos_y)
        pixel_ptr = get_ptr(self.pixels)
        sdl2.SDL_UpdateTexture(self.background, None, pixel_ptr, self.pitch_background)
        sdl2.SDL_RenderCopy(self.renderer, self.background, None, None)
