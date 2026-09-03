from src.transition import Transition
import sdl2
import ctypes
from sdl2.events import SDL_Event
from src.print_logs import print_info
from src.game_state import GameState, ScenePossible
from typing import Any


class SdlEvent:
    def __init__(self) -> None:
        pass

    def player_control(self) -> None:
        pass

    def main_loop(self, event: SDL_Event, game_state: GameState, scene: Any,
                  transition: Transition) -> None:
        while sdl2.SDL_PollEvent(ctypes.byref(event)) != 0:
            key = event.key.keysym.sym
            if event.type == sdl2.SDL_QUIT:
                game_state.is_running = False
            elif event.type == sdl2.SDL_KEYDOWN:
                if game_state.scene == ScenePossible.INTRO:
                    if key:
                        transition.transition_on = False
                        game_state.scene = ScenePossible.MAIN
                    continue

                if key == sdl2.SDLK_ESCAPE:
                    if game_state.scene == ScenePossible.MAIN:
                        game_state.is_running = False
                    elif game_state.scene == ScenePossible.GAME:
                        if not transition.transition_on:
                            transition.start_image_transition(
                                ScenePossible.MAIN
                            )
                            if hasattr(scene, 'needs_reset'):
                                scene.needs_reset = True
                    elif game_state.scene == ScenePossible.CSGO:
                        transition.speed = 80
                        transition.transition_on = True
                        transition.scene_to_put = ScenePossible.GAME
                        transition.img = True
                    continue

                if game_state.scene == ScenePossible.GAME:
                    if hasattr(scene, 'handle_event'):
                        scene.handle_event(event)

                    game_state.konami_code_entered.append(key)
                    if len(game_state.konami_code_entered) > len(
                            game_state.konami_code_excepted):
                        game_state.konami_code_entered = []
                    if game_state.konami_code_entered == (
                            game_state.konami_code_excepted):
                        transition.transition_on = True
                        transition.scene_to_put = ScenePossible.CSGO
                        transition.img = True
                        print_info("CS MOD ENTERED")
                        continue
                if game_state.scene == ScenePossible.CSGO:
                    scene.set_keystate(key, True)

            elif event.type == sdl2.SDL_KEYUP:
                if game_state.scene == ScenePossible.GAME:
                    if hasattr(scene, 'handle_event'):
                        scene.handle_event(event)
                elif game_state.scene == ScenePossible.CSGO:
                    scene.set_keystate(key, False)

            elif event.type == sdl2.SDL_MOUSEBUTTONDOWN:
                if game_state.scene == ScenePossible.GAME:
                    if hasattr(scene, 'handle_event'):
                        scene.handle_event(event)

            elif event.type == sdl2.SDL_WINDOWEVENT:
                if event.window.event == sdl2.SDL_WINDOWEVENT_CLOSE:
                    game_state.is_running = False
