import numpy as np
import sdl2
from src.color import Color
from src.game_state import GameConfig, ScenePossible
from src.drawing_methods import draw_rect_full
from src.scene.helper import get_ptr


class Transition:
    def __init__(self, renderer, current_scene: ScenePossible, config: GameConfig) -> None:
        self.transition_on = False
        self.scene_to_put: ScenePossible
        self.width = config.screen_width
        self.height = config.screen_height
        self.renderer = renderer
        self.background = sdl2.SDL_CreateTexture(
            renderer,
            sdl2.SDL_PIXELFORMAT_ARGB8888,
            sdl2.SDL_TEXTUREACCESS_STREAMING,
            self.width,
            self.height
        )
        self.pitch_background = self.width * 4
        self.pixels = np.zeros((self.height, self.width), dtype=np.uint32)

    def clean_up(self) -> None:
        sdl2.SDL_DestroyTexture(self.background)


    def rect_transition(self) -> None:
        rect_width = 0
        rect_height = self.height
        while rect_width < self.width:
            draw_rect_full(self.pixels, rect_width, rect_height, Color.BLACK)
            pixel_ptr = get_ptr(self.pixels)
            sdl2.SDL_UpdateTexture(self.background, None, pixel_ptr, self.pitch_background)
            sdl2.SDL_RenderCopy(self.renderer, self.background, None, None)
            sdl2.SDL_RenderPresent(self.renderer)
            rect_width += 1
        self.transition_on = False

    def set_scene_to_put(self, scene: ScenePossible) -> None:
        self.scene_to_put = scene
