import sdl2
from src.print_logs import print_error, print_info, print_warning
from src.control import SdlEvent
from src.game_state import GameState, ScenePossible
from src.scene.main_menu.main_menu import MainMenu


class Window:
    def __init__(self) -> None:
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

    def main_loop(self) -> None:
        self.init_window()
        window = self.create_window()
        if window == -1:
            return
        renderer = sdl2.SDL_CreateRenderer(window, -1, sdl2.SDL_RENDERER_ACCELERATED)
        game_state = GameState()
        event = sdl2.SDL_Event()
        sdl_event = SdlEvent()
        main = MainMenu(renderer, self.width, self.height)
        while(game_state.is_running):
            sdl_event.main_loop(event, game_state)
            if game_state.scene == ScenePossible.MAIN:
                main.draw_background()
            sdl2.SDL_Delay(16)
