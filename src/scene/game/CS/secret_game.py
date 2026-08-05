import sdl2
import sdl2.sdlimage as sdim
import numpy as np
from src.game_state import GameConfig, GameState
from src.drawing_methods import clear_background, draw_sprite_sheet
from src.color import Color
from src.scene.helper import get_ptr
from src.print_logs import print_error


class SecretGame:
    def __init__(self, renderer, width: int, height: int, game_state: GameState, config: GameConfig, tilemap):
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
        self.tilemap_data = tilemap
        self.img_path = b"assets/tileset.png"
        self.img_surface = sdim.IMG_Load(self.img_path)
        if not self.img_surface:
            print_error(f"can't charge image {sdim.IMG_GetError()}")
        self.img_texture = sdl2.SDL_CreateTextureFromSurface(self.renderer, self.img_surface)
        sdl2.SDL_FreeSurface(self.img_surface)


    def draw_tilemap(self, scale) -> None:
        x = 0
        y = 0
        tile_count = 0
        for tile in self.tilemap_data:
            if tile == 0:
                pass
            else:
                draw_sprite_sheet(self.renderer, self.img_texture, x, y, tile - 41, scale)
            tile_count += 1
            x += 32
            if tile_count > 39:
                x = 0
                y += 32
                tile_count = 0

    def draw_secret_game(self) -> None:
        clear_background(self.pixels, Color.BLUE)
        pixel_ptr = get_ptr(self.pixels)
        sdl2.SDL_UpdateTexture(self.background, None, pixel_ptr, self.pitch_background)
        sdl2.SDL_RenderCopy(self.renderer, self.background, None, None)
        self.draw_tilemap(1)
        sdl2.SDL_RenderPresent(self.renderer)
