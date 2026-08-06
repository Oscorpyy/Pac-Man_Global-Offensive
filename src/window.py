from typing import Any

import sdl2
import json
from src.scene.game.CS.secret_game import SecretGame
from src.print_logs import print_error, print_info, print_warning
from src.control import SdlEvent
from src.game_state import GameState, ScenePossible, GameConfig
from src.scene.main_menu.main_menu import MainMenu
from src.scene.game.game import Game
from src.camera import Camera


class Window:
    def __init__(self, config: GameConfig) -> None:
        self.config = config
        self.width = 800
        self.height = 600

    def init_window(self) -> int:
        if sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO) != 0:
            print_error(f"initialisation error with SDL {sdl2.SDL_GetError()}")
            return -1
        return 0

    def create_window(self) -> sdl2.SDL_Window | int:
        window = sdl2.SDL_CreateWindow(
                b"Pac-Man",
                sdl2.SDL_WINDOWPOS_CENTERED, sdl2.SDL_WINDOWPOS_CENTERED,
                self.width, self.height,
                sdl2.SDL_WINDOW_SHOWN
        )
        if not window:
            print_error(f"Error with window creation: {sdl2.SDL_GetError()}")
            return -1
        return window

    def scene_to_free(self, game_state: GameState) -> None:
        match game_state.scene:
            case ScenePossible.MAIN:
                self.main.clean_up()

    def get_secret_map_data(self) -> list:
        map_tiles = []
        try:
            with open("assets/de_office.json") as f:
                content = json.load(f)
                map_data = content.get("layers", [])
                if map_data is None:
                    print_error("Something went wrong with de_office map data")
                else:
                    map_tiles = map_data[0].get("data", [])
                    if map_tiles is None:
                        print_error("Something went wrong with de_office map data")
                        map_tiles = []
        except (FileNotFoundError, PermissionError, ValueError):
            print_error("can't find de_office.json")
            map_tiles = []
        return map_tiles

    def main_loop(self) -> None:
        if self.init_window() == -1:
            return
        print_info("window init successful")
        window = self.create_window()
        if window == -1:
            return
        print_info("window creation successful")
        renderer = sdl2.SDL_CreateRenderer(window, -1, sdl2.SDL_RENDERER_ACCELERATED)
        game_state = GameState()
        event = sdl2.SDL_Event()
        sdl_event = SdlEvent()
        de_office = self.get_secret_map_data()
        self.main = MainMenu(renderer, self.width, self.height, game_state, self.config)
        self.game = Game(renderer, self.width, self.height, game_state, self.config)
        self.cam = Camera()
        self.secret_game = SecretGame(renderer, self.width, self.height, game_state, self.config, de_office, self.cam)

        while(game_state.is_running):
            sdl_event.main_loop(event, game_state, self.main)
            match game_state.scene:
                case ScenePossible.MAIN:
                    self.main.draw_main_menu()
                case ScenePossible.GAME:
                    self.game.draw_game()
                case ScenePossible.CSGO:
                    self.secret_game.draw_secret_game()
            game_state.frame += 1
            if game_state.frame > 60:
                game_state.frame = 1
            sdl2.SDL_Delay(16)
        self.scene_to_free(game_state)
        sdl2.SDL_DestroyRenderer(renderer)
        sdl2.SDL_DestroyWindow(window)
        sdl2.SDL_Quit()
