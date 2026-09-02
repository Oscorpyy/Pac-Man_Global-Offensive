import os
import math
import json
import sdl2
import sdl2.sdlimage as sdim
import sdl2.sdlttf as sttf
import numpy as np
from src.color import Color
from src.drawing_methods import (
    draw_fps,
    clear_background,
    draw_sin_a,
    draw_text,
    draw_sprites,
    Button,
)
from src.scene.helper import get_ptr
from src.print_logs import print_error
from src.game_state import GameConfig, GameState, ScenePossible
from src.scene.main_menu.settings import SettingsWindow
from src.scene.main_menu.instruction import InstructionWindow
from src.image import Image
from src.transition import Transition


class MenuDrawingState:
    def __init__(self) -> None:
        self.state_lst: list = ["main", "instruction", "settings"]
        self.current = self.state_lst[0]


class MainMenu:
    def __init__(self, renderer, game_state: GameState, game_config: GameConfig, transition: Transition) -> None:
        self.game_state = game_state
        self.menu_state = MenuDrawingState()
        self.game_config = game_config
        self.renderer = renderer
        self.top_score = self.get_highscore()
        self.scores = self.top_score.get("scores", None)
        if self.scores is not None:
            self.scores.sort(key=lambda item: item['point'], reverse=True)
        # img loading
        sdim.IMG_Init(sdim.IMG_INIT_PNG)
        self.logo =  Image(b"assets/game_logo.png", renderer)
        # Font loading
        sttf.TTF_Init()
        self.font_size: int = 16
        self.font = sttf.TTF_OpenFont(b"assets/Press_Start_2P/PressStart2P-Regular.ttf", self.font_size)
        if not self.font:
            print_error(f"can't charge font {sttf.TTF_GetError()}")
        self.width: int = self.game_config.screen_width
        self.height: int = self.game_config.screen_height
        self.pixels = np.zeros((self.height, self.width), dtype=np.uint32)
        self.settings_win = SettingsWindow(
            self.width, self.height, renderer, self.pixels, self.font,
            on_close=self.set_can_draw_main
        )
        self.instruction_win = InstructionWindow(
            self.width, self.height, renderer, self.pixels, self.font,
            on_close=self.set_can_draw_main
        )
        self.transition = transition
        self.background = sdl2.SDL_CreateTexture(
            renderer,
            sdl2.SDL_PIXELFORMAT_ARGB8888,
            sdl2.SDL_TEXTUREACCESS_STREAMING,
            self.width,
            self.height
        )
        btn_width = 200
        self.btn_list: list = [
            Button(self.renderer, self.pixels,
                   self.font, (self.width // 2 - (btn_width // 2)),
                   self.height // 3, btn_width, 50, Color.GRAY, Color.WHITE,
                   self.next_scene, b"Start Game"),
            Button(self.renderer, self.pixels,
                   self.font, (self.width // 2 - (btn_width // 2)) - (
                    btn_width + 32), self.height // 3, btn_width, 50,
                   Color.GRAY, Color.WHITE, self.set_can_draw_settings,
                   b"Settings"),
            Button(self.renderer, self.pixels,
                   self.font, (self.width // 2 - (btn_width // 2)) + (
                    btn_width + 32), self.height // 3, btn_width, 50,
                   Color.GRAY, Color.WHITE, self.set_can_draw_instructions,
                   b"Instructions"),
            Button(self.renderer, self.pixels,
                   self.font, self.game_config.screen_width - 105,
                   5, 100, 50,
                   Color.WHITE, Color.RED,
                   self.close_game, b"Exit")
        ]
        self.pitch_background = self.width * 4
        self.time: float = 0.0
        self.background_color = 0xFF0000FF

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
        sdl2.SDL_DestroyTexture(self.logo.texture)
        sdl2.SDL_DestroyTexture(self.background)
        self.settings_win.clean_up()
        self.instruction_win.clean_up()


    def next_scene(self) -> None:
        self.transition.scene_to_put = ScenePossible.GAME
        self.transition.transition_on = True
        self.transition.img = True


    def draw_scores(self) -> None:
        scores = self.scores
        draw_text(self.renderer, self.font, b"HIGHSCORE", self.width // 2 - (len("HIGHSCORE") * 16 // 2), self.height // 2, Color.WHITE)
        y_offset: int = self.height // 2 + 30
        if scores is not None:
            if len(scores) == 0:
                draw_text(self.renderer, self.font, b"HIGHSCORE", self.width // 2 - (len("HIGHSCORE") * 16 // 2), self.height // 2, Color.WHITE)
            else:
                i = 0
                for stat in scores:
                    if i > 9:
                        continue
                    txt: str = f"{stat.get("name")}: {stat.get("point")}".encode("utf-8")
                    draw_text(self.renderer, self.font, txt, self.width // 2 - (len(txt) * 16 // 2), y_offset, Color.WHITE)
                    y_offset += 30
                    i += 1

    def set_can_draw_main(self) -> None:
        self.menu_state.current = self.menu_state.state_lst[0]

    def set_can_draw_settings(self) -> None:
        self.menu_state.current = self.menu_state.state_lst[2]

    def set_can_draw_instructions(self) -> None:
        self.menu_state.current = self.menu_state.state_lst[1]

    def close_game(self) -> None:
        self.game_state.is_running = False

    def draw_background(self) -> None:
        clear_background(self.pixels, self.get_rainbow_color(self.time * 0.2))
        draw_sin_a(self.pixels, self.width, self.height, int(self.height * 0.5), 50, 0.01, 100, Color.ST_WHITE, self.time)
        draw_sin_a(self.pixels, self.width, self.height, int(self.height * 0.5), 50, -0.02, 60, Color.ST_WHITE, self.time)
        for btn in self.btn_list:
            btn.draw_background()
        pixel_ptr = get_ptr(self.pixels)
        sdl2.SDL_UpdateTexture(self.background, None, pixel_ptr, self.pitch_background)
        sdl2.SDL_RenderCopy(self.renderer, self.background, None, None)
        draw_sprites(self.renderer, self.logo, ((self.width // 2) - (self.logo.width * 5 // 2)), 0, 5)
        for btn in self.btn_list:
            btn.draw_text(Color.BLACK)
        self.draw_scores()

    def get_rainbow_color(self, time_var: float) -> int:
        center = 100
        amp = 40
        r = int(center + amp * math.sin(time_var))
        g = int(center + amp * math.sin(time_var + 2))
        b = int(center + amp * math.sin(time_var + 4))
        return (0xFF << 24) | (r << 16) | (g << 8) | b

    def draw_main_menu(self) -> None:
        if self.menu_state.current == self.menu_state.state_lst[2]:
            self.settings_win.draw_settings(self.time, self.get_rainbow_color(self.time * 0.2))
        elif self.menu_state.current == self.menu_state.state_lst[1]:
            self.instruction_win.draw_instructions(self.time, self.get_rainbow_color(self.time * 0.2))
        elif self.menu_state.current == self.menu_state.state_lst[0]:
            self.draw_background()
        draw_fps(self.renderer, self.font, self.game_state.fps)
        if self.game_state.scene != ScenePossible.MAIN:
            self.clean_up()
        self.time += 0.1
