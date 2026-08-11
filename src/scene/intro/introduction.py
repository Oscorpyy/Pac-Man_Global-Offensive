import sdl2 
import sdl2.sdlimage as sdim
import sdl2.sdlttf as sttf
import numpy as np
import time
from src.print_logs import print_error
from src.image import Image
from src.scene.helper import get_ptr
from src.game_state import GameConfig, GameState, ScenePossible
from src.drawing_methods import clear_background, draw_text
from src.color import Color
from src.transition import Transition
from src.drawing_methods import draw_sprites
from src.transition import Transition


class Introduction:
    def __init__(self, renderer, game_state: GameState, config: GameConfig, transition: Transition):
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
        sdim.IMG_Init(sdim.IMG_INIT_PNG)
        self.sdl_logo = Image(b"assets/sdl.png", renderer)
        self.team_logo = Image(b"assets/Team_logo.png", renderer)
        self.pitch_background = self.width * 4
        sttf.TTF_Init()
        self.font_size = 24
        self.font = sttf.TTF_OpenFont(b"assets/Press_Start_2P/PressStart2P-Regular.ttf", self.font_size)
        if not self.font:
            print_error(f"can't charge font {sttf.TTF_GetError()}")
        self.time_passed = time.perf_counter()

    def clean_up(self) -> None:
        sdim.IMG_Quit()
        sttf.TTF_CloseFont(self.font)
        sttf.TTF_Quit()
        sdl2.SDL_DestroyTexture(self.sdl_logo.texture)
        sdl2.SDL_DestroyTexture(self.background)

    def draw_intro(self) -> None:
        clear_background(self.pixels, Color.BLACK)
        pixel_ptr = get_ptr(self.pixels)
        sdl2.SDL_UpdateTexture(self.background, None, pixel_ptr, self.pitch_background)
        sdl2.SDL_RenderCopy(self.renderer, self.background, None, None)
        draw_sprites(self.renderer, self.team_logo, int(self.width * 0.2) - int(self.sdl_logo.width * 0.2 * 0.5), int(self.height * 0.5) - int(self.sdl_logo.height * 0.5), 0.30)
        draw_text(self.renderer, self.font, b"Made by:\n- Opernod\n- Lgoderne", int(self.width * 0.2) - int(self.sdl_logo.width * 0.2 * 0.5), int(self.height * 0.5) - int(self.sdl_logo.height * 0.2 * 0.5), Color.WHITE)
        draw_sprites(self.renderer, self.sdl_logo, int(self.width * 0.8) - int(self.sdl_logo.width * 0.2 * 0.5), int(self.height * 0.5) - int(self.sdl_logo.height * 0.5), 0.2)
        draw_text(self.renderer, self.font, b"Made with SDL2", int(self.width * 0.8) - int(self.sdl_logo.width * 0.2 * 0.5), int(self.height * 0.5) - int(self.sdl_logo.height * 0.2 * 0.5), Color.WHITE)
        if (time.perf_counter() - self.time_passed > 3):
            self.transition.scene_to_put = ScenePossible.MAIN
            self.transition.transition_on = True
            self.transition.intro = True
