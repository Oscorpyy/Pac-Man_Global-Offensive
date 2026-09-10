import sdl2
import json
import time
from src.scene.intro.introduction import Introduction
from src.scene.game.CS.secret_game import SecretGame
from src.print_logs import print_error, print_info
from src.control import SdlEvent
from src.game_state import GameState, ScenePossible, GameConfig
from src.scene.main_menu.main_menu import MainMenu
from src.scene.game.game import Game
from src.camera import Camera
from src.transition import Transition
from src.scene.end_screen.end import EndScreen


class Window:
    def __init__(self, config: GameConfig) -> None:
        """Initialize Window manager with configuration parameters.

        Args:
            config: The game configuration object.
        """
        self.config = config
        self.width = self.config.screen_width
        self.height = self.config.screen_height

    def init_window(self) -> int:
        """Initialize the SDL2 video subsystem.

        Returns:
            0 on success, or -1 on error.
        """
        if sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO) != 0:
            print_error(f"initialisation error with SDL {sdl2.SDL_GetError()}")
            return -1
        return 0

    def create_window(self) -> sdl2.SDL_Window | int:
        """Create and display the primary SDL window.

        Returns:
            SDL_Window instance on success, or -1 on error.
        """
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

    def end_screen_quit(self) -> None:
        """Reset both game modes and return to the main menu."""
        self.secret_game.reset()
        self.game.end_screen_quit()

    def scene_to_free(self, game_state: GameState) -> None:
        """Free resources for the currently active scene upon exit.

        Args:
            game_state: Current game state indicating active scene.
        """
        match game_state.scene:
            case ScenePossible.MAIN:
                self.main.clean_up()
            case ScenePossible.GAME:
                self.game.clean_up()
            case ScenePossible.CSGO:
                self.secret_game.clean_up()
            case ScenePossible.WIN:
                self.win_screen.clean_up()
            case ScenePossible.LOOSE:
                self.loose_screen.clean_up()

    def get_secret_map_data(self) -> list[list[int]]:
        """Load and parse the secret CS map tile layers from JSON.

        Returns:
            A list of layer tile matrices.
        """
        map_tiles: list[list[int]] = []
        try:
            with open("assets/de_office.json") as f:
                content = json.load(f)
                map_data = content.get("layers", [])
                if map_data is None:
                    print_error("Something went wrong with de_office map data")
                else:
                    for i in range(len(map_data)):
                        map_tiles.append(map_data[i].get("data", []))
                        if map_tiles is None:
                            print_error("Something went wrong with "
                                        "de_office map data")
                            map_tiles = []
        except (FileNotFoundError, PermissionError, ValueError):
            print_error("can't find de_office.json")
            map_tiles = []
        return map_tiles

    def main_loop(self) -> None:
        """Run the main application loop, dispatching scenes and events."""
        if self.init_window() == -1:
            return
        print_info("window init successful")
        window = self.create_window()
        if window == -1:
            return
        print_info("window creation successful")
        renderer = sdl2.SDL_CreateRenderer(window, -1,
                                           sdl2.SDL_RENDERER_ACCELERATED)
        game_state = GameState()
        event = sdl2.SDL_Event()
        transition = Transition(renderer, game_state, self.config)
        sdl_event = SdlEvent()
        de_office = self.get_secret_map_data()
        self.intro = Introduction(renderer, game_state, self.config,
                                  transition)
        self.main = MainMenu(renderer, game_state, self.config, transition)
        self.game = Game(renderer, game_state, self.config, transition)
        self.win_screen = EndScreen(
            renderer, game_state, self.width, self.height,
            "assets/win_picture.png", self.config.highscore_filename,
            self.end_screen_quit
        )
        self.loose_screen = EndScreen(
            renderer, game_state, self.width, self.height,
            "assets/loose_picture.png", self.config.highscore_filename,
            self.end_screen_quit
        )
        self.game.save_handler = self.win_screen
        self.cam = Camera()
        self.secret_game = SecretGame(renderer, game_state, self.config,
                                      self.game, de_office, self.cam,
                                      transition)
        previous_scene = game_state.scene
        last_time = time.perf_counter()
        while (game_state.is_running):
            current_time = time.perf_counter()
            dt = current_time - last_time
            game_state.dt = dt
            last_time = current_time
            rendered_scene = game_state.scene
            if dt > 0:
                game_state.fps_lst.append(1.0 / dt)
                game_state.fps = int(sum(game_state.fps_lst) / len(
                    game_state.fps_lst))
            match game_state.scene:
                case ScenePossible.INTRO:
                    self.intro.draw_intro()
                    sdl_event.main_loop(event, game_state, self.main,
                                        transition)
                case ScenePossible.MAIN:
                    if previous_scene != ScenePossible.MAIN:
                        self.main.refresh_scores()
                    self.main.draw_main_menu()
                    sdl_event.main_loop(event, game_state,
                                        self.main, transition)
                case ScenePossible.GAME:
                    sdl_event.main_loop(event, game_state,
                                        self.game, transition)
                    self.game.draw_game()
                case ScenePossible.CSGO:
                    sdl_event.main_loop(event, game_state,
                                        self.secret_game, transition)
                    self.secret_game.draw_secret_game()
                case ScenePossible.WIN:
                    sdl_event.main_loop(event, game_state,
                                        self.win_screen, transition)
                    self.win_screen.draw()
                case ScenePossible.LOOSE:
                    sdl_event.main_loop(event, game_state,
                                        self.loose_screen, transition)
                    self.loose_screen.draw()
            previous_scene = rendered_scene
            if transition.transition_on is True:
                transition.draw_transition()
            sdl2.SDL_RenderPresent(renderer)
            game_state.frame += 1
            if game_state.frame > 60:
                game_state.frame = 1
            time_to_wait = (time.perf_counter() - current_time) * 1000.0
            target_ms = 1000.0 / 60.0
            time_left = target_ms - time_to_wait
            if time_left > 0:
                sdl2.SDL_Delay(int(time_left))
            game_state.check_cs_finished()
        self.scene_to_free(game_state)
        sdl2.SDL_DestroyRenderer(renderer)
        sdl2.SDL_DestroyWindow(window)
        sdl2.SDL_Quit()
