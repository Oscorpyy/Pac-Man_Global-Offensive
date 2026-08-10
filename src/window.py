import sdl2
import json
import time
from typing import Any
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
        self.width = self.config.screen_width
        self.height = self.config.screen_height

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
            case ScenePossible.GAME:
                self.game.clean_up()
            case ScenePossible.CSGO:
                self.secret_game.clean_up()

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
        self.main = MainMenu(renderer, game_state, self.config)
        self.game = Game(renderer, game_state, self.config)
        self.cam = Camera()
        self.secret_game = SecretGame(renderer, game_state, self.config, de_office, self.cam)
        last_time = time.perf_counter()
        while(game_state.is_running):
            current_time = time.perf_counter()
            dt = current_time - last_time
            last_time = current_time
            if dt > 0:
                game_state.fps_lst.append(1.0 / dt)
                game_state.fps = int(sum(game_state.fps_lst) / len(game_state.fps_lst))
            match game_state.scene:
                case ScenePossible.MAIN:
                    self.main.draw_main_menu()
                    sdl_event.main_loop(event, game_state, self.main)
                case ScenePossible.GAME:
                    sdl_event.main_loop(event, game_state, self.game)
                    self.game.draw_game()
                case ScenePossible.CSGO:
                    sdl_event.main_loop(event, game_state, self.secret_game)
                    self.secret_game.draw_secret_game()
            game_state.frame += 1
            if game_state.frame > 60:
                game_state.frame = 1
            time_to_wait = (time.perf_counter() - current_time) * 1000.0
            target_ms = 1000.0 / 60.0
            time_left = target_ms - time_to_wait
            if time_left > 0:
                sdl2.SDL_Delay(int(time_left))
        self.scene_to_free(game_state)
        sdl2.SDL_DestroyRenderer(renderer)
        sdl2.SDL_DestroyWindow(window)
        sdl2.SDL_Quit()
