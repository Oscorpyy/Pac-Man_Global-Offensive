import sdl2
from sdl2 import sdlimage as sdim
from sdl2 import sdlttf as sttf
import numpy as np
from src.scene.helper import get_ptr
from src.game_state import GameConfig, GameState
from src.drawing_methods import clear_background, Button, draw_fps, draw_text
from src.color import Color
from src.transition import Transition
from mazegenerator.mazegenerator import MazeGenerator
from src.player import PacPlayer

class Game:
    def __init__(self, renderer, game_state: GameState, config: GameConfig,
                 transition: Transition):
        self.transition = transition
        self.width = config.screen_width
        self.height = config.screen_height
        self.renderer = renderer
        self.pixels = np.zeros((self.height, self.width), dtype=np.uint32)
        self.game_state = game_state
        self.config = config
        sttf.TTF_Init()
        self.font_size = 16
        self.font = sttf.TTF_OpenFont(
            b"assets/Press_Start_2P/PressStart2P-Regular.ttf", self.font_size)
        if not self.font:
            print_error(f"can't charge font {sttf.TTF_GetError()}")
        self.seed = 0
        self.current_level = 1
        self.maze_levels: list[list[list[int]]]
        self.background = sdl2.SDL_CreateTexture(
            renderer,
            sdl2.SDL_PIXELFORMAT_ARGB8888,
            sdl2.SDL_TEXTUREACCESS_STREAMING,
            self.width,
            self.height
        )
        self.pitch_background = self.width * 4
        self.create_maze_levels()
        self.create_items_levels()
        self.draw_button()
        self.player = PacPlayer()
        mid_y = len(self.maze_levels[0]) // 2
        mid_x = len(self.maze_levels[0][0]) // 2
        self.player.pos_x = mid_x
        self.player.pos_y = mid_y
        self.draw_button()

    def handle_event(self, event) -> None:
        """
        Gère les événements propres à la scène de jeu (clavier, etc.).
        """
        if event.type == sdl2.SDL_KEYDOWN:
            key = event.key.keysym.sym
            # print(f"DEBUG: Touche enfoncée = {key}")

            if key in (sdl2.SDLK_w, sdl2.SDLK_UP):
                self.player.key_w = True
                self.player.key_s = False
                self.player.key_a = False
                self.player.key_d = False

            elif key in (sdl2.SDLK_s, sdl2.SDLK_DOWN):
                self.player.key_w = False
                self.player.key_s = True
                self.player.key_a = False
                self.player.key_d = False

            elif key in (sdl2.SDLK_a, sdl2.SDLK_LEFT):
                self.player.key_w = False
                self.player.key_s = False
                self.player.key_a = True
                self.player.key_d = False

            elif key in (sdl2.SDLK_d, sdl2.SDLK_RIGHT):
                self.player.key_w = False
                self.player.key_s = False
                self.player.key_a = False
                self.player.key_d = True

            elif event.type == sdl2.SDL_KEYUP:
                key = event.key.keysym.sym
            elif key in (sdl2.SDLK_w, sdl2.SDLK_UP):
                self.player.key_w = False
            elif key in (sdl2.SDLK_s, sdl2.SDLK_DOWN):
                self.player.key_s = False
            elif key in (sdl2.SDLK_a, sdl2.SDLK_LEFT):
                self.player.key_a = False
            elif key in (sdl2.SDLK_d, sdl2.SDLK_RIGHT):
                self.player.key_d = False

    def clean_up(self) -> None:
        sttf.TTF_CloseFont(self.font)
        sttf.TTF_Quit()
        sdl2.SDL_DestroyTexture(self.background)

    def draw_button(self,) -> None:
        btn_w, btn_h = 90, 35
        padding = 10
        y_pos = 10
        self.btn_prev = Button(
            renderer=self.renderer,
            pixels=self.pixels,
            font=self.font,
            x=padding,
            y=y_pos,
            w=btn_w,
            h=btn_h,
            color_rect=Color.BLUE,
            color_hover=Color.RED,
            function=self.prev_level,
            text=b"PREV"
        )
        self.btn_next = Button(
            renderer=self.renderer,
            pixels=self.pixels,
            font=self.font,
            x=padding + btn_w + padding,
            y=y_pos,
            w=btn_w,
            h=btn_h,
            color_rect=Color.BLUE,
            color_hover=Color.RED,
            function=self.next_level,
            text=b"NEXT"
        )

    def create_maze_levels(self) -> None:
        self.maze_levels = []
        for level in self.config.level_array_multiple_levels:
            if level["name"] == "level1":
                try:
                    self.seed = int(self.config.seed)
                except ValueError:
                    self.seed = 0
            else:
                self.seed = 0
            maze = MazeGenerator((tuple([level["width"], level["height"]])),
                                 False, tuple([0, 0]),
                                 tuple([level["width"] - 1,
                                        level["height"] - 1]),
                                 self.seed)
            print(f"Level {level} generated with seed {maze._seed}")
            self.maze_levels.append(maze.maze)

    def draw_game(self) -> None:
        clear_background(self.pixels, Color.BLACK)

        side = int(min(self.config.screen_width,
                       self.config.screen_height) * 0.9)
        start_height = (self.config.screen_height - side) // 4
        start_width = (self.config.screen_width - side) // 2

        current_maze = self.maze_levels[self.current_level - 1]
        current_items = self.items_levels[self.current_level - 1]
        cellsize = side // self.config.level_array_multiple_levels[
            self.current_level - 1]["width"]

        self.player.update()
        self.player.handle_movement(current_maze, current_items)
        if self.check_level_complete(current_items):
            # Si c'est le tout dernier niveau, le joueur a gagné la partie !
            if self.current_level == len(
                    self.config.level_array_multiple_levels):
                pass
            else:
                self.next_level()
        self.draw_maze(current_maze, Color.RED, Color.BLACK, start_width,
                       start_height, cellsize)

        self.draw_items(current_items, Color.WHITE, Color.YELLOW, start_width,
                        start_height, cellsize)

        self.player.draw_player_pixels(self.pixels, start_width, start_height,
                                       cellsize, Color.CYAN)

        self.draw_cheat()
        self.btn_prev.draw_background()
        self.btn_next.draw_background()
        self.btn_prev.draw_text(Color.WHITE)
        self.btn_next.draw_text(Color.WHITE)

        pixel_ptr = get_ptr(self.pixels)
        sdl2.SDL_UpdateTexture(self.background, None, pixel_ptr,
        self.pitch_background)
        sdl2.SDL_RenderCopy(self.renderer, self.background, None, None)
        draw_text(self.renderer, self.font,
                  f"Level: {self.current_level}".encode('utf-8'), 10,
                  50, Color.WHITE, 1)

    def prev_level(self) -> None:
        if self.current_level > 1:
            self.current_level -= 1
        self.player.key_w = False
        self.player.key_s = False
        self.player.key_a = False
        self.player.key_d = False

    def next_level(self) -> None:
        max_levels = len(self.config.level_array_multiple_levels)
        if self.current_level < max_levels:
            self.current_level += 1
            self.player.pos_y = len(
                self.maze_levels[self.current_level - 1]) // 2
            self.player.pos_x = len(
                self.maze_levels[self.current_level - 1][0]) // 2
        self.player.key_w = False
        self.player.key_s = False
        self.player.key_a = False
        self.player.key_d = False

    def draw_cheat(self) -> None:
        pass

    def draw_maze(self, maze_matrix: list[list[int]], color_wall: int,
                  color_cel: int, start_x: int, start_y: int,
                  cellsize: int) -> None:
        """
        Draw the generated maze directly from a 2D array onto the rendering
        buffer.

        Args:
            maze_matrix (list[list[int]]): The 2D array containing bitwise
            walls.
            color_wall (int): Color value for the maze walls.
            color_cel (int): Color value for the cell background/paths.
            start_x (int): X offset to start drawing the maze.
            start_y (int): Y offset to start drawing the maze.
            cellsize (int): The size of each cell in pixels.

        Returns:
            None
        """
        NORTH, EAST, SOUTH, WEST = 1, 2, 4, 8
        thickness = max(1, cellsize // 8)
        pre_wall: list[np.ndarray] = []
        for i in range(16):
            arr = np.full((cellsize, cellsize), color_cel, dtype=np.uint32)

            if i & NORTH:
                arr[0:thickness, :] = color_wall
            if i & SOUTH:
                arr[cellsize - thickness:cellsize, :] = color_wall
            if i & EAST:
                arr[:, cellsize - thickness:cellsize] = color_wall
            if i & WEST:
                arr[:, 0:thickness] = color_wall

            pre_wall.append(arr)
        maze_height = len(maze_matrix)
        maze_width = len(maze_matrix[0]) if maze_height > 0 else 0

        for y in range(maze_height):
            for x in range(maze_width):
                cell_val = maze_matrix[y][x]
                draw_x = start_x + (x * cellsize)
                draw_y = start_y + (y * cellsize)
                v_start_x = max(0, draw_x)
                v_start_y = max(0, draw_y)
                v_end_x = min(self.width, draw_x + cellsize)
                v_end_y = min(self.height, draw_y + cellsize)

                visible_w = v_end_x - v_start_x
                visible_h = v_end_y - v_start_y

                if visible_w > 0 and visible_h > 0:
                    src_start_x = v_start_x - draw_x
                    src_start_y = v_start_y - draw_y
                    src_end_x = src_start_x + visible_w
                    src_end_y = src_start_y + visible_h
                    self.pixels[v_start_y:v_end_y, v_start_x:v_end_x] = \
                        pre_wall[cell_val][src_start_y:src_end_y,
                                           src_start_x:src_end_x]

    def create_items_levels(self) -> None:
        """
        Génère les emplacements des pacgums et super-pacgums pour chaque
        niveau.
        0 = Vide (centre ou case inaccessible)
        1 = Pacgum (couloirs)
        2 = Super-pacgum (4 coins)
        """
        self.items_levels = []
        for maze in self.maze_levels:
            maze_height = len(maze)
            maze_width = len(maze[0]) if maze_height > 0 else 0

            items_matrix = [[1 for _ in range(maze_width)] for _ in range(
                maze_height)]

            for y in range(maze_height):
                for x in range(maze_width):
                    if maze[y][x] == 15:
                        items_matrix[y][x] = 0

            mid_y = maze_height // 2
            mid_x = maze_width // 2
            items_matrix[mid_y][mid_x] = 0

            if maze_height > 1 and maze_width > 1:
                items_matrix[0][0] = 2
                items_matrix[0][maze_width - 1] = 2
                items_matrix[maze_height - 1][0] = 2
                items_matrix[maze_height - 1][maze_width - 1] = 2

            self.items_levels.append(items_matrix)

    def draw_items(self, items_matrix: list[list[int]], color_pacgum: int,
                   color_super: int,
                   start_x: int, start_y: int, cellsize: int) -> None:
        """
        Dessine les pacgums (1) et super-pacgums (2) au centre exact des
        couloirs.
        """
        maze_height = len(items_matrix)
        maze_width = len(items_matrix[0]) if maze_height > 0 else 0

        pg_size = max(3, cellsize // 5)
        spg_size = max(6, cellsize // 2)

        for y in range(maze_height):
            for x in range(maze_width):
                item = items_matrix[y][x]
                if item == 0:
                    continue
                cx = start_x + (x * cellsize) + (cellsize // 2)
                cy = start_y + (y * cellsize) + (cellsize // 2)

                radius = (pg_size // 2) if item == 1 else (spg_size // 2)
                color = color_pacgum if item == 1 else color_super

                y1, y2 = max(0, cy - radius), min(self.height, cy + radius)
                x1, x2 = max(0, cx - radius), min(self.width, cx + radius)

                if y2 > y1 and x2 > x1:
                    self.pixels[y1:y2, x1:x2] = color

    def check_level_complete(self, items_matrix: list[list[int]]) -> bool:
        """
        Vérifie si toutes les pac-gommes (1) et super pac-gommes (2)
        ont été mangées dans la matrice actuelle.
        """
        for row in items_matrix:
            if 1 in row or 2 in row:
                return False
        return True
