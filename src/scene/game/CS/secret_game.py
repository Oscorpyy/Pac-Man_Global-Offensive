import sdl2
import numpy as np
from src.game_state import GameConfig, GameState
from src.drawing_methods import clear_background
from src.color import Color
from src.scene.helper import get_ptr


class SecretGame:
    def __init__(self, renderer, width: int, height: int, game_state: GameState, config: GameConfig):
        self.renderer = renderer
        self.pixels = np.zeros((height, width), dtype=np.uint32)
        self.game_state = game_state
        self.config = config
        self.background = sdl2.SDL_CreateTexture(
            renderer,
            sdl2.SDL_PIXELFORMAT_ARGB8888,
            sdl2.SDL_TEXTUREACCESS_STREAMING,
            width,
            height
        )
        self.pitch_background = width * 4

    def draw_secret_game(self) -> None:
        clear_background(self.pixels, Color.BLUE)
        pixel_ptr = get_ptr(self.pixels)
        sdl2.SDL_UpdateTexture(self.background, None, pixel_ptr, self.pitch_background)
        sdl2.SDL_RenderCopy(self.renderer, self.background, None, None)
        sdl2.SDL_RenderPresent(self.renderer)
