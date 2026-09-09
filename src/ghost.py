import ctypes
import random
import numpy as np
import sdl2
import sdl2.sdlimage as sdim

VULNERABLE_DURATION: float = 7.0
RESPAWN_DURATION: float = 7.0
BASE_GHOST_SPEED: float = 3.0
VULNERABLE_SPEED_RATIO: float = 0.60
MAX_CHASE_PROBABILITY: float = 0.7


def _load_argb_array(filepath: str) -> np.ndarray:
    """Load an image file into a uint32 ARGB numpy array.

    Dark background pixels (RGB sum < 50) are masked to alpha=0.

    Args:
        filepath: Path to the image file.

    Returns:
        np.ndarray: 2D array of uint32 ARGB pixels.

    Raises:
        RuntimeError: If image loading or surface conversion fails.
    """
    path_bytes = filepath.encode('utf-8')
    surf = sdim.IMG_Load(path_bytes)
    if not surf:
        raise RuntimeError(
            f"Could not load image {filepath}: {sdim.IMG_GetError()}"
        )
    conv_surf = sdl2.SDL_ConvertSurfaceFormat(
        surf, sdl2.SDL_PIXELFORMAT_ARGB8888, 0
    )
    sdl2.SDL_FreeSurface(surf)
    h = conv_surf.contents.h
    pitch = conv_surf.contents.pitch
    ptr = ctypes.cast(
        conv_surf.contents.pixels, ctypes.POINTER(ctypes.c_uint32)
    )
    arr = np.ctypeslib.as_array(ptr, shape=(h, pitch // 4)).copy()
    sdl2.SDL_FreeSurface(conv_surf)

    r = (arr >> 16) & 0xFF
    g = (arr >> 8) & 0xFF
    b = arr & 0xFF
    rgb_sum = r.astype(int) + g.astype(int) + b.astype(int)
    dark_mask = rgb_sum < 50
    arr[dark_mask] = arr[dark_mask] & 0x00FFFFFF   # alpha=0 sur fond sombre
    return arr


def _get_segs(counts: np.ndarray) -> list[tuple[int, int]]:
    """Find contiguous segments of positive values in an array.

    Args:
        counts: 1D array of counts or flags.

    Returns:
        list[tuple[int, int]]: List of (start_index, end_index) tuples.
    """
    segs: list[tuple[int, int]] = []
    in_s = False
    st = 0
    for i, c in enumerate(counts):
        if c > 0 and not in_s:
            in_s = True
            st = i
        elif c == 0 and in_s:
            in_s = False
            segs.append((st, i - 1))
    if in_s:
        segs.append((st, len(counts) - 1))
    return segs


def _scale_tile_64(tile: np.ndarray) -> np.ndarray:
    """Resample a sub-array to 64x64 using nearest-neighbor interpolation.

    Args:
        tile: 2D numpy array of pixels.

    Returns:
        np.ndarray: Scaled 64x64 pixel array.
    """
    h, w = tile.shape
    iy = (np.arange(64) * h // 64).astype(int)
    ix = (np.arange(64) * w // 64).astype(int)
    return tile[np.ix_(iy, ix)]


def extract_ghost_frames(filepath: str) -> list[list[np.ndarray]]:
    """Extract directional animation frames from a ghost sprite sheet.

    Extracts 4 directions x 2 animation frames scaled to 64x64 ARGB.

    Args:
        filepath: Path to the ghost sprite sheet.

    Returns:
        list[list[np.ndarray]]: Nested list of frames [direction][frame].
    """
    arr = _load_argb_array(filepath)
    h = arr.shape[0]

    alpha = (arr >> 24) & 0xFF
    non_bg = alpha > 0
    r_segs = _get_segs(non_bg.sum(axis=1))
    c_segs = _get_segs(non_bg.sum(axis=0))

    if len(r_segs) != 4 or len(c_segs) != 2:
        w = arr.shape[1]
        cell_h, cell_w = h // 4, w // 2
        r_segs = [(r * cell_h, (r + 1) * cell_h - 1) for r in range(4)]
        c_segs = [(c * cell_w, (c + 1) * cell_w - 1) for c in range(2)]

    frames: list[list[np.ndarray]] = []
    for r1, r2 in r_segs:
        row: list[np.ndarray] = []
        for c1, c2 in c_segs:
            sub = arr[r1:r2 + 1, c1:c2 + 1].copy()
            row.append(_scale_tile_64(sub))
        frames.append(row)
    return frames


def extract_dead_ghost_frames(filepath: str) -> list[np.ndarray]:
    """Extract animation frames from the vulnerable ghost sprite sheet.

    Args:
        filepath: Path to the vulnerable sprite image (dead_ghost.png).

    Returns:
        list[np.ndarray]: List of 2 animation frames scaled to 64x64 ARGB.
    """
    arr = _load_argb_array(filepath)

    r = (arr >> 16) & 0xFF
    g = (arr >> 8) & 0xFF
    b = arr & 0xFF
    rgb_sum = r.astype(int) + g.astype(int) + b.astype(int)
    non_bg = rgb_sum > 50
    row_counts = non_bg.sum(axis=1)
    col_counts = non_bg.sum(axis=0)

    rows_idx = np.where(row_counts > 0)[0]
    r1_all, r2_all = int(rows_idx[0]), int(rows_idx[-1])

    c_segs = _get_segs(col_counts)
    c_segs = [s for s in c_segs if (s[1] - s[0] + 1) >= 20]
    if len(c_segs) != 2:
        w = arr.shape[1]
        c_segs = [(0, w // 2 - 1), (w // 2, w - 1)]

    frames: list[np.ndarray] = []
    for c1, c2 in c_segs:
        sub = arr[r1_all:r2_all + 1, c1:c2 + 1].copy()
        frames.append(_scale_tile_64(sub))
    return frames


def _blit_tile(pixels: np.ndarray, tile: np.ndarray,
               cx: int, cy: int, size: int) -> None:
    """Blend a 64x64 ARGB tile centered at (cx, cy) into pixel buffer.

    Args:
        pixels: Destination ARGB pixel matrix.
        tile: 64x64 ARGB source tile.
        cx: Center X coordinate in pixels.
        cy: Center Y coordinate in pixels.
        size: Target width and height in pixels.
    """
    if size <= 0:
        return
    iy = (np.arange(size) * 64 // size).astype(int)
    ix = (np.arange(size) * 64 // size).astype(int)
    scaled = tile[np.ix_(iy, ix)]

    x1, y1 = cx - size // 2, cy - size // 2
    x2, y2 = x1 + size, y1 + size
    h_scr, w_scr = pixels.shape
    vy1, vy2 = max(0, y1), min(h_scr, y2)
    vx1, vx2 = max(0, x1), min(w_scr, x2)
    if vy2 <= vy1 or vx2 <= vx1:
        return

    sy1 = vy1 - y1
    sy2 = sy1 + (vy2 - vy1)
    sx1 = vx1 - x1
    sx2 = sx1 + (vx2 - vx1)

    sub = scaled[sy1:sy2, sx1:sx2]
    alpha = (sub >> 24) & 0xFF
    mask_op = alpha == 255
    mask_bl = (alpha > 0) & (alpha < 255)

    dst = pixels[vy1:vy2, vx1:vx2]
    dst[mask_op] = sub[mask_op]

    if np.any(mask_bl):
        av = alpha[mask_bl].astype(np.uint32)
        ia = 255 - av
        sf = sub[mask_bl]
        bg = dst[mask_bl]
        rf = ((sf >> 16) & 0xFF) * av + ((bg >> 16) & 0xFF) * ia
        gf = ((sf >> 8) & 0xFF) * av + ((bg >> 8) & 0xFF) * ia
        bf = (sf & 0xFF) * av + (bg & 0xFF) * ia
        dst[mask_bl] = (0xFF << 24) | ((rf // 255) << 16) | (
            (gf // 255) << 8) | (bf // 255)


class Ghost:
    """Represent a Pac-Man ghost with normal, vulnerable, and dead states.

    Attributes:
        color_name: Name of the ghost color identifier.
        base_speed: Default movement speed in grid cells per second.
        is_vulnerable: Whether ghost is currently in vulnerable state.
        is_dead: Whether ghost was eaten and is waiting to respawn.
    """

    _dead_frames: list[np.ndarray] | None = None
    _dead_frames_path: str = "assets/dead_ghost.png"

    def __init__(self, color_name: str, sprite_path: str,
                 pos_x: int = 0, pos_y: int = 0) -> None:
        """Initialize a Ghost instance with appearance and coordinates.

        Args:
            color_name: Identifier name for the ghost's color/identity.
            sprite_path: Filepath to the ghost's sprite sheet.
            pos_x: Initial grid X position.
            pos_y: Initial grid Y position.
        """
        self.color_name: str = color_name
        self._pos_x: int = int(pos_x)
        self._pos_y: int = int(pos_y)
        self.target_x: int = int(pos_x)
        self.target_y: int = int(pos_y)
        self.render_x: float = float(pos_x)
        self.render_y: float = float(pos_y)
        self.progress: float = 0.0
        self.is_moving: bool = False

        self.direction: int = 0   # 0=Right 1=Left 2=Up 3=Down

        # Vitesse
        self.base_speed: float = BASE_GHOST_SPEED
        self.vulnerable_speed_ratio: float = VULNERABLE_SPEED_RATIO
        self.move_cooldown: int = int(round(60.0 / self.base_speed))
        self.move_tick: int = 0

        # Animation
        self.current_frame: int = 0
        self.tick_counter: int = 0
        self.animation_speed: int = 10

        # Sprite normal (4 dirs × 2 frames)
        self.frames: list[list[np.ndarray]] = extract_ghost_frames(sprite_path)

        # Sprite vulnérable (partagé, chargé une seule fois)
        if Ghost._dead_frames is None:
            Ghost._dead_frames = extract_dead_ghost_frames(
                Ghost._dead_frames_path
            )

        # État
        self.is_vulnerable: bool = False
        self.vulnerable_timer: float = 0.0
        self.is_dead: bool = False
        self.is_permanently_dead: bool = False
        self.respawn_timer: float = 0.0
        self.corners_to_respawn: list[tuple[int, int]] = []
        self.last_dt: float = 1.0 / 60.0
        self.player_pos: tuple[int, int] | None = None
        self.chase_probability: float = 0.0

    @property
    def pos_x(self) -> int:
        """Get the ghost's grid X coordinate.

        Returns:
            Current grid X position.
        """
        return self._pos_x

    @pos_x.setter
    def pos_x(self, val: int) -> None:
        """Set the ghost's grid X coordinate and synchronize render position.

        Args:
            val: New grid X coordinate.
        """
        self._pos_x = int(val)
        self.target_x = self._pos_x
        self.render_x = float(self._pos_x)
        self.progress = 0.0
        self.is_moving = False

    @property
    def pos_y(self) -> int:
        """Get the ghost's grid Y coordinate.

        Returns:
            Current grid Y position.
        """
        return self._pos_y

    @pos_y.setter
    def pos_y(self, val: int) -> None:
        """Set the ghost's grid Y coordinate and synchronize render position.

        Args:
            val: New grid Y coordinate.
        """
        self._pos_y = int(val)
        self.target_y = self._pos_y
        self.render_y = float(self._pos_y)
        self.progress = 0.0
        self.is_moving = False

    @property
    def current_speed(self) -> float:
        """Return current speed in cells per second based on state."""
        if self.is_vulnerable:
            return self.base_speed * self.vulnerable_speed_ratio
        return self.base_speed

    # ------------------------------------------------------------------ #
    #  MISE À JOUR                                                         #
    # ------------------------------------------------------------------ #

    def update(self, dt: float = 1.0 / 60.0,
               player_pos: tuple[int, int] | None = None,
               time_left: float | None = None,
               max_time: float | None = None) -> None:
        """Update animation frames and vulnerable or respawn timers.

        Args:
            dt: Delta time elapsed since last update in seconds.
            player_pos: Current player grid coordinates (x, y).
            time_left: Remaining level time in seconds.
            max_time: Total level time in seconds.
        """
        dt = min(max(dt, 0.0), 0.1)
        self.last_dt = dt
        self.player_pos = player_pos
        if time_left is not None and max_time is not None and max_time > 0:
            elapsed_ratio = 1.0 - (time_left / max_time)
            self.chase_probability = min(
                MAX_CHASE_PROBABILITY, max(0.0, elapsed_ratio)
                * MAX_CHASE_PROBABILITY / 0.9
            )
        else:
            self.chase_probability = 0.0

        # Timer de réapparition
        if self.is_dead:
            if self.is_permanently_dead:
                return
            self.respawn_timer -= dt
            if self.respawn_timer <= 0.0:
                self.is_dead = False
                self.respawn_timer = 0.0
                self.is_vulnerable = False
                self.vulnerable_timer = 0.0
                if self.corners_to_respawn:
                    candidates = self.corners_to_respawn
                    if player_pos is not None and len(candidates) > 1:
                        non_player = [c for c in candidates if c != player_pos]
                        if non_player:
                            candidates = non_player
                    rx, ry = random.choice(candidates)
                    self._pos_x = rx
                    self._pos_y = ry
                    self.target_x = rx
                    self.target_y = ry
                    self.render_x = float(rx)
                    self.render_y = float(ry)
                    self.progress = 0.0
                    self.is_moving = False
                self.direction = random.randint(0, 3)
            return

        # Timer de vulnérabilité
        if self.is_vulnerable:
            self.vulnerable_timer -= dt
            if self.vulnerable_timer <= 0.0:
                self.is_vulnerable = False
                self.vulnerable_timer = 0.0

        # Animation du sprite
        self.tick_counter += 1
        anim_speed = self.animation_speed if not self.is_vulnerable else int(
                self.animation_speed * 1.5)
        if self.tick_counter >= anim_speed:
            self.tick_counter = 0
            self.current_frame = (self.current_frame + 1) % 2

    def make_vulnerable(self) -> None:
        """Activate vulnerable state for VULNERABLE_DURATION seconds."""
        if not self.is_dead:
            self.is_vulnerable = True
            self.vulnerable_timer = VULNERABLE_DURATION

    def kill(self, corners: list[tuple[int, int]]) -> None:
        """Kill the ghost, making it invisible until it respawns in a corner.

        Args:
            corners: List of valid corner (x, y) coordinates for respawn.
        """
        self.is_dead = True
        self.is_permanently_dead = False
        self.is_vulnerable = False
        self.vulnerable_timer = 0.0
        self.respawn_timer = RESPAWN_DURATION
        self.corners_to_respawn = list(corners) if corners else [(0, 0)]
        self._pos_x = -1
        self._pos_y = -1
        self.target_x = -1
        self.target_y = -1
        self.render_x = -100.0
        self.render_y = -100.0
        self.progress = 0.0
        self.is_moving = False

    def kill_permanently(self) -> None:
        """Permanently kill the ghost for the remainder of the level."""
        self.is_dead = True
        self.is_permanently_dead = True
        self.is_vulnerable = False
        self.vulnerable_timer = 0.0
        self.respawn_timer = 0.0
        self._pos_x = -1
        self._pos_y = -1
        self.target_x = -1
        self.target_y = -1
        self.render_x = -100.0
        self.render_y = -100.0
        self.progress = 0.0
        self.is_moving = False

    # ------------------------------------------------------------------ #
    #  DÉPLACEMENT FLUIDE                                                  #
    # ------------------------------------------------------------------ #

    def _choose_next_cell(
        self,
        maze_matrix: list[list[int]],
        allow_reverse: bool = False
    ) -> tuple[int, int, int] | None:
        """Select the next valid adjacent cell, avoiding instant reversal.

        Args:
            maze_matrix: 2D maze representation with wall bitmasks.
            allow_reverse: Whether 180-degree turn is permitted.

        Returns:
            tuple[int, int, int] | None: (direction, next_x, next_y) or None.
        """
        NORTH, EAST, SOUTH, WEST = 1, 2, 4, 8
        maze_height = len(maze_matrix)
        maze_width = len(maze_matrix[0]) if maze_height > 0 else 0

        if not (
                0 <= self._pos_y < maze_height
                and 0 <= self._pos_x < maze_width
                ):
            return None

        curr_cell = maze_matrix[self._pos_y][self._pos_x]
        dir_moves = {
            0: (1, 0, EAST),
            1: (-1, 0, WEST),
            2: (0, -1, NORTH),
            3: (0, 1, SOUTH)
        }
        opposite = {0: 1, 1: 0, 2: 3, 3: 2}

        valid_moves = []
        for d, (dx, dy, wall_bit) in dir_moves.items():
            if not (curr_cell & wall_bit):
                nx, ny = self._pos_x + dx, self._pos_y + dy
                if 0 <= nx < maze_width and 0 <= ny < maze_height:
                    valid_moves.append((d, nx, ny))

        if not valid_moves:
            return None

        if not allow_reverse:
            non_opp = [
                m for m in valid_moves
                if m[0] != opposite.get(self.direction, -1)
            ]
            pool = non_opp if non_opp else valid_moves
        else:
            pool = valid_moves

        if self.player_pos is not None and self.is_vulnerable:
            player_x, player_y = self.player_pos
            best_distance = max(
                abs(nx - player_x) + abs(ny - player_y)
                for _, nx, ny in pool
            )
            pool = [
                move for move in pool
                if abs(move[1] - player_x) + abs(move[2] - player_y)
                == best_distance
            ]
        elif (self.player_pos is not None
              and random.random() < self.chase_probability):
            player_x, player_y = self.player_pos
            best_distance = min(
                abs(nx - player_x) + abs(ny - player_y)
                for _, nx, ny in pool
            )
            pool = [
                move for move in pool
                if abs(move[1] - player_x) + abs(move[2] - player_y)
                == best_distance
            ]

        return random.choice(pool)

    def move_step(self, maze_matrix: list[list[int]],
                  dt: float | None = None) -> None:
        """Execute one step of smooth continuous movement between cells.

        Args:
            maze_matrix: 2D maze representation with wall bitmasks.
            dt: Delta time elapsed since last update.
        """
        if self.is_dead:
            self.render_x = -100.0
            self.render_y = -100.0
            self.is_moving = False
            return

        delta = self.last_dt if dt is None else dt
        delta = min(max(delta, 0.0), 0.05)
        step = self.current_speed * delta

        if self.is_moving:
            self.progress += step
            if self.progress < 1.0:
                self.render_x = (
                    1.0 - self.progress
                    ) * self._pos_x + self.progress * self.target_x
                self.render_y = (
                    1.0 - self.progress
                    ) * self._pos_y + self.progress * self.target_y
            else:
                self._pos_x = self.target_x
                self._pos_y = self.target_y
                excess = self.progress - 1.0
                self.progress = 0.0

                nxt = self._choose_next_cell(maze_matrix, allow_reverse=False)
                if nxt is not None:
                    cdir, nx, ny = nxt
                    self.direction = cdir
                    self.target_x = nx
                    self.target_y = ny
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
                    self.render_x = float(self._pos_x)
                    self.render_y = float(self._pos_y)
        else:
            nxt = self._choose_next_cell(maze_matrix, allow_reverse=False)
            if nxt is not None:
                cdir, nx, ny = nxt
                self.direction = cdir
                self.target_x = nx
                self.target_y = ny
                self.is_moving = True
                self.progress = min(step, 0.99)
                self.render_x = (
                    1.0 - self.progress
                    ) * self._pos_x + self.progress * self.target_x
                self.render_y = (
                    1.0 - self.progress
                    ) * self._pos_y + self.progress * self.target_y
            else:
                self.render_x = float(self._pos_x)
                self.render_y = float(self._pos_y)

    def move_normal(self, maze_matrix: list[list[int]],
                    dt: float | None = None) -> None:
        """Move the ghost in normal mode at base speed.

        Args:
            maze_matrix: 2D maze representation with wall bitmasks.
            dt: Delta time elapsed since last update.
        """
        self.move_step(maze_matrix, dt)

    def move_vulnerable(self, maze_matrix: list[list[int]],
                        dt: float | None = None) -> None:
        """Move the ghost in vulnerable mode at reduced speed.

        Args:
            maze_matrix: 2D maze representation with wall bitmasks.
            dt: Delta time elapsed since last update.
        """
        self.move_step(maze_matrix, dt)

    # ------------------------------------------------------------------ #
    #  RENDU                                                               #
    # ------------------------------------------------------------------ #

    def draw_ghost_pixels(self, pixels: np.ndarray, start_x: int,
                          start_y: int, cellsize: int) -> None:
        """Draw the ghost into pixel buffer at interpolated position.

        Args:
            pixels: ARGB pixel buffer array.
            start_x: Screen X pixel offset for maze origin.
            start_y: Screen Y pixel offset for maze origin.
            cellsize: Size of a single maze cell in pixels.
        """
        if self.is_dead:
            return

        cx = int(start_x + (self.render_x * cellsize) + (cellsize // 2))
        cy = int(start_y + (self.render_y * cellsize) + (cellsize // 2))
        target_size = max(8, int(cellsize * 0.55))

        if self.is_vulnerable and Ghost._dead_frames is not None:
            tile = Ghost._dead_frames[self.current_frame % 2]
            _blit_tile(pixels, tile, cx, cy, target_size)
        else:
            dir_to_row = {0: 1, 1: 3, 2: 0, 3: 2}
            r_idx = dir_to_row.get(self.direction, 1)
            c_idx = self.current_frame % 2
            tile = self.frames[r_idx][c_idx]
            _blit_tile(pixels, tile, cx, cy, target_size)
