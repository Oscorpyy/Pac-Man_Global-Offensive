import ctypes
import sdl2
import numpy as np
from src.color import Color
from src.scene.helper import get_ptr
from src.image import Image
from src.drawing_methods import (
    draw_rect_full,
    clear_background,
    draw_sin_a,
    draw_rect_not_full,
    draw_line
)


class SettingsWindow:
    def __init__(self, main_widow_width: int, main_widow_height: int,
                 renderer, pixels: np.ndarray, font,
                 on_close=None) -> None:
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
        self.on_close = on_close
        self.settings_img = Image(b"assets/settings.png", renderer)
        self.hold_button_state = False

    def clean_up(self) -> None:
        sdl2.SDL_DestroyTexture(self.background)
        if hasattr(self, 'settings_img') and self.settings_img:
            sdl2.SDL_DestroyTexture(self.settings_img.texture)

    def draw_settings(self, time: float, bg: int) -> None:
        clear_background(self.pixels, bg)
        draw_sin_a(self.pixels, self.m_width, self.m_height, int(
            self.m_height * 0.5), 50, 0.01, 100, Color.ST_WHITE, time)
        draw_sin_a(self.pixels, self.m_width, self.m_height, int(
            self.m_height * 0.5), 50, -0.02, 60, Color.ST_WHITE, time)
        settings_background_x = self.m_width // 2
        settings_background_y = self.m_height // 2
        settings_pos_x = settings_background_x // 2
        settings_pos_y = settings_background_y // 2
        draw_rect_full(self.pixels, settings_background_x,
                       settings_background_y, Color.BLACK, settings_pos_x,
                       settings_pos_y)
        draw_rect_not_full(self.pixels, settings_background_x,
                           settings_background_y, Color.WHITE, 5,
                           settings_pos_x, settings_pos_y)

        close_x = settings_pos_x + settings_background_x - 25
        close_y = settings_pos_y + 25

        radius = 8
        thickness = 2
        hit_margin = 15

        mouse_x = ctypes.c_int(0)
        mouse_y = ctypes.c_int(0)
        button_state = sdl2.mouse.SDL_GetMouseState(
            ctypes.byref(mouse_x), ctypes.byref(mouse_y)
        )

        is_hovered = (
            (close_x - hit_margin <= mouse_x.value <= close_x + hit_margin)
            and (close_y - hit_margin <= mouse_y.value <= close_y + hit_margin)
        )

        if is_hovered:
            cross_color = Color.RED
            if ((button_state & 1 or button_state == 1)
                    and not self.hold_button_state):
                if self.on_close is not None:
                    self.on_close()
                self.hold_button_state = True
            elif button_state == 0 and self.hold_button_state:
                self.hold_button_state = False
        else:
            cross_color = Color.WHITE
            if button_state == 0:
                self.hold_button_state = False

        draw_line(
            self.pixels,
            close_x - radius,
            close_y - radius,
            close_x + radius,
            close_y + radius,
            cross_color,
            thickness
        )

        draw_line(
            self.pixels,
            close_x - radius,
            close_y + radius,
            close_x + radius,
            close_y - radius,
            cross_color,
            thickness
        )
        pixel_ptr = get_ptr(self.pixels)
        sdl2.SDL_UpdateTexture(
            self.background,
            None,
            pixel_ptr,
            self.pitch_background
        )
        sdl2.SDL_RenderCopy(self.renderer, self.background, None, None)

        max_w = settings_background_x - 40
        max_h = settings_background_y - 65
        if (max_w > 0 and max_h > 0
                and self.settings_img.width > 0
                and self.settings_img.height > 0):
            scale_w = max_w / self.settings_img.width
            scale_h = max_h / self.settings_img.height
            scale = min(scale_w, scale_h)
            img_w = int(self.settings_img.width * scale)
            img_h = int(self.settings_img.height * scale)
            img_x = settings_pos_x + (settings_background_x - img_w) // 2
            img_y = (settings_pos_y + 40
                     + ((settings_background_y - 45 - img_h) // 2))
            dest_rect = sdl2.SDL_Rect(img_x, img_y, img_w, img_h)
            sdl2.SDL_RenderCopy(
                self.renderer, self.settings_img.texture,
                None, ctypes.byref(dest_rect)
            )
