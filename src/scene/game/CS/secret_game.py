import sdl2
import sdl2.sdlttf as sttf
import sdl2.sdlimage as sdim
import numpy as np
import ctypes
import time
from src.game_state import GameConfig, GameState
from src.drawing_methods import clear_background, draw_fps, draw_rect_full, draw_sprite_sheet, draw_sprites, draw_text
from src.color import Color
from src.scene.helper import Vector2, get_ptr
from src.print_logs import print_error
from src.image import Image
from src.camera import Camera
from src.player import CsPlayer
from src.transition import Transition


class MouseVector2:
    def __init__(self) -> None:
        self.x, self.y = ctypes.c_int(0), ctypes.c_int(0)
        self.mouse_button: sdl2.Uint32


class SecretGame:
    def __init__(self, renderer, game_state: GameState, config: GameConfig, tilemap, cam: Camera, transition: Transition):
        self.transition = transition
        self.renderer = renderer
        self.width = config.screen_width
        self.height = config.screen_height
        self.pixels = np.zeros((self.height, self.width), dtype=np.uint32)
        self.ui_pixels = np.zeros((self.height, self.width), dtype=np.uint32)
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
        self.player_sprite = Image(b"assets/terrorist/terrorist_sheet.png", self.renderer)
        self.bomba = Image(b"assets/3D_model/little_bomba.png", self.renderer)
        self.character_icons = Image(b"assets/character_icons.png", self.renderer)
        sttf.TTF_Init()
        self.font_size = 16
        self.font = sttf.TTF_OpenFont(b"assets/Press_Start_2P/PressStart2P-Regular.ttf", self.font_size)
        if not self.font:
            print_error(f"can't charge font {sttf.TTF_GetError()}")
        self.player = CsPlayer(self.player_sprite, cam)
        self.default_player_pos_x = 32 * 2
        self.default_player_pos_y = 32 * 35
        self.player.pos_x = self.default_player_pos_x
        self.player.pos_y = self.default_player_pos_y
        self.player.can_move = False
        self.player.can_shoot = False
        self.cam = cam
        self.cam.offset_x = self.player.pos_x - (self.width // 4) + (self.player.sprite.width // 2)
        self.cam.offset_y = self.player.pos_y - (self.height // 4) + (self.player.sprite.height // 2)
        self.speed: int = 3
        self.current_mouse_pos = MouseVector2()
        self.round_timer: float = 49.0
        self.bomb_diffuse_time: float = 5.0
        self.player_diffuse_time: float = 0.0
        self.round_start_timer: float = 4.0

    def clean_up(self) -> None:
        sdim.IMG_Quit()
        sttf.TTF_CloseFont(self.font)
        sttf.TTF_Quit()
        sdl2.SDL_DestroyTexture(self.player_sprite.texture)
        sdl2.SDL_DestroyTexture(self.map_tiles.texture)
        sdl2.SDL_DestroyTexture(self.background)
        sdl2.SDL_DestroyTexture(self.bomba.texture)
        sdl2.SDL_DestroyTexture(self.character_icons.texture)

    def draw_tilemap(self, scale) -> None:
        renderer = self.renderer
        map_tiles = self.map_tiles
        cam_scaled_x = self.cam.offset_x * scale
        cam_scaled_y = self.cam.offset_y * scale
        tile_scaled = 32 * scale
        i = 0
        for layer in self.tilemap_data:
            x = 0
            y = 0
            tile_count = 0
            if i == 3:
                continue
            for tile in layer:
                screen_x = (x * scale) - cam_scaled_x
                screen_y = (y * scale) - cam_scaled_y
                if tile == 0:
                    pass
                elif (screen_x > -tile_scaled and screen_x < self.width) and (screen_y > -tile_scaled and screen_y < self.height):
                    draw_sprite_sheet(renderer, map_tiles, (x * scale) - cam_scaled_x, (y * scale) - cam_scaled_y, tile - 97, scale)
                tile_count += 1
                x += 32
                if tile_count > 39:
                    x = 0
                    y += 32
                    tile_count = 0
            i += 1

    def set_keystate(self, key, is_pressed: bool) -> None:
        if key == sdl2.SDLK_w:
            self.player.key_w = is_pressed
        elif key == sdl2.SDLK_s:
            self.player.key_s = is_pressed
        elif key == sdl2.SDLK_a:
            self.player.key_a = is_pressed
        elif key == sdl2.SDLK_d:
            self.player.key_d = is_pressed
        elif key == sdl2.SDLK_e:
            self.player.key_e = is_pressed

    def can_player_move(self, pos_x: int, pos_y: int) -> bool:
        x = 0
        y = 0
        tile_count = 0
        player_size = 32
        for tile in self.tilemap_data[3]:
            if tile != 0:
                if (pos_x + player_size > x and pos_x < x + 32 and
                    pos_y + player_size > y and pos_y < y + 32):
                    return False
            tile_count += 1
            x += 32
            if tile_count > 39:
                x = 0
                tile_count = 0
                y += 32
        return True

    def update_player_pos(self) -> None:
        if (self.player.key_w is True):
            pos_y = self.player.pos_y - self.speed
            if self.can_player_move(self.player.pos_x, pos_y) is True:
                self.player.pos_y = pos_y
        if (self.player.key_s is True):
            pos_y = self.player.pos_y + self.speed
            if self.can_player_move(self.player.pos_x, pos_y) is True:
                self.player.pos_y = pos_y
        if (self.player.key_a is True):
            pos_x = self.player.pos_x - self.speed
            if self.can_player_move(pos_x, self.player.pos_y) is True:
                self.player.pos_x = pos_x
        if (self.player.key_d is True):
            pos_x = self.player.pos_x + self.speed
            if self.can_player_move(pos_x, self.player.pos_y) is True:
                self.player.pos_x = pos_x

    def defuse_bomb(self) -> None:
        bomb_size: int = 32
        bomb_pos_x: int = 32
        bomb_pos_y: int = 64
        player_size: int = 32
        if (self.player.pos_x <= bomb_pos_x + bomb_size and
            self.player.pos_x + player_size >= bomb_pos_x and
            self.player.pos_y <= bomb_pos_y + bomb_size and
            self.player.pos_y + player_size >= bomb_pos_y
        ):
            if self.player.key_e is True:
                self.player_diffuse_time += self.game_state.dt
                time: str = f"{self.player_diffuse_time:.1f}"
                draw_text(self.renderer, self.font, time.encode(), (32 * 2) - (self.cam.offset_x * 2), (64 * 1) - (self.cam.offset_y * 2), Color.GREEN, 2)
                if self.player_diffuse_time >= 5:
                    self.game_state.cs_round_win += 1
                    self.player_diffuse_time = 0.0
                    self.player.pos_x = self.default_player_pos_x
                    self.player.pos_y = self.default_player_pos_y
                    self.player.can_move = False
                    self.player.can_shoot = False
                    self.round_start_timer = 4
                    self.round_timer = 49.0
            if self.player.key_e is False:
                self.player_diffuse_time = 0
        else:
            self.player_diffuse_time = 0

    def update_cam_mouse_move(self, scale: int) -> None:
        factor = 0.3
        self.current_mouse_pos.mouse_button = sdl2.SDL_GetMouseState(ctypes.byref(self.current_mouse_pos.x), ctypes.byref(self.current_mouse_pos.y))
        base_x = self.player.pos_x - (self.width // (2 * scale))
        base_y = self.player.pos_y - (self.height // (2 * scale))
        diff_x = self.current_mouse_pos.x.value - (self.width // 2)
        diff_y = self.current_mouse_pos.y.value - (self.height // 2)
        self.cam.offset_x = int(base_x + ((diff_x / scale) * factor))
        self.cam.offset_y = int(base_y + ((diff_y / scale) * factor))

    def draw_scores(self) -> None:
        my_score = f"{self.game_state.cs_round_win}"
        ennemy_score = f"{self.game_state.cs_round_loose}"
        draw_text(self.renderer, self.font, my_score.encode(), (self.width // 2) - 15, 10, Color.BLACK)
        draw_text(self.renderer, self.font, ennemy_score.encode(), (self.width // 2) + 15, 10, Color.BLACK)

    def draw_timer(self) -> None:
        if self.round_start_timer > 0:
            timer: str = f"{int(self.round_start_timer)}"
            draw_text(self.renderer, self.font, timer.encode(), (self.width // 2), 40, Color.RED)
        else:
            timer: str = f"{int(self.round_timer)}"
            if self.round_timer <= 10.0:
                draw_text(self.renderer, self.font, timer.encode(), (self.width // 2), 40, Color.RED)
            else:
                draw_text(self.renderer, self.font, timer.encode(), (self.width // 2) - 10, 40, Color.BLACK)

    def draw_number_player(self) -> None:
        draw_sprite_sheet(self.renderer, self.character_icons, (self.width // 2) - 100, 10, 0, 2)
        draw_sprite_sheet(self.renderer, self.character_icons, (self.width // 2) + 50, 10, 1, 2)
        draw_text(self.renderer, self.font, b"1", (self.width // 2) - 100, 10, Color.WHITE)
        draw_text(self.renderer, self.font, b"0", (self.width // 2) + 50, 10, Color.WHITE)

    def update_timers(self) -> None:
        self.round_timer -= self.game_state.dt
        self.round_start_timer -= self.game_state.dt
        if self.round_start_timer <= 0.0:
            self.player.can_move = True
            self.player.can_shoot = True
        if self.round_timer <= 0.0:
            self.player.can_move = False
            self.player.can_shoot = False
            self.round_timer = 49.0
            self.round_start_timer = 4
            self.player.pos_x = self.default_player_pos_x
            self.player.pos_y = self.default_player_pos_y
            self.game_state.cs_round_loose += 1

    def draw_secret_game(self) -> None:
        clear_background(self.pixels, Color.GRAY)
        pixel_ptr = get_ptr(self.pixels)
        sdl2.SDL_UpdateTexture(self.background, None, pixel_ptr, self.pitch_background)
        sdl2.SDL_RenderCopy(self.renderer, self.background, None, None)
        self.draw_tilemap(2)
        draw_sprites(self.renderer, self.bomba, (32 * 2) - (self.cam.offset_x * 2), (64 * 2) - (self.cam.offset_y * 2), 2)
        self.player.draw_player(self.renderer, 2, self.current_mouse_pos.x.value, self.current_mouse_pos.y.value)
        draw_fps(self.renderer, self.font, self.game_state.fps)
        self.draw_scores()
        self.draw_timer()
        self.draw_number_player()
        if self.player.can_move is True:
            self.update_player_pos()
        self.player.update()
        self.defuse_bomb()
        self.update_cam_mouse_move(2)
        self.update_timers()
