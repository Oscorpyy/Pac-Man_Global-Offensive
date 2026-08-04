import sdl2
import ctypes
from sdl2.events import SDL_Event
from src.game_state import GameState, ScenePossible
from typing import Any

class SdlEvent:
    def player_control(self) -> None:
        pass


    def free_memory(self, game_state: GameState, scene: Any) -> None:
        match game_state.scene:
            case ScenePossible.MAIN:
                scene.clean_up()

    def main_loop(self, event: SDL_Event, game_state: GameState, scene: Any) -> None:
        while sdl2.SDL_PollEvent(ctypes.byref(event)) != 0:
            if event.type == sdl2.SDL_Quit:
                game_state.is_running = False
            elif event.type == sdl2.SDL_KEYDOWN:
                key = event.key.keysym.sym
                if key == sdl2.SDLK_ESCAPE:
                    pass
                if game_state.scene == ScenePossible.GAME:
                    game_state.konami_code_entered.append(key)
                    if len(game_state.konami_code_entered) > len(game_state.konami_code_excepted):
                        game_state.konami_code_entered = []
                    if game_state.konami_code_entered == game_state.konami_code_excepted:
                        game_state.scene = ScenePossible.CSGO
                        print("CS MOD ENTERED")
                    print(game_state.konami_code_entered)

            elif event.type == sdl2.SDL_WINDOWEVENT:
                if event.window.event == sdl2.SDL_WINDOWEVENT_CLOSE:
                    game_state.is_running = False