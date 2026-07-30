import sdl2
import sdl2.sdlimage as sdim
import sdl2.sdlttf as sttf
import numpy as np
from src.color import Color
from src.drawing_methods import draw_rect_full, clear_background, draw_text, draw_sprite_sheet, Button
from src.scene.helper import get_ptr
from src.print_logs import print_error
from src.game_state import GameState, ScenePossible


class MainMenu:
    def __init__(self, renderer, width: int, height: int, game_state: GameState) -> None:
        self.game_state = game_state
        self.renderer = renderer
        # img loading
        sdim.IMG_Init(sdim.IMG_INIT_PNG)
        self.img_path = b"assets/test3.png"
        self.img_surface = sdim.IMG_Load(self.img_path)
        if not self.img_surface:
            print_error(f"can't charge image {sdim.IMG_GetError()}")
        self.img_texture = sdl2.SDL_CreateTextureFromSurface(self.renderer, self.img_surface)
        sdl2.SDL_FreeSurface(self.img_surface)
        # Font loading
        sttf.TTF_Init()
        self.font_size = 16
        self.font = sttf.TTF_OpenFont(b"assets/Press_Start_2P/PressStart2P-Regular.ttf", self.font_size)
        if not self.font:
            print_error(f"can't charge font {sttf.TTF_GetError()}")
        self.text = b"aaaaaaaaaa\nadsfasdfsadf"
        self.width = width
        self.background = sdl2.SDL_CreateTexture(
            renderer,
            sdl2.SDL_PIXELFORMAT_ARGB8888,
            sdl2.SDL_TEXTUREACCESS_STREAMING,
            width,
            height
        )
        self.test_x: int = 10
        self.pixels = np.zeros((height, width), dtype=np.uint32)
        self.pitch_background = width * 4


    def clean_up(self) -> None:
        sdim.IMG_Quit()
        sttf.TTF_CloseFont(self.font)
        sttf.TTF_Quit()


    def next_scene(self):
        self.game_state.scene = ScenePossible.GAME


    def draw_background(self) -> None:
        btn_test = Button(self.renderer, self.pixels, self.font, 300, 80, 160, 50, Color.RED, Color.PURPLE, self.next_scene)
        clear_background(self.pixels, Color.BLUE)
        draw_rect_full(self.pixels, 15, 15, Color.RED, x=self.test_x, y=0)
        btn_test.draw_background()
        pixel_ptr = get_ptr(self.pixels)
        sdl2.SDL_UpdateTexture(self.background, None, pixel_ptr, self.pitch_background)
        sdl2.SDL_RenderCopy(self.renderer, self.background, None, None)
        # draw_sprites(self.renderer, self.img_texture, 50, 45, 10)
        draw_sprite_sheet(self.renderer, self.img_texture, 50, 45, 0, 4)
        draw_text(self.renderer, self.font, self.text, 10, 200, 2)
        btn_test.draw_text(b"Start Game")
        sdl2.SDL_RenderPresent(self.renderer)
        self.test_x += 10
        if self.test_x >= self.width:
            self.test_x = 10


    def draw_main_menu(self) -> None:
        self.draw_background()
