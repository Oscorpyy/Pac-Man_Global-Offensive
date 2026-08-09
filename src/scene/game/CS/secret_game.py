import sdl2
import sdl2.sdlttf as sttf
import sdl2.sdlimage as sdim
import numpy as np
import ctypes
from src.game_state import GameConfig, GameState
from src.drawing_methods import clear_background, draw_fps, draw_sprite_sheet
from src.color import Color
from src.scene.helper import get_ptr
from src.print_logs import print_error
from src.image import Image
from src.camera import Camera
from src.player import CsPlayer


class MouseVector2:
    def __init__(self) -> None:
        self.x, self.y = ctypes.c_int(0), ctypes.c_int(0)
        self.mouse_button: sdl2.Uint32


class SecretGame:
    def __init__(self, renderer, game_state: GameState, config: GameConfig, tilemap, cam: Camera):
        self.renderer = renderer
        self.width = config.screen_width
        self.height = config.screen_height
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
        self.tilemap_data = tilemap
        self.map_tiles = Image(b"assets/tileset.png", self.renderer)
        self.player_sprite = Image(b"assets/test2.png", self.renderer)
        sttf.TTF_Init()
        self.font_size = 16
        self.font = sttf.TTF_OpenFont(b"assets/Press_Start_2P/PressStart2P-Regular.ttf", self.font_size)
        if not self.font:
            print_error(f"can't charge font {sttf.TTF_GetError()}")
        self.player = CsPlayer(self.player_sprite, cam)
        self.cam = cam
        self.cam.offset_x = self.player.pos_x - (self.width // 4) + (self.player.sprite.width // 2)
        self.cam.offset_y = self.player.pos_y - (self.height // 4) + (self.player.sprite.height // 2)
        print(self.cam.offset_x)
        print(self.player.pos_x)
        print(self.cam.offset_y)
        print(self.player.pos_y)
        self.speed: int = 3
        self.key_w: bool = False
        self.key_s: bool = False
        self.key_a: bool = False
        self.key_d: bool = False
        self.current_mouse_pos = MouseVector2()

    def clean_up(self) -> None:
        sdim.IMG_Quit()
        sttf.TTF_CloseFont(self.font)
        sttf.TTF_Quit()
        sdl2.SDL_DestroyTexture(self.player_sprite.texture)
        sdl2.SDL_DestroyTexture(self.map_tiles.texture)
        sdl2.SDL_DestroyTexture(self.background)


    def draw_tilemap(self, scale) -> None:
        renderer = self.renderer
        map_tiles = self.map_tiles
        x = 0
        y = 0
        tile_count = 0
        cam_scaled_x = self.cam.offset_x * scale
        cam_scaled_y = self.cam.offset_y * scale
        for tile in self.tilemap_data:
            if tile == 0:
                pass
            else:
                draw_sprite_sheet(renderer, map_tiles, (x * scale) - cam_scaled_x, (y * scale) - cam_scaled_y, tile - 41, scale)
            tile_count += 1
            x += 32
            if tile_count > 39:
                x = 0
                y += 32
                tile_count = 0

    def set_keystate(self, key, is_pressed: bool) -> None:
        if key == sdl2.SDLK_w:
            self.key_w = is_pressed
        elif key == sdl2.SDLK_s:
            self.key_s = is_pressed
        elif key == sdl2.SDLK_a:
            self.key_a = is_pressed
        elif key == sdl2.SDLK_d:
            self.key_d = is_pressed

    def update_player_pos(self) -> None:
        if (self.key_w is True):
            self.player.pos_y -= self.speed
        if (self.key_s is True):
            self.player.pos_y += self.speed
        if (self.key_a is True):
            self.player.pos_x -= self.speed
        if (self.key_d is True):
            self.player.pos_x += self.speed

    def update_cam_mouse_move(self, scale: int) -> None:
        factor = 0.3
        self.current_mouse_pos.mouse_button = sdl2.SDL_GetMouseState(ctypes.byref(self.current_mouse_pos.x), ctypes.byref(self.current_mouse_pos.y))
        base_x = self.player.pos_x - (self.width // (2 * scale)) 
        base_y = self.player.pos_y - (self.height // (2 * scale))
        diff_x = self.current_mouse_pos.x.value - (self.width // 2)
        diff_y = self.current_mouse_pos.y.value - (self.height // 2)
        self.cam.offset_x = int(base_x + ((diff_x / scale) * factor))
        self.cam.offset_y = int(base_y + ((diff_y / scale) * factor))


    def draw_secret_game(self) -> None:
        clear_background(self.pixels, Color.BLACK)
        pixel_ptr = get_ptr(self.pixels)
        sdl2.SDL_UpdateTexture(self.background, None, pixel_ptr, self.pitch_background)
        sdl2.SDL_RenderCopy(self.renderer, self.background, None, None)
        self.draw_tilemap(2)
        self.player.draw_player(self.renderer, 2)
        draw_fps(self.renderer, self.font, self.game_state.fps)
        sdl2.SDL_RenderPresent(self.renderer)
        self.update_player_pos()
        self.update_cam_mouse_move(2)
