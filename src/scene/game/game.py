import sdl2 
import numpy as np
from src.scene.helper import get_ptr
from src.game_state import GameConfig, GameState
from src.drawing_methods import clear_background, draw_rect_not_full
from src.color import Color
from src.transition import Transition


class Game:
    def __init__(self, renderer, game_state: GameState, config: GameConfig,
                 transition: Transition):
        self.transition = transition
        self.width = config.screen_width
        self.height = config.screen_height
        self.renderer = renderer
        self.pixels = np.zeros((self.height, self.width), dtype=np.uint32)
        self.game_state = game_state
        self.config = config
        self.background = sdl2.SDL_CreateTexture(
            renderer,
            sdl2.SDL_PIXELFORMAT_ARGB8888,
            sdl2.SDL_TEXTUREACCESS_STREAMING,
            self.width,
            self.height
        )
        self.pitch_background = self.width * 4

    def clean_up(self) -> None:
        # sdim.IMG_Quit()
        # sttf.TTF_CloseFont(self.font)
        # sttf.TTF_Quit()
        # sdl2.SDL_DestroyTexture(self.character.texture)
        sdl2.SDL_DestroyTexture(self.background)

    def draw_game(self) -> None:
        clear_background(self.pixels, Color.BLACK)
        draw_rect_not_full(self.pixels, 100, 100, Color.RED, 5, 50, 50)
        pixel_ptr = get_ptr(self.pixels)
        sdl2.SDL_UpdateTexture(self.background, None, pixel_ptr,
                               self.pitch_background)
        sdl2.SDL_RenderCopy(self.renderer, self.background, None, None)
