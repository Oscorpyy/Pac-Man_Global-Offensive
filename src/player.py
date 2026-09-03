import math
import numpy as np
from src.camera import Camera
from src.image import Image
from src.drawing_methods import draw_sprite_sheet
from src.ghost import BASE_GHOST_SPEED, VULNERABLE_DURATION

DIR_MAP = {
    0: (1, 0, 2),   # EAST
    1: (-1, 0, 8),  # WEST
    2: (0, -1, 1),  # NORTH
    3: (0, 1, 4),   # SOUTH
}
OPPOSITE_DIR = {0: 1, 1: 0, 2: 3, 3: 2}


def _can_move(x: int, y: int, direction: int,
              maze_matrix: list[list[int]]) -> bool:
    maze_h = len(maze_matrix)
    maze_w = len(maze_matrix[0]) if maze_h > 0 else 0
    if not (0 <= y < maze_h and 0 <= x < maze_w):
        return False
    dx, dy, wall_bit = DIR_MAP[direction]
    curr_cell = maze_matrix[y][x]
    if (curr_cell & wall_bit) != 0:
        return False
    nx, ny = x + dx, y + dy
    if not (0 <= ny < maze_h and 0 <= nx < maze_w):
        return False
    return True


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

    def draw_player(self, renderer, scale: int, mouse_x: int, mouse_y: int) -> None:
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
    _cached_texture_argb = None
    BASE_SPEED: float = BASE_GHOST_SPEED

    def __init__(self, sprite=None, cam=None) -> None:
        self._pos_x: int = 0
        self._pos_y: int = 0
        self.target_x: int = 0
        self.target_y: int = 0
        self.render_x: float = 0.0
        self.render_y: float = 0.0
        self.progress: float = 0.0
        self.is_moving: bool = False

        self.speed: float = BASE_GHOST_SPEED
        self.move_cooldown: int = int(round(60.0 / self.speed))
        self.move_tick: int = 0

        self.can_move: bool = True
        self.can_collide: bool = True

        self.sprite = sprite
        self.cam = cam

        self.current_frame: int = 0
        self.frame_number: int = 4
        self.animation_speed: int = 8
        self.tick_counter: int = 0

        self.key_w: bool = False
        self.key_s: bool = False
        self.key_a: bool = False
        self.key_d: bool = False

        self.direction: int = 0  # 0=Right, 1=Left, 2=Up, 3=Down
        self.next_direction: int | None = None
        self.is_powered_up: bool = False
        self.power_timer: float = 0.0

        if PacPlayer._cached_texture_argb is None:
            try:
                import sdl2
                import sdl2.sdlimage as sdim
                import ctypes
                surf = sdim.IMG_Load(b"assets/pacman.png")
                if surf:
                    conv_surf = sdl2.SDL_ConvertSurfaceFormat(
                        surf, sdl2.SDL_PIXELFORMAT_ARGB8888, 0)
                    sdl2.SDL_FreeSurface(surf)
                    if conv_surf:
                        h = conv_surf.contents.h
                        pitch = conv_surf.contents.pitch
                        ptr = ctypes.cast(
                            conv_surf.contents.pixels,
                            ctypes.POINTER(ctypes.c_uint32)
                        )
                        PacPlayer._cached_texture_argb = np.ctypeslib.as_array(
                            ptr, shape=(h, pitch // 4)).copy()
                        sdl2.SDL_FreeSurface(conv_surf)
            except Exception as e:
                print(f"Warning: could not load pacman texture: {e}")
                PacPlayer._cached_texture_argb = None
        self.texture_argb = PacPlayer._cached_texture_argb

    @property
    def pos_x(self) -> int:
        return self._pos_x

    @pos_x.setter
    def pos_x(self, value: int) -> None:
        self._pos_x = int(value)
        self.target_x = self._pos_x
        self.render_x = float(self._pos_x)
        self.progress = 0.0
        self.is_moving = False

    @property
    def pos_y(self) -> int:
        return self._pos_y

    @pos_y.setter
    def pos_y(self, value: int) -> None:
        self._pos_y = int(value)
        self.target_y = self._pos_y
        self.render_y = float(self._pos_y)
        self.progress = 0.0
        self.is_moving = False

    def get_desired_direction(self) -> int | None:
        """Retourne la direction souhaitée selon les touches maintenues ou bufférisées."""
        if self.key_w:
            return 2
        if self.key_s:
            return 3
        if self.key_a:
            return 1
        if self.key_d:
            return 0
        return self.next_direction

    def update(self, dt: float = 1.0 / 60.0) -> None:
        """Met à jour le compteur d'animation du sprite et le timer de vulnérabilité."""
        dt = min(max(dt, 0.0), 0.1)
        if self.is_moving:
            self.tick_counter += 1
            if self.tick_counter >= self.animation_speed:
                self.tick_counter = 0
                self.current_frame = (self.current_frame + 1) % self.frame_number
        else:
            self.current_frame = 0

        if self.is_powered_up:
            self.power_timer -= dt
            if self.power_timer <= 0.0:
                self.is_powered_up = False
                self.power_timer = 0.0

    def _consume_item(self, items_matrix: list[list[int]],
                      game_state=None, config=None,
                      ghosts=None) -> None:
        """Consomme la pac-gomme ou super-pacgomme sur la case courante."""
        maze_h = len(items_matrix)
        maze_w = len(items_matrix[0]) if maze_h > 0 else 0
        if 0 <= self._pos_y < maze_h and 0 <= self._pos_x < maze_w:
            item = items_matrix[self._pos_y][self._pos_x]
            if item == 1:  # Pacgum
                items_matrix[self._pos_y][self._pos_x] = 0
                if game_state is not None and config is not None:
                    pts = (config.points_per_pacgum
                           if config.points_per_pacgum is not None else 10)
                    game_state.point += int(pts)
            elif item == 2:  # Super-pacgum
                items_matrix[self._pos_y][self._pos_x] = 0
                self.is_powered_up = True
                self.power_timer = VULNERABLE_DURATION
                if ghosts is not None:
                    for ghost in ghosts:
                        ghost.make_vulnerable()
                if game_state is not None and config is not None:
                    pts = (config.points_per_super_pacgum
                           if config.points_per_super_pacgum is not None
                           else 50)
                    game_state.point += int(pts)

    def handle_movement(self, maze_matrix: list[list[int]],
                        items_matrix: list[list[int]],
                        game_state=None, config=None,
                        ghosts=None, dt: float = 1.0 / 60.0) -> None:
        """
        Déplace Pac-Man de façon fluide et continue (vitesse calquée sur les fantômes normaux).
        Gère le demi-tour immédiat et l'input buffering aux virages.
        """
        if not self.can_move:
            return

        dt = min(max(dt, 0.0), 0.05)
        step = self.speed * dt

        desired = self.get_desired_direction()

        if self.is_moving:
            # 1. Demi-tour immédiat à 180° au milieu du couloir
            if desired is not None and desired == OPPOSITE_DIR.get(self.direction, -1):
                self._pos_x, self.target_x = self.target_x, self._pos_x
                self._pos_y, self.target_y = self.target_y, self._pos_y
                self.progress = max(0.0, 1.0 - self.progress)
                self.direction = desired
                self.next_direction = None

            # 2. Avance
            self.progress += step
            if self.progress < 1.0:
                self.render_x = (1.0 - self.progress) * self._pos_x + self.progress * self.target_x
                self.render_y = (1.0 - self.progress) * self._pos_y + self.progress * self.target_y
            else:
                # Arrivé à la case cible
                self._pos_x = self.target_x
                self._pos_y = self.target_y
                excess = self.progress - 1.0
                self.progress = 0.0

                self._consume_item(items_matrix, game_state, config, ghosts)

                desired = self.get_desired_direction()
                if desired is not None and _can_move(self._pos_x, self._pos_y, desired, maze_matrix):
                    self.direction = desired
                    self.next_direction = None
                    dx, dy, _ = DIR_MAP[self.direction]
                    self.target_x = self._pos_x + dx
                    self.target_y = self._pos_y + dy
                    self.is_moving = True
                    self.progress = min(excess, 0.99)
                    self.render_x = (1.0 - self.progress) * self._pos_x + self.progress * self.target_x
                    self.render_y = (1.0 - self.progress) * self._pos_y + self.progress * self.target_y
                elif _can_move(self._pos_x, self._pos_y, self.direction, maze_matrix):
                    dx, dy, _ = DIR_MAP[self.direction]
                    self.target_x = self._pos_x + dx
                    self.target_y = self._pos_y + dy
                    self.is_moving = True
                    self.progress = min(excess, 0.99)
                    self.render_x = (1.0 - self.progress) * self._pos_x + self.progress * self.target_x
                    self.render_y = (1.0 - self.progress) * self._pos_y + self.progress * self.target_y
                else:
                    self.is_moving = False
                    self.target_x = self._pos_x
                    self.target_y = self._pos_y
                    self.progress = 0.0
                    self.render_x = float(self._pos_x)
                    self.render_y = float(self._pos_y)

        else:
            self.render_x = float(self._pos_x)
            self.render_y = float(self._pos_y)
            self._consume_item(items_matrix, game_state, config, ghosts)

            if desired is not None and _can_move(self._pos_x, self._pos_y, desired, maze_matrix):
                self.direction = desired
                self.next_direction = None
                dx, dy, _ = DIR_MAP[self.direction]
                self.target_x = self._pos_x + dx
                self.target_y = self._pos_y + dy
                self.is_moving = True
                self.progress = min(step, 0.99)
                self.render_x = (1.0 - self.progress) * self._pos_x + self.progress * self.target_x
                self.render_y = (1.0 - self.progress) * self._pos_y + self.progress * self.target_y
            elif (self.key_w or self.key_s or self.key_a or self.key_d) and _can_move(self._pos_x, self._pos_y, self.direction, maze_matrix):
                dx, dy, _ = DIR_MAP[self.direction]
                self.target_x = self._pos_x + dx
                self.target_y = self._pos_y + dy
                self.is_moving = True
                self.progress = min(step, 0.99)
                self.render_x = (1.0 - self.progress) * self._pos_x + self.progress * self.target_x
                self.render_y = (1.0 - self.progress) * self._pos_y + self.progress * self.target_y

    def draw_player_pixels(self, pixels: np.ndarray, start_x: int,
                           start_y: int, cellsize: int, color: int) -> None:
        """
        Dessine Pac-Man à sa position interpolée avec sa texture orientée
        et la bouche animée.
        """
        cx = int(start_x + (self.render_x * cellsize) + (cellsize // 2))
        cy = int(start_y + (self.render_y * cellsize) + (cellsize // 2))
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

                if self.is_powered_up and (int(self.power_timer * 10) % 2 == 0):
                    # Clignotement cyan pendant le super-pouvoir
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

        if self.key_w:
            frame_offset = 0
        elif self.key_d:
            frame_offset = 4
        elif self.key_s:
            frame_offset = 8
        elif self.key_a:
            frame_offset = 12
        else:
            frame_offset = 0

        draw_sprite_sheet(renderer, self.sprite, screen_x, screen_y,
                          self.current_frame + frame_offset, scale)
