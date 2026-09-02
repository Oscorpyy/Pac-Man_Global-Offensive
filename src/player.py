import math
from src.camera import Camera
from src.image import Image
from src.drawing_methods import draw_sprite_sheet
from src.color import Color
import numpy as np


class CsPlayer:
    def __init__(self, sprite: Image, cam: Camera) -> None:
        self.pos_x: int = 0
        self.pos_y: int = 0
        self.can_move: bool = True
        self.can_collide: bool = True
        self.can_shoot: bool = True
        self.sprite: Image = sprite
        self.cam = cam
        self.current_frame: int = 0
        self.frame_number: int = 24
        self.animation_speed: int = 5
        self.tick_counter: int = 0
        self.key_w: bool = False
        self.key_s: bool = False
        self.key_a: bool = False
        self.key_d: bool = False
        self.key_e: bool = False

    def update(self) -> None:
        self.tick_counter += 1
        if self.tick_counter >= self.animation_speed:
            self.tick_counter = 0
            self.current_frame += 1
            self.current_frame = self.current_frame % self.frame_number

    def draw_player(self, renderer,  scale: int, mouse_x: int, mouse_y: int) -> None:
        pos_x = (self.pos_x - self.cam.offset_x) * scale
        pos_y = (self.pos_y - self.cam.offset_y) * scale
        dx = mouse_x - pos_x
        dy = mouse_y - pos_y
        angle_rad = math.atan2(dy, dx)
        angle = math.degrees(angle_rad)
        angle = (angle + 360) % 360
        direction_index = int(((angle + 22.5) % 360) // 45)
        if direction_index == 5:
            draw_sprite_sheet(renderer, self.sprite, pos_x, pos_y, self.current_frame + 125, scale)
        elif direction_index == 3:
            draw_sprite_sheet(renderer, self.sprite, pos_x, pos_y, self.current_frame + 101, scale)
        elif direction_index == 1:
            draw_sprite_sheet(renderer, self.sprite, pos_x, pos_y, self.current_frame + 150, scale)
        elif direction_index == 7:
            draw_sprite_sheet(renderer, self.sprite, pos_x, pos_y, self.current_frame + 175, scale)
        elif direction_index == 6:
            draw_sprite_sheet(renderer, self.sprite, pos_x, pos_y, self.current_frame + 75, scale)
        elif direction_index == 4:
            draw_sprite_sheet(renderer, self.sprite, pos_x, pos_y, self.current_frame + 50, scale)
        elif direction_index == 0:
            draw_sprite_sheet(renderer, self.sprite, pos_x, pos_y, self.current_frame + 26, scale)
        elif direction_index == 2:
            draw_sprite_sheet(renderer, self.sprite, pos_x, pos_y, self.current_frame, scale)


class PacPlayer:
    def __init__(self, sprite=None, cam=None) -> None:
        self.pos_x: int = 0
        self.pos_y: int = 0
        self.can_move: bool = True
        self.can_collide: bool = True
        self.is_powered_up: bool = False

        self.sprite = sprite
        self.cam = cam

        self.current_frame: int = 0
        self.frame_number: int = 4
        self.animation_speed: int = 10
        self.tick_counter: int = 0

        self.move_cooldown: int = 12
        self.move_tick: int = 0

        self.key_w: bool = False
        self.key_s: bool = False
        self.key_a: bool = False
        self.key_d: bool = False

        self.direction: int = 0  # 0=Right, 1=Left, 2=Up, 3=Down
        self.is_powered_up: bool = False
        self.power_timer: int = 0

        self.texture_argb = None
        try:
            import sdl2
            import sdl2.sdlimage as sdim
            import ctypes
            surf = sdim.IMG_Load(b"assets/pacman.png")
            if surf:
                conv_surf = sdl2.SDL_ConvertSurfaceFormat(surf, sdl2.SDL_PIXELFORMAT_ARGB8888, 0)
                sdl2.SDL_FreeSurface(surf)
                if conv_surf:
                    w, h = conv_surf.contents.w, conv_surf.contents.h
                    pitch = conv_surf.contents.pitch
                    ptr = ctypes.cast(conv_surf.contents.pixels, ctypes.POINTER(ctypes.c_uint32))
                    self.texture_argb = np.ctypeslib.as_array(ptr, shape=(h, pitch // 4)).copy()
                    sdl2.SDL_FreeSurface(conv_surf)
        except Exception as e:
            print(f"Warning: could not load pacman texture: {e}")
            self.texture_argb = None

    def update(self) -> None:
        """Met à jour le compteur d'animation du sprite."""
        self.tick_counter += 1
        if self.tick_counter >= self.animation_speed:
            self.tick_counter = 0
            self.current_frame = (self.current_frame + 1) % self.frame_number

        if self.is_powered_up:
            self.power_timer -= 1
            if self.power_timer <= 0:
                self.is_powered_up = False

    def handle_movement(self, maze_matrix: list[list[int]],
                        items_matrix: list[list[int]],
                        game_state=None, config=None) -> None:
        """
        Déplace Pac-Man selon les murs (bits 1=Nord, 2=Est, 4=Sud, 8=Ouest)
        et consomme les pacgums sur son passage.
        """
        if self.key_w:
            self.direction = 2
        elif self.key_s:
            self.direction = 3
        elif self.key_a:
            self.direction = 1
        elif self.key_d:
            self.direction = 0

        if not self.can_move:
            return

        self.move_tick += 1
        if self.move_tick < self.move_cooldown:
            return
        self.move_tick = 0

        NORTH, EAST, SOUTH, WEST = 1, 2, 4, 8
        maze_height = len(maze_matrix)
        maze_width = len(maze_matrix[0]) if maze_height > 0 else 0

        curr_cell = maze_matrix[self.pos_y][self.pos_x]
        new_x, new_y = self.pos_x, self.pos_y

        if self.key_w and not (curr_cell & NORTH) and self.pos_y > 0:
            new_y -= 1
        elif self.key_s and not (
                curr_cell & SOUTH) and self.pos_y < maze_height - 1:
            new_y += 1
        elif self.key_a and not (
                curr_cell & WEST) and self.pos_x > 0:
            new_x -= 1
        elif self.key_d and not (
                curr_cell & EAST) and self.pos_x < maze_width - 1:
            new_x += 1

        self.pos_x, self.pos_y = new_x, new_y

        # Consommation des gommes
        if 0 <= self.pos_y < maze_height and 0 <= self.pos_x < maze_width:
            item = items_matrix[self.pos_y][self.pos_x]
            if item == 1:  # Pacgum
                items_matrix[self.pos_y][self.pos_x] = 0
                if game_state is not None and config is not None:
                    pts = config.points_per_pacgum if config.points_per_pacgum is not None else 10
                    game_state.point += int(pts)
            elif item == 2:  # Super-pacgum
                items_matrix[self.pos_y][self.pos_x] = 0
                self.is_powered_up = True
                self.power_timer = 600  # 10 secondes (60 frames * 10)
                if game_state is not None and config is not None:
                    pts = config.points_per_super_pacgum if config.points_per_super_pacgum is not None else 50
                    game_state.point += int(pts)

    def draw_player_pixels(self, pixels: np.ndarray, start_x: int,
                           start_y: int, cellsize: int, color: int) -> None:
        """
        Dessine Pac-Man à l'aide de sa vraie texture orientée
        avec la bouche animée et la gestion de la transparence alpha.
        """
        cx = start_x + (self.pos_x * cellsize) + (cellsize // 2)
        cy = start_y + (self.pos_y * cellsize) + (cellsize // 2)
        target_size = max(8, int(cellsize * 0.9))

        r_idx = self.direction % 4
        mouth_sequence = [0, 1, 2, 3]
        c_idx = mouth_sequence[self.current_frame % 4]

        if self.texture_argb is not None:
            tile = self.texture_argb[r_idx * 64:(r_idx + 1) * 64,
                                     c_idx * 64:(c_idx + 1) * 64]

            idx_y = (np.arange(target_size) * 64 // target_size).astype(int)
            idx_x = (np.arange(target_size) * 64 // target_size).astype(int)
            scaled_tile = tile[np.ix_(idx_y, idx_x)]

            dst_x1 = cx - target_size // 2
            dst_y1 = cy - target_size // 2
            dst_x2 = dst_x1 + target_size
            dst_y2 = dst_y1 + target_size

            h_scr, w_scr = pixels.shape
            v_y1 = max(0, dst_y1)
            v_y2 = min(h_scr, dst_y2)
            v_x1 = max(0, dst_x1)
            v_x2 = min(w_scr, dst_x2)

            if v_y2 > v_y1 and v_x2 > v_x1:
                src_y1 = v_y1 - dst_y1
                src_y2 = src_y1 + (v_y2 - v_y1)
                src_x1 = v_x1 - dst_x1
                src_x2 = src_x1 + (v_x2 - v_x1)

                sub_tile = scaled_tile[src_y1:src_y2, src_x1:src_x2]

                if self.is_powered_up and ((self.power_timer // 5) % 2 == 0):
                    # Flashing cyan effect when powered up
                    sub_tile = np.where(sub_tile & 0xFF000000 != 0, 0xFF00FFFF, sub_tile)

                alpha = (sub_tile >> 24) & 0xFF

                mask_opaque = (alpha == 255)
                mask_blend = (alpha > 0) & (alpha < 255)

                dst_slice = pixels[v_y1:v_y2, v_x1:v_x2]
                dst_slice[mask_opaque] = sub_tile[mask_opaque]

                if np.any(mask_blend):
                    a_val = alpha[mask_blend].astype(np.uint32)
                    inv_a = 255 - a_val
                    sf = sub_tile[mask_blend]
                    bg = dst_slice[mask_blend]

                    r_fg = (sf >> 16) & 0xFF
                    g_fg = (sf >> 8) & 0xFF
                    b_fg = sf & 0xFF
                    r_bg = (bg >> 16) & 0xFF
                    g_bg = (bg >> 8) & 0xFF
                    b_bg = bg & 0xFF

                    r_fin = (r_fg * a_val + r_bg * inv_a) // 255
                    g_fin = (g_fg * a_val + g_bg * inv_a) // 255
                    b_fin = (b_fg * a_val + b_bg * inv_a) // 255
                    dst_slice[mask_blend] = (0xFF << 24) | (r_fin << 16) | (g_fin << 8) | b_fin
        else:
            radius = max(3, int(cellsize * 0.45))
            h_scr, w_scr = pixels.shape
            draw_col = 0xFFFFDD00 if not self.is_powered_up else 0xFF00FFFF
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    if dx * dx + dy * dy <= radius * radius:
                        px, py = cx + dx, cy + dy
                        if 0 <= px < w_scr and 0 <= py < h_scr:
                            pixels[py, px] = draw_col

    def draw_player(self, renderer, scale: int) -> None:
        """Affiche le sprite SDL2 (si vous utilisez une feuille de sprites)."""
        screen_x = (self.pos_x - self.cam.offset_x) * scale
        screen_y = (self.pos_y - self.cam.offset_y) * scale

        if self.key_w: frame_offset = 0
        elif self.key_d: frame_offset = 4
        elif self.key_s: frame_offset = 8
        elif self.key_a: frame_offset = 12
        else: frame_offset = 0

        draw_sprite_sheet(renderer, self.sprite, screen_x, screen_y,
                          self.current_frame + frame_offset, scale)
