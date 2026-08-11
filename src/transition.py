import numpy as np
import sdl2
from src.color import Color
from src.game_state import GameConfig, GameState, ScenePossible
from src.drawing_methods import clear_background, draw_rect_full
from src.scene.helper import get_ptr


class Transition:
    def __init__(self, renderer, game_state: GameState, config: GameConfig) -> None:
        self.transition_on = False
        self.game_state = game_state
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
        sdl2.SDL_SetTextureBlendMode(self.background, sdl2.SDL_BLENDMODE_BLEND)
        self.pitch_background = self.width * 4
        self.pixels = np.zeros((self.height, self.width), dtype=np.uint32)
        self.sens_transition: bool = False
        self.rect_width = 0
        self.speed = 40
        self.intro_fade_color = 0
        self.rect: bool = False
        self.intro: bool = False

    def clean_up(self) -> None:
        sdl2.SDL_DestroyTexture(self.background)


    def rect_transition(self) -> None:
        rect_height = self.height
        clear_background(self.pixels, 0x00000000)
        draw_rect_full(self.pixels, self.rect_width, rect_height, Color.BLUE)
        pixel_ptr = get_ptr(self.pixels)
        sdl2.SDL_UpdateTexture(self.background, None, pixel_ptr, self.pitch_background)
        sdl2.SDL_RenderCopy(self.renderer, self.background, None, None)
        if not self.sens_transition:
            self.rect_width += self.speed
            if self.rect_width >= self.width:
                self.game_state.scene = self.scene_to_put
                self.sens_transition = True
        else:
            self.rect_width -= self.speed
            if self.rect_width <= 0:
                self.transition_on = False
                self.sens_transition = False
                self.rect_width = 0
                self.rect = False

    def intro_transition(self) -> None:
        if not self.sens_transition:
            self.intro_fade_color += 5
            if self.intro_fade_color >= 255:
                self.intro_fade_color = 255
                self.game_state.scene = self.scene_to_put
                self.sens_transition = True
        else:
            self.intro_fade_color -= 5
            if self.intro_fade_color <= 0:
                self.intro_fade_color = 0
                self.transition_on = False
                self.sens_transition = False
                self.intro = False
        final_color = (self.intro_fade_color << 24) | 0x000000
        clear_background(self.pixels, final_color)
        pixel_ptr = get_ptr(self.pixels)
        sdl2.SDL_UpdateTexture(self.background, None, pixel_ptr, self.pitch_background)
        sdl2.SDL_RenderCopy(self.renderer, self.background, None, None)

    def set_scene_to_put(self, scene: ScenePossible) -> None:
        self.scene_to_put = scene

    def draw_transition(self) -> None:
        if self.rect is True:
            self.rect_transition()
        if self.intro is True:
            self.intro_transition()
