import os
import json
import sdl2
import sdl2.sdlimage as sdim
import sdl2.sdlttf as sttf
import numpy as np
from src.color import Color
from src.drawing_methods import (
    draw_rect_full,
    clear_background,
    draw_text,
    draw_sprite_sheet,
    Button,
    draw_rect_not_full
)
from src.scene.helper import get_ptr
from src.print_logs import print_error
from src.game_state import GameConfig, GameState, ScenePossible


class SettingsWindow:
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
    
    def draw_settings(self) -> None:
        clear_background(self.pixels, Color.NAVY)
        settings_background_x = self.m_width // 2
        settings_background_y = self.m_height // 2
        settings_pos_x = settings_background_x // 2
        settings_pos_y = settings_background_y // 2
        draw_rect_full(self.pixels, settings_background_x, settings_background_y, Color.BLACK, settings_pos_x, settings_pos_y)
        draw_rect_not_full(self.pixels, settings_background_x, settings_background_y, Color.WHITE, 5,settings_pos_x, settings_pos_y)
        pixel_ptr = get_ptr(self.pixels)
        sdl2.SDL_UpdateTexture(self.background, None, pixel_ptr, self.pitch_background)
        sdl2.SDL_RenderCopy(self.renderer, self.background, None, None)


class MainMenu:
    def __init__(self, renderer, width: int, height: int, game_state: GameState, game_config: GameConfig) -> None:
        self.game_state = game_state
        self.game_config = game_config
        self.renderer = renderer
        self.top_score = self.get_highscore()
        # img loading
        sdim.IMG_Init(sdim.IMG_INIT_PNG)
        self.img_path = b"assets/test3.png"
        self.img_surface = sdim.IMG_Load(self.img_path)
        if not self.img_surface:
            print_error(f"can't charge image {sdim.IMG_GetError()}")
        self.img_texture = sdl2.SDL_CreateTextureFromSurface(self.renderer, self.img_surface)
        sdl2.SDL_FreeSurface(self.img_surface)
        # Font loading
        sttf.TTF_Init()
        self.font_size = 16
        self.font = sttf.TTF_OpenFont(b"assets/Press_Start_2P/PressStart2P-Regular.ttf", self.font_size)
        if not self.font:
            print_error(f"can't charge font {sttf.TTF_GetError()}")
        self.width = width
        self.height = height
        self.pixels = np.zeros((height, width), dtype=np.uint32)
        self.settings_win = SettingsWindow(width, height, renderer, self.pixels, self.font)
        self.background = sdl2.SDL_CreateTexture(
            renderer,
            sdl2.SDL_PIXELFORMAT_ARGB8888,
            sdl2.SDL_TEXTUREACCESS_STREAMING,
            width,
            height
        )
        self.btn_list: list = [
            Button(self.renderer, self.pixels, self.font, int(self.width * 0.25), self.height // 3, 160, 50, Color.BLACK, Color.GREEN, self.next_scene, b"Start Game"),
            Button(self.renderer, self.pixels, self.font, int(self.width * 0.55), self.height // 3, 160, 50, Color.BLACK, Color.GREEN, self.set_can_draw_settings, b"Settings")
        ]
        self.pitch_background = width * 4
        self.can_draw_settings: bool = False


    def get_highscore(self) -> dict:
        content: dict = {}
        try:
            with open(self.game_config.highscore_filename, "r") as f:
                content = json.load(f)
        except (FileNotFoundError, PermissionError, ValueError) as e:
            print_error(f"Caught error: {e}")
        return content


    def clean_up(self) -> None:
        sdim.IMG_Quit()
        sttf.TTF_CloseFont(self.font)
        sttf.TTF_Quit()
        sdl2.SDL_DestroyTexture(self.img_texture)
        sdl2.SDL_DestroyTexture(self.background)
        self.settings_win.clean_up()


    def next_scene(self) -> None:
        self.game_state.scene = ScenePossible.GAME


    def draw_scores(self) -> None:
        scores_lst = self.top_score.get("scores", None)
        if scores_lst is not None:
            scores_lst.sort(key=lambda item: item['point'], reverse=True)
        draw_text(self.renderer, self.font, b"HIGHSCORE", int(self.width * 0.4), 275)
        y_offset: int = 300
        if scores_lst is not None:
            if len(scores_lst) == 0:
                draw_text(self.renderer, self.font, b"HIGHSCORE", int(self.width * 0.4), 275)
            else:
                i = 0
                for stat in scores_lst:
                    if i > 9:
                        continue
                    txt: str = f"{stat.get("name")}: {stat.get("point")}".encode("utf-8")
                    draw_text(self.renderer, self.font, txt, int(self.width * 0.35), y_offset)
                    y_offset += 30
                    i += 1


    def set_can_draw_settings(self) -> None:
        if self.can_draw_settings is False:
            self.can_draw_settings = True


    def draw_background(self) -> None:
        clear_background(self.pixels, Color.NAVY)
        for btn in self.btn_list:
            btn.draw_background()
        pixel_ptr = get_ptr(self.pixels)
        sdl2.SDL_UpdateTexture(self.background, None, pixel_ptr, self.pitch_background)
        sdl2.SDL_RenderCopy(self.renderer, self.background, None, None)
        # draw_sprites(self.renderer, self.img_texture, 50, 45, 10)
        draw_sprite_sheet(self.renderer, self.img_texture, 50, 45, 0, 4)
        for btn in self.btn_list:
            btn.draw_text()
        self.draw_scores()


    def draw_main_menu(self) -> None:
        if self.can_draw_settings is True:
            self.settings_win.draw_settings()
        else:
            self.draw_background()
        sdl2.SDL_RenderPresent(self.renderer)
        if self.game_state.scene != ScenePossible.MAIN:
            self.clean_up()
