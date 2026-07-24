import sdl2
import ctypes
from sdl2.events import SDL_Event
from src.game_state import GameState

class SdlEvent:
    def player_control(self) -> None:
        pass

    def main_loop(self, event: SDL_Event, game_state: GameState) -> None:
        while sdl2.SDL_PollEvent(ctypes.byref(event)) != 0:
            if event.type == sdl2.SDL_Quit:
                game_state.is_running = False
            elif event.type == sdl2.SDL_KEYDOWN:
                key = event.key.keysym.sym
                if key == sdl2.SDLK_ESCAPE:
                    game_state.is_running = False
            elif event.type == sdl2.SDL_WINDOWEVENT:
                if event.window.event == sdl2.SDL_WINDOWEVENT_CLOSE:
                    game_state.is_running = False
