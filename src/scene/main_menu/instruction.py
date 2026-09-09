import ctypes
import sdl2
import sdl2.sdlttf as sttf
import numpy as np
from src.color import Color, color_to_sdl_color
from src.scene.helper import get_ptr
from src.drawing_methods import (
    draw_rect_full,
    clear_background,
    draw_rect_not_full,
    draw_sin_a,
    draw_line,
    draw_sprites
)
from src.image import Image
from src.print_logs import print_info
from typing import Any


class InstructionWindow:
    KONAMI_SEQUENCE = [
        "UP", "UP", "DOWN", "DOWN",
        "LEFT", "RIGHT", "LEFT", "RIGHT",
        "B", "A"
    ]

    MODIFIER_KEYS = {
        sdl2.SDLK_LSHIFT, sdl2.SDLK_RSHIFT,
        sdl2.SDLK_LCTRL, sdl2.SDLK_RCTRL,
        sdl2.SDLK_LALT, sdl2.SDLK_RALT,
        sdl2.SDLK_CAPSLOCK, sdl2.SDLK_NUMLOCKCLEAR,
    }

    def __init__(self, main_widow_width: int, main_widow_height: int,
                 renderer: sdl2.render.SDL_Renderer,
                 pixels: np.ndarray, font: ctypes.c_int,
                 on_close: Any = None | Any) -> None:
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
        self.hold_button_state = False

        self.show_cs: bool = False
        self.konami_code_entered: list = []

        font_path = b"assets/Press_Start_2P/PressStart2P-Regular.ttf"
        self.body_font_size = max(9, min(20, int(self.m_height * 0.019)))
        self.title_font_size = max(13, min(30, int(self.m_height * 0.027)))
        self.small_font_size = max(8, min(16, int(self.m_height * 0.015)))

        self.body_font = sttf.TTF_OpenFont(font_path, self.body_font_size)
        if not self.body_font:
            self.body_font = self.font

        self.title_font = sttf.TTF_OpenFont(font_path, self.title_font_size)
        if not self.title_font:
            self.title_font = self.font

        self.small_font = sttf.TTF_OpenFont(font_path, self.small_font_size)
        if not self.small_font:
            self.small_font = self.body_font

        self.pacman_img: Image | None = None
        self.bomba_img: Image | None = None
        try:
            self.pacman_img = Image(b"assets/pacman.png", renderer)
        except Exception:
            self.pacman_img = None
        try:
            self.bomba_img = Image(
                b"assets/3D_model/little_bomba.png", renderer
            )
        except Exception:
            self.bomba_img = None

    def clean_up(self) -> None:
        if self.background:
            sdl2.SDL_DestroyTexture(self.background)
            self.background = None

        if self.body_font and self.body_font != self.font:
            sttf.TTF_CloseFont(self.body_font)
            self.body_font = None

        if self.title_font and self.title_font != self.font:
            sttf.TTF_CloseFont(self.title_font)
            self.title_font = None

        if (self.small_font and self.small_font != self.font
                and self.small_font != self.body_font):
            sttf.TTF_CloseFont(self.small_font)
            self.small_font = None

        if self.pacman_img and hasattr(self.pacman_img, "texture"):
            if self.pacman_img.texture:
                sdl2.SDL_DestroyTexture(self.pacman_img.texture)
            self.pacman_img = None

        if self.bomba_img and hasattr(self.bomba_img, "texture"):
            if self.bomba_img.texture:
                sdl2.SDL_DestroyTexture(self.bomba_img.texture)
            self.bomba_img = None

    def reset(self) -> None:
        self.show_cs = False
        self.konami_code_entered.clear()

    def _feed_token(self, token: str) -> bool:
        self.konami_code_entered.append(token)
        if len(self.konami_code_entered) > len(self.KONAMI_SEQUENCE):
            self.konami_code_entered.pop(0)

        if self.konami_code_entered == self.KONAMI_SEQUENCE:
            self.show_cs = not self.show_cs
            self.konami_code_entered.clear()
            print_info(
                f"[Instructions] Konami Code accepted! show_cs={self.show_cs}"
            )
            return True
        return False

    def check_input(self, event: sdl2.events.SDL_Event | None = None) -> bool:
        """
        Check inputs to detect the complete Konami Code.
        Accepts an SDL_Event, int keycode, or str token.
        Returns True when the full Konami Code is completed.
        """
        if event is None:
            return False

        if isinstance(event, str):
            token = event.upper().strip()
            return self._feed_token(token)

        sym = None
        scancode = None
        if hasattr(event, "type"):
            if event.type != sdl2.SDL_KEYDOWN:
                return False
            if getattr(event.key, "repeat", 0) != 0:
                return False
            sym = getattr(event.key.keysym, "sym", None)
            scancode = getattr(event.key.keysym, "scancode", None)
        elif isinstance(event, int):
            sym = event

        if sym in self.MODIFIER_KEYS:
            return False

        if (sym in (sdl2.SDLK_UP, sdl2.SDLK_KP_8)
                or scancode in (sdl2.SDL_SCANCODE_UP,
                                sdl2.SDL_SCANCODE_KP_8)):
            token = "UP"
        elif (sym in (sdl2.SDLK_DOWN, sdl2.SDLK_KP_2)
                or scancode in (sdl2.SDL_SCANCODE_DOWN,
                                sdl2.SDL_SCANCODE_KP_2)):
            token = "DOWN"
        elif (sym in (sdl2.SDLK_LEFT, sdl2.SDLK_KP_4)
                or scancode in (sdl2.SDL_SCANCODE_LEFT,
                                sdl2.SDL_SCANCODE_KP_4)):
            token = "LEFT"
        elif (sym in (sdl2.SDLK_RIGHT, sdl2.SDLK_KP_6)
                or scancode in (sdl2.SDL_SCANCODE_RIGHT,
                                sdl2.SDL_SCANCODE_KP_6)):
            token = "RIGHT"
        elif (sym in (sdl2.SDLK_b, ord("b"), ord("B"))
                or scancode == sdl2.SDL_SCANCODE_B):
            token = "B"
        elif (sym in (sdl2.SDLK_a, ord("a"), ord("A"))
                or scancode in (sdl2.SDL_SCANCODE_A, sdl2.SDL_SCANCODE_Q)):
            token = "A"
        else:
            token = "MISMATCH"

        return self._feed_token(token)

    def check_inputs(self, event: sdl2.events.SDL_Event | None = None) -> bool:
        return self.check_input(event)

    def handle_event(self, event: sdl2.events.SDL_Event | None = None) -> bool:
        return self.check_input(event)

    def _draw_text_line(self, font, text: str, x: int, y: int,
                        color: Color, scale: int = 1) -> int:
        if not text or not text.strip():
            return 16 * scale
        text_bytes = text.encode("utf-8")
        sdl_col = color_to_sdl_color(color)
        surface = sttf.TTF_RenderUTF8_Solid(font, text_bytes, sdl_col)
        if not surface:
            return 16 * scale
        line_w = surface.contents.w
        line_h = surface.contents.h
        texture = sdl2.SDL_CreateTextureFromSurface(self.renderer, surface)
        sdl2.SDL_FreeSurface(surface)
        if texture:
            dest_rect = sdl2.SDL_Rect(
                x, y, line_w * scale, line_h * scale
            )
            sdl2.SDL_RenderCopy(
                self.renderer, texture, None, ctypes.byref(dest_rect)
            )
            sdl2.SDL_DestroyTexture(texture)
        return line_h * scale

    def _draw_centered_line(self, font, text: str, y: int, box_x: int,
                            box_w: int, color: Color,
                            scale: int = 1) -> int:
        if not text or not text.strip():
            return 16 * scale
        w_val, h_val = ctypes.c_int(0), ctypes.c_int(0)
        sttf.TTF_SizeUTF8(
            font, text.encode("utf-8"),
            ctypes.byref(w_val), ctypes.byref(h_val)
        )
        x = box_x + max(10, (box_w - w_val.value * scale) // 2)
        return self._draw_text_line(font, text, x, y, color, scale)

    def _draw_pacman_instructions(self, box_x: int, box_y: int,
                                  box_w: int, box_h: int) -> None:
        curr_y = box_y + int(box_h * 0.05)
        step = max(13, int(box_h * 0.04))

        title = "=== PAC-MAN INSTRUCTIONS ==="
        self._draw_centered_line(
            self.title_font, title, curr_y, box_x, box_w, Color.YELLOW
        )
        if self.pacman_img and self.pacman_img.texture:
            w_val, _ = ctypes.c_int(0), ctypes.c_int(0)
            sttf.TTF_SizeUTF8(
                self.title_font, title.encode("utf-8"),
                ctypes.byref(w_val), ctypes.byref(_)
            )
            icon_x = box_x + (box_w - w_val.value) // 2 - 36
            if icon_x > box_x + 10:
                draw_sprites(
                    self.renderer, self.pacman_img,
                    icon_x, curr_y - 2, 28 / max(1, self.pacman_img.width)
                )

        curr_y += step + 2
        self._draw_centered_line(
            self.small_font,
            "Eat all pac-dots and escape the ghosts!",
            curr_y, box_x, box_w, Color.WHITE
        )

        curr_y += step + 8
        left_margin = box_x + int(box_w * 0.05)

        self._draw_text_line(
            self.title_font, "-- CONTROLS --",
            left_margin, curr_y, Color.CYAN
        )
        curr_y += step

        self._draw_text_line(
            self.body_font,
            "[ARROWS] / [WASD] : Move Pac-Man",
            left_margin + 12, curr_y, Color.WHITE
        )
        curr_y += step

        self._draw_text_line(
            self.body_font,
            "[ESCAPE]          : Pause / Return to main menu",
            left_margin + 12, curr_y, Color.WHITE
        )
        curr_y += step + 8

        self._draw_text_line(
            self.title_font, "-- GAME RULES --",
            left_margin, curr_y, Color.CYAN
        )
        curr_y += step

        self._draw_text_line(
            self.body_font,
            "* Eat all pac-dots in the maze to clear the level.",
            left_margin + 12, curr_y, Color.WHITE
        )
        curr_y += step

        self._draw_text_line(
            self.body_font,
            "* Avoid the 4 ghosts: touching one costs 1 life!",
            left_margin + 12, curr_y, Color.WHITE
        )
        curr_y += step

        self._draw_text_line(
            self.body_font,
            "* You start the game with 3 lives.",
            left_margin + 12, curr_y, Color.WHITE
        )
        curr_y += step

        self._draw_text_line(
            self.body_font,
            "* Watch the timer: finish before the countdown ends!",
            left_margin + 12, curr_y, Color.WHITE
        )
        curr_y += step + 8

        self._draw_text_line(
            self.title_font, "-- ITEMS & GHOSTS --",
            left_margin, curr_y, Color.CYAN
        )
        curr_y += step

        self._draw_text_line(
            self.body_font,
            "* PAC-DOT       : +10 pts. Collect them all!",
            left_margin + 12, curr_y, Color.WHITE
        )
        curr_y += step

        self._draw_text_line(
            self.body_font,
            "* POWER PELLET  : +50 pts. Ghosts turn blue & vulnerable.",
            left_margin + 12, curr_y, Color.YELLOW
        )
        curr_y += step

        self._draw_text_line(
            self.body_font,
            "* EATEN GHOST   : +200 pts while in frightened mode!",
            left_margin + 12, curr_y, Color.GREEN
        )
        curr_y += step

        self._draw_text_line(
            self.body_font,
            "* GHOSTS        : Blinky(Red) Pinky(Pink) Inky(Cyan) Clyde",
            left_margin + 12, curr_y, Color.WHITE
        )

    def _draw_cs_instructions(self, box_x: int, box_y: int,
                              box_w: int, box_h: int) -> None:
        curr_y = box_y + int(box_h * 0.05)
        step = max(13, int(box_h * 0.04))

        title = "=== PAC-MAN: GLOBAL OFFENSIVE ==="
        self._draw_centered_line(
            self.title_font, title, curr_y, box_x, box_w, Color.GOLD
        )
        if self.bomba_img and self.bomba_img.texture:
            w_val, _ = ctypes.c_int(0), ctypes.c_int(0)
            sttf.TTF_SizeUTF8(
                self.title_font, title.encode("utf-8"),
                ctypes.byref(w_val), ctypes.byref(_)
            )
            icon_x = box_x + (box_w - w_val.value) // 2 - 36
            if icon_x > box_x + 10:
                draw_sprites(
                    self.renderer, self.bomba_img,
                    icon_x, curr_y - 2, 28 / max(1, self.bomba_img.width)
                )

        curr_y += step + 2
        self._draw_centered_line(
            self.small_font,
            "Counter-Terrorist Tactical Mission",
            curr_y, box_x, box_w, Color.WHITE
        )

        curr_y += step + 8
        left_margin = box_x + int(box_w * 0.05)

        self._draw_text_line(
            self.title_font, "-- CONTROLS --",
            left_margin, curr_y, Color.CYAN
        )
        curr_y += step

        self._draw_text_line(
            self.body_font,
            "[WASD] / [ZQSD] : Move (Forward, Backward, Strafe)",
            left_margin + 12, curr_y, Color.WHITE
        )
        curr_y += step

        self._draw_text_line(
            self.body_font,
            "[MOUSE]         : Aim (camera follows crosshair)",
            left_margin + 12, curr_y, Color.WHITE
        )
        curr_y += step

        self._draw_text_line(
            self.body_font,
            "[LEFT CLICK]    : Shoot at terrorists",
            left_margin + 12, curr_y, Color.WHITE
        )
        curr_y += step

        self._draw_text_line(
            self.body_font,
            "[KEY E]         : Hold 5s near the bomb to defuse",
            left_margin + 12, curr_y, Color.WHITE
        )
        curr_y += step

        self._draw_text_line(
            self.body_font,
            "[ESCAPE]        : Return to game",
            left_margin + 12, curr_y, Color.WHITE
        )
        curr_y += step + 8

        self._draw_text_line(
            self.title_font, "-- MISSION OBJECTIVES --",
            left_margin, curr_y, Color.CYAN
        )
        curr_y += step

        self._draw_text_line(
            self.body_font,
            "* Play as the Counter-Terrorist (CT) operative.",
            left_margin + 12, curr_y, Color.WHITE
        )
        curr_y += step

        self._draw_text_line(
            self.body_font,
            "* Reach the bomb site and defuse the C4!",
            left_margin + 12, curr_y, Color.WHITE
        )
        curr_y += step

        self._draw_text_line(
            self.body_font,
            "* Eliminate all enemy terrorists on your way.",
            left_margin + 12, curr_y, Color.WHITE
        )
        curr_y += step

        self._draw_text_line(
            self.body_font,
            "* Round timer: 49s (4s freeze time at round start).",
            left_margin + 12, curr_y, Color.WHITE
        )
        curr_y += step + 8

        self._draw_text_line(
            self.title_font, "-- VICTORY CONDITIONS --",
            left_margin, curr_y, Color.CYAN
        )
        curr_y += step

        self._draw_text_line(
            self.body_font,
            "* Defuse the C4 bomb before it explodes = Round won!",
            left_margin + 12, curr_y, Color.GREEN
        )
        curr_y += step

    def draw_instructions(self, time: float, bg: int) -> None:
        clear_background(self.pixels, bg)
        draw_sin_a(
            self.pixels, self.m_width, self.m_height,
            int(self.m_height * 0.5), 50, 0.01, 100,
            Color.ST_WHITE, time
        )
        draw_sin_a(
            self.pixels, self.m_width, self.m_height,
            int(self.m_height * 0.5), 50, -0.02, 60,
            Color.ST_WHITE, time
        )

        box_w = min(int(self.m_width * 0.84), self.m_width - 40)
        box_h = min(int(self.m_height * 0.86), self.m_height - 40)
        box_x = (self.m_width - box_w) // 2
        box_y = (self.m_height - box_h) // 2

        draw_rect_full(self.pixels, box_w, box_h, Color.BLACK, box_x, box_y)

        border_col = Color.GOLD if self.show_cs else Color.WHITE
        draw_rect_not_full(
            self.pixels, box_w, box_h, border_col, 5, box_x, box_y
        )

        close_x = box_x + box_w - 25
        close_y = box_y + 25

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
                self.reset()
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
            close_x - radius, close_y - radius,
            close_x + radius, close_y + radius,
            cross_color, thickness
        )
        draw_line(
            self.pixels,
            close_x - radius, close_y + radius,
            close_x + radius, close_y - radius,
            cross_color, thickness
        )

        pixel_ptr = get_ptr(self.pixels)
        sdl2.SDL_UpdateTexture(
            self.background, None, pixel_ptr, self.pitch_background
        )
        sdl2.SDL_RenderCopy(self.renderer, self.background, None, None)

        if self.show_cs:
            self._draw_cs_instructions(box_x, box_y, box_w, box_h)
        else:
            self._draw_pacman_instructions(box_x, box_y, box_w, box_h)
