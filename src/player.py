import math
import ctypes
from typing import Any
import sdl2
from src.camera import Camera
from src.image import Image
from src.drawing_methods import draw_sprite_sheet
from src.bullet import Bullet
from src.game_state import GameConfig
import numpy as np
from src.ghost import BASE_GHOST_SPEED, VULNERABLE_DURATION

DIR_MAP = {
    0: (1, 0, 2),   # EAST
    1: (-1, 0, 8),  # WEST
    2: (0, -1, 1),  # NORTH
    3: (0, 1, 4),   # SOUTH
}
OPPOSITE_DIR = {0: 1, 1: 0, 2: 3, 3: 2}


def _can_move(x: int, y: int, direction: int,
              maze_matrix: list[list[int]],
              ignore_walls: bool = False) -> bool:
    """Check if movement in a given direction is valid from current cell.

    Args:
        x: Current cell X coordinate.
        y: Current cell Y coordinate.
        direction: Movement direction (0=East, 1=West, 2=North, 3=South).
        maze_matrix: 2D grid matrix with bitmask wall information.
        ignore_walls: If True, walls are ignored (for noclip mode).

    Returns:
        True if movement is within bounds and unobstructed, False otherwise.
    """
    maze_h = len(maze_matrix)
    maze_w = len(maze_matrix[0]) if maze_h > 0 else 0
    if not (0 <= y < maze_h and 0 <= x < maze_w):
        return False
    dx, dy, wall_bit = DIR_MAP[direction]
    if not ignore_walls:
        curr_cell = maze_matrix[y][x]
        if (curr_cell & wall_bit) != 0:
            return False
    nx, ny = x + dx, y + dy
    if not (0 <= ny < maze_h and 0 <= nx < maze_w):
        return False
    return True


class CsPlayer:
    def __init__(self, sprite: Image, cam: Camera, config: GameConfig) -> None:
        """Initialize the Counter-Strike player state and controls.

        Args:
            sprite: Player sprite sheet image.
            cam: Camera instance tracking player position.
            config: Game configuration options.
        """
        self.config = config
        self.pos_x: int = 0
        self.pos_y: int = 0
        self.can_move: bool = True
        self.can_collide: bool = True
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
        self.left_mouse_click: int
        self.bullet_lst: list[Bullet] = []
        self.can_shoot: bool = False
        self.shoot_timer: float = 4

    def update(self, dt: float) -> None:
        """Update animation frame and shooting cooldown timer.

        Args:
            dt: Delta time elapsed since last frame.
        """
        self.tick_counter += 1
        if self.tick_counter >= self.animation_speed:
            self.tick_counter = 0
            self.current_frame += 1
            self.current_frame = self.current_frame % self.frame_number
        if self.shoot_timer > 0:
            self.shoot_timer -= dt
            self.can_shoot = False
        elif self.shoot_timer < 0:
            self.can_shoot = True

    def draw_player(self, renderer: sdl2.render.SDL_Renderer,
                    scale: int, mouse_x: int,
                    mouse_y: int) -> None:
        """Draw player sprite oriented toward the mouse cursor position.

        Args:
            renderer: SDL renderer instance.
            scale: Drawing scale factor.
            mouse_x: Screen X coordinate of the mouse cursor.
            mouse_y: Screen Y coordinate of the mouse cursor.
        """
        pos_x = (self.pos_x - self.cam.offset_x) * scale
        pos_y = (self.pos_y - self.cam.offset_y) * scale
        dx = mouse_x - pos_x
        dy = mouse_y - pos_y
        angle_rad = math.atan2(dy, dx)
        angle = math.degrees(angle_rad)
        angle = (angle + 360) % 360
        direction_index = int(((angle + 22.5) % 360) // 45)
        if direction_index == 5:
            draw_sprite_sheet(renderer, self.sprite, pos_x, pos_y,
                              self.current_frame + 125, scale)
        elif direction_index == 3:
            draw_sprite_sheet(renderer, self.sprite, pos_x, pos_y,
                              self.current_frame + 101, scale)
        elif direction_index == 1:
            draw_sprite_sheet(renderer, self.sprite, pos_x, pos_y,
                              self.current_frame + 150, scale)
        elif direction_index == 7:
            draw_sprite_sheet(renderer, self.sprite, pos_x, pos_y,
                              self.current_frame + 175, scale)
        elif direction_index == 6:
            draw_sprite_sheet(renderer, self.sprite, pos_x, pos_y,
                              self.current_frame + 75, scale)
        elif direction_index == 4:
            draw_sprite_sheet(renderer, self.sprite, pos_x, pos_y,
                              self.current_frame + 50, scale)
        elif direction_index == 0:
            draw_sprite_sheet(renderer, self.sprite, pos_x, pos_y,
                              self.current_frame + 26, scale)
        elif direction_index == 2:
            draw_sprite_sheet(renderer, self.sprite, pos_x, pos_y,
                              self.current_frame, scale)

    def shoot(self, renderer: sdl2.render.SDL_Renderer) -> None:
        """Spawn a bullet traveling toward mouse position if cooldown permits.

        Args:
            renderer: SDL renderer used for bullet textures.
        """
        mouse_x, mouse_y = ctypes.c_int(0), ctypes.c_int(0)
        left_mouse_click = sdl2.mouse.SDL_GetMouseState(ctypes.byref(mouse_x),
                                                        ctypes.byref(mouse_y))
        if left_mouse_click == 1 and self.can_shoot is True:
            self.shoot_timer = 0.3
            self.can_shoot = False
            new_bullet = Bullet(renderer, x=self.pos_x, y=self.pos_y)
            new_bullet.set_direction(mouse_x, mouse_y,
                                     self.config.screen_width,
                                     self.config.screen_height)
            self.bullet_lst.append(new_bullet)

    def draw_bullet_lst(self, offset_x: int, offset_y: int) -> None:
        """Render and advance all active bullets fired by the player.

        Args:
            offset_x: Camera horizontal offset.
            offset_y: Camera vertical offset.
        """
        for bullet in self.bullet_lst:
            bullet.draw_bullet(offset_x, offset_y)
            bullet.update_pos()

    def kill_bullet(self, tilemap: list[int]) -> None:
        """Remove bullets that exceeded range or collided with walls.

        Args:
            tilemap: Map tile layer data for wall collision checks.
        """
        i = 0
        for bullet in self.bullet_lst:
            if bullet.max_travel < 0:
                self.bullet_lst.pop(i)
            if self.check_bullet_collide_wall(
                                              int(bullet.x + bullet.speed),
                                              int(bullet.y + bullet.speed),
                                              tilemap
                                              ) is False:

                self.bullet_lst.pop(i)
        i += 1

    def check_bullet_collide_wall(self, pos_x: int, pos_y: int,
                                  tilemap: list[int]) -> bool:
        """Check if a bullet at given coordinates collides with any wall tile.

        Args:
            pos_x: Bullet X position.
            pos_y: Bullet Y position.
            tilemap: Map tile array.

        Returns:
            False if colliding with a solid tile, True otherwise.
        """
        x = 0
        y = 0
        tile_count = 0
        bullet_size: int = 32
        for tile in tilemap:
            if tile != 0:
                if (pos_x + bullet_size > x and pos_x < x + 32 and
                        pos_y + bullet_size > y and pos_y < y + 32):
                    return False
            tile_count += 1
            x += 32
            if tile_count > 39:
                x = 0
                tile_count = 0
                y += 32
        return True

    def check_bullet_collide_ennemy(self, lst_ennemy: list[Any],
                                    x: float, y: float) -> bool:
        """Check and resolve collision between bullet position and enemies.

        Args:
            lst_ennemy: List of active enemy objects.
            x: Bullet X position.
            y: Bullet Y position.

        Returns:
            True if an enemy was hit and removed, False otherwise.
        """
        bullet_size: int = 32
        i = 0
        for ennemy in lst_ennemy:
            if (ennemy.pos_x + bullet_size > x and ennemy.pos_x < x + 32 and
                    ennemy.pos_y + bullet_size > y and ennemy.pos_y < y + 32):
                lst_ennemy.pop(i)
                return True
            i += 1
        return False


class PacPlayer:
    _cached_texture_argb = None
    BASE_SPEED: float = BASE_GHOST_SPEED

    def __init__(self, sprite: Image | Any = None,
                 cam: Camera | Any = None) -> None:
        """Initialize the Pac-Man player with state and textures.

        Args:
            sprite: Optional player sprite image.
            cam: Optional camera instance.
        """
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
        self.noclip: bool = False

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
        """Get player grid X coordinate.

        Returns:
            Current grid X position.
        """
        return self._pos_x

    @pos_x.setter
    def pos_x(self, value: int) -> None:
        """Set player grid X coordinate and synchronize render position.

        Args:
            value: New grid X coordinate.
        """
        self._pos_x = int(value)
        self.target_x = self._pos_x
        self.render_x = float(self._pos_x)
        self.progress = 0.0
        self.is_moving = False

    @property
    def pos_y(self) -> int:
        """Get player grid Y coordinate.

        Returns:
            Current grid Y position.
        """
        return self._pos_y

    @pos_y.setter
    def pos_y(self, value: int) -> None:
        """Set player grid Y coordinate and synchronize render position.

        Args:
            value: New grid Y coordinate.
        """
        self._pos_y = int(value)
        self.target_y = self._pos_y
        self.render_y = float(self._pos_y)
        self.progress = 0.0
        self.is_moving = False

    def get_desired_direction(self) -> int | None:
        """Return the desired move direction from keys or buffered input.

        Returns:
            int | None: Direction index (0=Right, 1=Left, 2=Up, 3=Down) or
                None if no direction is requested.
        """
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
        """Update sprite animation frame and power-up timer.

        Args:
            dt: Delta time elapsed since last frame in seconds.
        """
        dt = min(max(dt, 0.0), 0.1)
        if self.is_moving:
            self.tick_counter += 1
            if self.tick_counter >= self.animation_speed:
                self.tick_counter = 0
                self.current_frame = (
                    self.current_frame + 1) % self.frame_number
        else:
            self.current_frame = 0

        if self.is_powered_up:
            self.power_timer -= dt
            if self.power_timer <= 0.0:
                self.is_powered_up = False
                self.power_timer = 0.0

    def _consume_item(self, items_matrix: list[list[int]],
                      game_state: Any = None, config: Any = None,
                      ghosts: Any = None) -> None:
        """Consume the pac-dot or energizer on the current tile.

        Args:
            items_matrix: 2D matrix containing tile items.
            game_state: Current game state to update score.
            config: Game configuration for scoring values.
            ghosts: List of ghost instances to make vulnerable.
        """
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
                        game_state: Any = None, config: Any = None,
                        ghosts: Any = None,
                        dt: float = 1.0 / 60.0) -> None:
        """Move Pac-Man continuously with direction buffering and turn logic.

        Args:
            maze_matrix: 2D matrix of maze walls and open paths.
            items_matrix: 2D matrix of dots and energizers.
            game_state: Current game state.
            config: Configuration dictionary or object.
            ghosts: List of ghost instances.
            dt: Delta time elapsed since last update.
        """
        if not self.can_move:
            return

        dt = min(max(dt, 0.0), 0.05)
        step = self.speed * dt

        desired = self.get_desired_direction()

        if self.is_moving:
            # 1. Demi-tour immédiat à 180° au milieu du couloir
            if desired is not None and desired == OPPOSITE_DIR.get(
                    self.direction, -1):
                self._pos_x, self.target_x = self.target_x, self._pos_x
                self._pos_y, self.target_y = self.target_y, self._pos_y
                self.progress = max(0.0, 1.0 - self.progress)
                self.direction = desired
                self.next_direction = None

            # 2. Avance
            self.progress += step
            if self.progress < 1.0:
                self.render_x = (
                    1.0 - self.progress
                    ) * self._pos_x + self.progress * self.target_x
                self.render_y = (
                    1.0 - self.progress
                    ) * self._pos_y + self.progress * self.target_y
            else:
                # Arrivé à la case cible
                self._pos_x = self.target_x
                self._pos_y = self.target_y
                excess = self.progress - 1.0
                self.progress = 0.0

                self._consume_item(items_matrix, game_state, config, ghosts)

                desired = self.get_desired_direction()
                if desired is not None and _can_move(self._pos_x, self._pos_y,
                                                     desired, maze_matrix,
                                                     self.noclip):
                    self.direction = desired
                    self.next_direction = None
                    dx, dy, _ = DIR_MAP[self.direction]
                    self.target_x = self._pos_x + dx
                    self.target_y = self._pos_y + dy
                    self.is_moving = True
                    self.progress = min(excess, 0.99)
                    self.render_x = (
                        1.0 - self.progress
                        ) * self._pos_x + self.progress * self.target_x
                    self.render_y = (
                        1.0 - self.progress
                        ) * self._pos_y + self.progress * self.target_y
                elif _can_move(self._pos_x, self._pos_y, self.direction,
                               maze_matrix, self.noclip):
                    dx, dy, _ = DIR_MAP[self.direction]
                    self.target_x = self._pos_x + dx
                    self.target_y = self._pos_y + dy
                    self.is_moving = True
                    self.progress = min(excess, 0.99)
                    self.render_x = (
                        1.0 - self.progress
                        ) * self._pos_x + self.progress * self.target_x
                    self.render_y = (
                        1.0 - self.progress
                        ) * self._pos_y + self.progress * self.target_y
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

            if desired is not None and _can_move(self._pos_x, self._pos_y,
                                                 desired, maze_matrix,
                                                 self.noclip):
                self.direction = desired
                self.next_direction = None
                dx, dy, _ = DIR_MAP[self.direction]
                self.target_x = self._pos_x + dx
                self.target_y = self._pos_y + dy
                self.is_moving = True
                self.progress = min(step, 0.99)
                self.render_x = (
                    1.0 - self.progress
                    ) * self._pos_x + self.progress * self.target_x
                self.render_y = (
                    1.0 - self.progress
                    ) * self._pos_y + self.progress * self.target_y
            elif (self.key_w or self.key_s or self.key_a or self.key_d
                  ) and _can_move(self._pos_x, self._pos_y, self.direction,
                                  maze_matrix, self.noclip):
                dx, dy, _ = DIR_MAP[self.direction]
                self.target_x = self._pos_x + dx
                self.target_y = self._pos_y + dy
                self.is_moving = True
                self.progress = min(step, 0.99)
                self.render_x = (
                    1.0 - self.progress
                    ) * self._pos_x + self.progress * self.target_x
                self.render_y = (
                    1.0 - self.progress
                    ) * self._pos_y + self.progress * self.target_y

    def draw_player_pixels(self, pixels: np.ndarray, start_x: int,
                           start_y: int, cellsize: int, color: int) -> None:
        """Draw Pac-Man at interpolated coordinates with animated mouth.

        Args:
            pixels: ARGB pixel buffer array to render into.
            start_x: Screen X pixel offset for maze origin.
            start_y: Screen Y pixel offset for maze origin.
            cellsize: Size of a single maze cell in pixels.
            color: Fallback color for drawing.
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

                if self.is_powered_up and (int(
                        self.power_timer * 10) % 2 == 0):
                    # Clignotement cyan pendant le super-pouvoir
                    sub_tile = np.where(sub_tile & 0xFF000000 != 0,
                                        0xFF00FFFF, sub_tile)

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
                    dst_slice[mask_blend] = (0xFF << 24) | (
                        r_fin << 16) | (g_fin << 8) | b_fin
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

    def draw_player(self, renderer: sdl2.render.SDL_Renderer,
                    scale: int) -> None:
        """Render the player sprite using SDL2 sprite sheet rendering.

        Args:
            renderer: SDL2 renderer context.
            scale: Pixel scaling factor.
        """
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
