from src.transition import Transition
import sdl2
import ctypes
from sdl2.events import SDL_Event
from src.print_logs import print_info
from src.game_state import GameState, ScenePossible
from typing import Any
from src.transition import Transition

class SdlEvent:
    def __init__(self) -> None:
        pass

    def player_control(self) -> None:
        pass

    def main_loop(self, event: SDL_Event, game_state: GameState, scene: Any,
                  transition: Transition) -> None:
        while sdl2.SDL_PollEvent(ctypes.byref(event)) != 0:
            key = event.key.keysym.sym
            if event.type == sdl2.SDL_Quit:
                game_state.is_running = False
            elif event.type == sdl2.SDL_KEYDOWN:
                if key == sdl2.SDLK_ESCAPE:
                    if game_state.scene == ScenePossible.MAIN:
                        game_state.is_running = False
                    elif game_state.scene == ScenePossible.GAME:
                        transition.transition_on = True
                        transition.scene_to_put = ScenePossible.MAIN
                    elif game_state.scene == ScenePossible.CSGO:
                        transition.transition_on = True
                        transition.scene_to_put = ScenePossible.GAME
                if game_state.scene == ScenePossible.GAME:
                    game_state.konami_code_entered.append(key)
                    if len(game_state.konami_code_entered) > len(game_state.konami_code_excepted):
                        game_state.konami_code_entered = []
                    if game_state.konami_code_entered == game_state.konami_code_excepted:
                        transition.transition_on = True
                        transition.scene_to_put = ScenePossible.CSGO
                        # game_state.scene = ScenePossible.CSGO
                        print_info("CS MOD ENTERED")
                        continue
                if game_state.scene == ScenePossible.CSGO:
                    scene.set_keystate(key, True)

            elif event.type == sdl2.SDL_KEYUP:
                if game_state.scene == ScenePossible.CSGO:
                    scene.set_keystate(key, False)

            elif event.type == sdl2.SDL_WINDOWEVENT:
                if event.window.event == sdl2.SDL_WINDOWEVENT_CLOSE:
                    game_state.is_running = False
