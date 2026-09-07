import math
import random
import json
import re
import sdl2
import sdl2.sdlimage as sdim
import time
import ctypes
from sdl2 import sdlttf as sttf
import numpy as np
from src.scene.helper import get_ptr
from src.game_state import GameConfig, GameState, ScenePossible
from src.drawing_methods import draw_text, draw_sprites
from src.color import Color
from src.transition import Transition
from mazegenerator.mazegenerator import MazeGenerator
from src.player import PacPlayer
from src.ghost import Ghost
from src.print_logs import print_error
from src.image import Image


class Game:
    MAX_SAVE_NAME_LENGTH = 23

    def __init__(self, renderer, game_state: GameState, config: GameConfig,
                 transition: Transition):
        self.transition = transition
        self.width = config.screen_width
        self.height = config.screen_height
        self.renderer = renderer
        self.pixels = np.zeros((self.height, self.width), dtype=np.uint32)
        self.game_state = game_state
        self.config = config
        sdim.IMG_Init(sdim.IMG_INIT_PNG)
        sttf.TTF_Init()
        self.font_size = 16
        self.font = sttf.TTF_OpenFont(
            b"assets/Press_Start_2P/PressStart2P-Regular.ttf", self.font_size)
        if not self.font:
            print_error(f"can't charge font {sttf.TTF_GetError()}")
        self.cheat_button_img = Image("assets/cheat_menu.png", renderer)
        self.cheat_menu_open = False
        self.paused = False
        self.save_name = ""
        self.save_error = ""
        self.score_recorded = False
        self.pause_start_time: float = 0.0
        self.cheat_button_margin = 12
        self.cheat_button_size = 44
        self.cheat_menu_w = min(480, max(300, int(self.width * 0.8)))
        self.cheat_menu_h = min(360, max(260, int(self.height * 0.8)))
        self.invincible = False
        self.ghosts_killed = False
        self.seed = 0
        self.current_level = 1
        self.remaining_life = (int(self.config.lives)
                               if self.config.lives is not None else 3)
        self.level_start_time = time.time()
        self.maze_levels: list[list[list[int]]]
        self.background = sdl2.SDL_CreateTexture(
            renderer,
            sdl2.SDL_PIXELFORMAT_ARGB8888,
            sdl2.SDL_TEXTUREACCESS_STREAMING,
            self.width,
            self.height
        )
        self.pitch_background = self.width * 4
        self.needs_reset: bool = False
        self.maze_buffer: np.ndarray | None = None
        self.cached_maze_level = -1
        self.cached_cellsize = -1
        self.create_maze_levels()
        self.create_items_levels()
        self.player = PacPlayer()
        mid_y = len(self.maze_levels[0]) // 2
        mid_x = len(self.maze_levels[0][0]) // 2
        self.player.pos_x = mid_x
        self.player.pos_y = mid_y

        self.ghosts = [
            Ghost("red", "assets/red_ghost.png"),
            Ghost("pink", "assets/pink_ghost.png"),
            Ghost("blue", "assets/blue_ghost.png"),
            Ghost("yellow", "assets/yellow_ghost.png")
        ]
        self.spawn_ghosts()

    def reset(self) -> None:
        """Réinitialise complètement une nouvelle partie."""
        sdl2.SDL_StopTextInput()
        self.current_level = 1
        self.remaining_life = (int(self.config.lives)
                               if self.config.lives is not None else 3)
        self.level_start_time = time.time()
        self.pause_start_time = 0.0
        self.cheat_menu_open = False
        self.paused = False
        self.save_name = ""
        self.save_error = ""
        self.score_recorded = False
        self.invincible = False
        self.ghosts_killed = False
        self.game_state.point = 0
        self.maze_buffer = None
        self.cached_maze_level = -1
        self.cached_cellsize = -1
        self.create_maze_levels()
        self.create_items_levels()
        self.player = PacPlayer()
        if self.maze_levels and len(self.maze_levels) > 0:
            mid_y = len(self.maze_levels[0]) // 2
            mid_x = len(self.maze_levels[0][0]) // 2
            self.player.pos_x = mid_x
            self.player.pos_y = mid_y
        self.ghosts = [
            Ghost("red", "assets/red_ghost.png"),
            Ghost("pink", "assets/pink_ghost.png"),
            Ghost("blue", "assets/blue_ghost.png"),
            Ghost("yellow", "assets/yellow_ghost.png")
        ]
        self.spawn_ghosts()

    @staticmethod
    def _safe_int(value, default: int) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def toggle_cheat_menu(self) -> None:
        """Ouvre ou ferme le menu de cheat et gère la pause du jeu."""
        if not self.cheat_menu_open:
            self.cheat_menu_open = True
            self.pause_start_time = time.time()
            self.player.key_w = False
            self.player.key_s = False
            self.player.key_a = False
            self.player.key_d = False
            self.player.next_direction = None
        else:
            self.cheat_menu_open = False
            if self.pause_start_time > 0.0:
                self.level_start_time += (time.time() - self.pause_start_time)
                self.pause_start_time = 0.0

    def toggle_pause(self) -> None:
        """Pauses or resumes the game without changing the scene."""
        if self.paused:
            sdl2.SDL_StopTextInput()
            if self.pause_start_time > 0.0:
                self.level_start_time += (time.time() - self.pause_start_time)
                self.pause_start_time = 0.0
            self.paused = False
        else:
            self.paused = True
            self.save_name = ""
            self.save_error = ""
            self.pause_start_time = time.time()
            sdl2.SDL_StartTextInput()
            self.transition.transition_on = False
            self.transition.sens_transition = False
            self.transition.img = False
            self.transition.rect = False
            self.player.key_w = False
            self.player.key_s = False
            self.player.key_a = False
            self.player.key_d = False
            self.player.next_direction = None

    def handle_escape(self) -> bool:
        """Closes the cheat menu or toggles the pause menu."""
        if self.cheat_menu_open:
            self.toggle_cheat_menu()
            return True
        self.toggle_pause()
        return True

    def _quit_to_menu(self) -> None:
        sdl2.SDL_StopTextInput()
        self.paused = False
        self.transition.start_image_transition(ScenePossible.MAIN)
        self.needs_reset = True

    def _save_and_quit(self) -> None:
        if not re.fullmatch(r"[A-Za-z0-9_-]+", self.save_name):
            self.save_error = "INVALID NAME"
            return

        if not self._record_score():
            return
        self._quit_to_menu()

    def end_screen_save_and_quit(self, save_name: str) -> bool:
        self.save_name = save_name
        if not re.fullmatch(r"[A-Za-z0-9_-]+", self.save_name):
            return False
        if not self._record_score():
            return False
        self.reset()
        self.game_state.scene = ScenePossible.MAIN
        return True

    def end_screen_quit(self) -> None:
        self.reset()
        self.game_state.scene = ScenePossible.MAIN

    def _record_score(self) -> bool:
        if self.score_recorded:
            return True

        score_path = self.config.highscore_filename or "scores.json"
        score_name = self.save_name
        try:
            with open(score_path, "r") as score_file:
                score_data = json.load(score_file)
            scores = score_data.get("scores", [])
            scores.append({
                "name": score_name,
                "point": self.game_state.get_points(),
            })
            with open(score_path, "w") as score_file:
                json.dump({"scores": scores}, score_file, indent=4)
            self.score_recorded = True
            return True
        except (OSError, TypeError, ValueError):
            self.save_error = "SCORE NOT SAVED"
            return False

    def handle_event(self, event) -> None:
        """
        Gère les événements propres à la scène de jeu (clavier, etc.).
        """
        if event.type == sdl2.SDL_MOUSEBUTTONDOWN:
            button = getattr(event.button, "button", 0)
            if button == sdl2.SDL_BUTTON_LEFT:
                mouse_x = getattr(event.button, "x", -1)
                mouse_y = getattr(event.button, "y", -1)
                if self.paused:
                    for pause_button in self._get_pause_buttons():
                        bx, by = pause_button["x"], pause_button["y"]
                        bw, bh = pause_button["w"], pause_button["h"]
                        if (bx <= mouse_x <= bx + bw
                                and by <= mouse_y <= by + bh):
                            if pause_button["id"] == "save":
                                self._save_and_quit()
                            else:
                                self._quit_to_menu()
                            return
                    return
                if self._is_cheat_button_hovered(mouse_x, mouse_y):
                    self.toggle_cheat_menu()
                    return

                if self.cheat_menu_open:
                    cx, cy, cw, ch = self._get_cheat_close_rect()
                    if cx <= mouse_x <= cx + cw and cy <= mouse_y <= cy + ch:
                        self.toggle_cheat_menu()
                        return
                    for btn in self._get_cheat_buttons():
                        bx, by = btn["x"], btn["y"]
                        bw, bh = btn["w"], btn["h"]
                        if (bx <= mouse_x <= bx + bw
                                and by <= mouse_y <= by + bh):
                            self._apply_cheat(btn["id"])
                            return
                    return
            return

        if event.type == sdl2.SDL_TEXTINPUT and self.paused:
            text_bytes = bytes(event.text.text).split(b"\0", 1)[0]
            text = text_bytes.decode("utf-8", errors="ignore")
            if re.fullmatch(r"[A-Za-z0-9_-]+", text):
                available = self.MAX_SAVE_NAME_LENGTH - len(self.save_name)
                if available > 0:
                    self.save_name += text[:available]
                    self.save_error = ""
                if len(text) > available:
                    self.save_error = "NAME TOO LONG (23 MAX)"
            else:
                self.save_error = "INVALID CHARACTERS"
            return

        if event.type == sdl2.SDL_KEYDOWN:
            key = event.key.keysym.sym

            if self.paused:
                if key == sdl2.SDLK_BACKSPACE:
                    self.save_name = self.save_name[:-1]
                    self.save_error = ""
                elif key in (sdl2.SDLK_RETURN, sdl2.SDLK_KP_ENTER):
                    self._save_and_quit()
                return

            if key == sdl2.SDLK_c and not self.paused:
                self.toggle_cheat_menu()
                return

            if self.cheat_menu_open:
                if key in (sdl2.SDLK_RETURN, sdl2.SDLK_SPACE):
                    self.toggle_cheat_menu()
                elif key in (sdl2.SDLK_1, sdl2.SDLK_KP_1):
                    self._apply_cheat("life")
                elif key in (sdl2.SDLK_2, sdl2.SDLK_KP_2):
                    self._apply_cheat("score")
                elif key in (sdl2.SDLK_3, sdl2.SDLK_KP_3):
                    self._apply_cheat("prev")
                elif key in (sdl2.SDLK_4, sdl2.SDLK_KP_4):
                    self._apply_cheat("next")
                elif key in (sdl2.SDLK_5, sdl2.SDLK_KP_5):
                    self._apply_cheat("power")
                elif key in (sdl2.SDLK_6, sdl2.SDLK_KP_6):
                    self._apply_cheat("kill")
                elif key in (sdl2.SDLK_7, sdl2.SDLK_KP_7):
                    self._apply_cheat("invincible")
                elif key in (sdl2.SDLK_8, sdl2.SDLK_KP_8):
                    self._apply_cheat("noclip")
                return

            if key in (sdl2.SDLK_w, sdl2.SDLK_UP):
                self.player.key_w = True
                self.player.key_s = False
                self.player.key_a = False
                self.player.key_d = False
                self.player.next_direction = 2

            elif key in (sdl2.SDLK_s, sdl2.SDLK_DOWN):
                self.player.key_w = False
                self.player.key_s = True
                self.player.key_a = False
                self.player.key_d = False
                self.player.next_direction = 3

            elif key in (sdl2.SDLK_a, sdl2.SDLK_LEFT):
                self.player.key_w = False
                self.player.key_s = False
                self.player.key_a = True
                self.player.key_d = False
                self.player.next_direction = 1

            elif key in (sdl2.SDLK_d, sdl2.SDLK_RIGHT):
                self.player.key_w = False
                self.player.key_s = False
                self.player.key_a = False
                self.player.key_d = True
                self.player.next_direction = 0

        elif event.type == sdl2.SDL_KEYUP:
            if self.cheat_menu_open:
                return
            key = event.key.keysym.sym
            if key in (sdl2.SDLK_w, sdl2.SDLK_UP):
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
        sdim.IMG_Quit()
        sdl2.SDL_DestroyTexture(self.background)
        sdl2.SDL_DestroyTexture(self.cheat_button_img.texture)

    def _is_cheat_button_hovered(self, mouse_x: int, mouse_y: int) -> bool:
        button_x = (
            self.width - self.cheat_button_margin - self.cheat_button_size
        )
        button_y = self.cheat_button_margin
        return (
            button_x <= mouse_x <= button_x + self.cheat_button_size
            and button_y <= mouse_y <= button_y + self.cheat_button_size
        )

    def create_maze_levels(self) -> None:
        self.maze_levels = []
        levels = self.config.level_array_multiple_levels or []
        for level in levels:
            if level["name"] == "level1":
                self.seed = self._safe_int(self.config.seed, 0)
            else:
                self.seed = 0
            maze = MazeGenerator((tuple([level["width"], level["height"]])),
                                 False, tuple([0, 0]),
                                 tuple([level["width"] - 1,
                                        level["height"] - 1]),
                                 self.seed)
            # print(f"Level {level} generated with seed {maze._seed}")
            self.maze_levels.append(maze.maze)

    def draw_game(self) -> None:
        if self.needs_reset:
            self.reset()
            self.needs_reset = False

        side = int(min(self.config.screen_width,
                       self.config.screen_height) * 0.9)
        start_height = (self.config.screen_height - side) // 4
        start_width = (self.config.screen_width - side) // 2

        current_maze = self.maze_levels[self.current_level - 1]
        current_items = self.items_levels[self.current_level - 1]
        levels = self.config.level_array_multiple_levels or []
        current_level_config = levels[self.current_level - 1]
        cellsize = side // current_level_config["width"]

        self.draw_maze(current_maze, Color.RED, Color.BLACK, start_width,
                       start_height, cellsize)

        if (not self.transition.transition_on and not self.cheat_menu_open
            and not self.paused):
            max_time = self._safe_int(self.config.level_max_time, 90)
            elapsed = time.time() - self.level_start_time
            time_left = max(0, int(max_time - elapsed))
            if time_left <= 0:
                self.on_player_death()
                return

            dt = (self.game_state.dt
                  if self.game_state.dt > 0 else (1.0 / 60.0))
            dt = min(dt, 0.05)

            self.player.update(dt)
            self.player.handle_movement(current_maze, current_items,
                                        self.game_state, self.config,
                                        self.ghosts, dt)

            player_pos = (self.player.pos_x, self.player.pos_y)
            for ghost in self.ghosts:
                ghost.update(dt, player_pos)
                if ghost.is_dead:
                    continue
                if ghost.is_vulnerable:
                    ghost.move_vulnerable(current_maze, dt)
                else:
                    ghost.move_normal(current_maze, dt)

            self.handle_ghost_collisions(current_maze)

            if self.check_level_complete(current_items):
                if self.current_level == len(levels):
                    self.transition.transition_on = False
                    self.game_state.scene = ScenePossible.WIN
                else:
                    self.next_level()

        self.draw_items(current_items, Color.WHITE, Color.YELLOW, start_width,
                        start_height, cellsize)

        self.player.draw_player_pixels(self.pixels, start_width, start_height,
                                       cellsize, Color.CYAN)

        for ghost in self.ghosts:
            ghost.draw_ghost_pixels(self.pixels, start_width, start_height,
                                    cellsize)

        pixel_ptr = get_ptr(self.pixels)
        sdl2.SDL_UpdateTexture(self.background, None, pixel_ptr,
                               self.pitch_background)
        sdl2.SDL_RenderCopy(self.renderer, self.background, None, None)
        self.draw_info()
        self.draw_cheat()
        self.draw_pause()

    def handle_ghost_collisions(self, maze_matrix: list[list[int]]) -> None:
        """Gère les collisions entre Pac-Man et les fantômes."""
        px = getattr(self.player, 'render_x', float(self.player.pos_x))
        py = getattr(self.player, 'render_y', float(self.player.pos_y))
        player_pos = (self.player.pos_x, self.player.pos_y)

        maze_height = len(maze_matrix)
        maze_width = len(maze_matrix[0]) if maze_height > 0 else 0
        corners = [
            (0, 0),
            (maze_width - 1, 0) if maze_width > 0 else (0, 0),
            (0, maze_height - 1) if maze_height > 0 else (0, 0),
            (maze_width - 1, maze_height - 1)
            if maze_width > 0 and maze_height > 0 else (0, 0),
        ]

        collision_dist = 0.65

        for ghost in self.ghosts:
            if ghost.is_dead:
                continue
            gx = getattr(ghost, 'render_x', float(ghost.pos_x))
            gy = getattr(ghost, 'render_y', float(ghost.pos_y))

            dist = math.hypot(px - gx, py - gy)
            grid_match = ((ghost.pos_x, ghost.pos_y) == player_pos)

            if dist > collision_dist and not grid_match:
                continue

            if ghost.is_vulnerable:
                ghost.kill(corners)
                points = self._safe_int(self.config.points_per_ghost, 200)
                self.game_state.point += points
                continue

            if self.invincible:
                continue

            self.on_player_death()
            break

    def on_player_death(self) -> None:
        """Removes one life and respawns, or shows the loose screen."""
        if self.transition.transition_on:
            return

        self.remaining_life -= 1
        self.player.is_powered_up = False
        self.player.power_timer = 0
        self.player.key_w = False
        self.player.key_s = False
        self.player.key_a = False
        self.player.key_d = False

        if self.remaining_life <= 0:
            self.remaining_life = 0
            self.transition.transition_on = False
            self.game_state.scene = ScenePossible.LOOSE
            return

        self.level_start_time = time.time()
        self.pause_start_time = 0.0
        self.paused = False
        self.maze_buffer = None
        self.cached_maze_level = -1
        self.cached_cellsize = -1
        self.player.pos_y = len(
            self.maze_levels[self.current_level - 1]) // 2
        self.player.pos_x = len(
            self.maze_levels[self.current_level - 1][0]) // 2
        self.player.render_x = float(self.player.pos_x)
        self.player.render_y = float(self.player.pos_y)
        self.spawn_ghosts()

    def spawn_ghosts(self) -> None:
        """Positionne les 4 fantômes sur les emplacements des super-pacgums."""
        current_items = self.items_levels[self.current_level - 1]
        super_pacgum_positions = []
        maze_height = len(current_items)
        maze_width = len(current_items[0]) if maze_height > 0 else 0

        for y in range(maze_height):
            for x in range(maze_width):
                if current_items[y][x] == 2:
                    super_pacgum_positions.append((x, y))

        fallback_corners = [
            (0, 0),
            (maze_width - 1, 0),
            (0, maze_height - 1),
            (maze_width - 1, maze_height - 1)
        ]
        for pos in fallback_corners:
            if len(super_pacgum_positions) >= len(self.ghosts):
                break
            if pos not in super_pacgum_positions:
                super_pacgum_positions.append(pos)

        for i, ghost in enumerate(self.ghosts):
            pos = super_pacgum_positions[i % len(super_pacgum_positions)]
            ghost.pos_x, ghost.pos_y = pos
            ghost.is_dead = False
            ghost.is_permanently_dead = False
            ghost.is_vulnerable = False
            ghost.respawn_timer = 0.0
            ghost.vulnerable_timer = 0.0
            ghost.direction = random.randint(0, 3)
            if self.ghosts_killed:
                ghost.kill_permanently()

    def prev_level(self) -> None:
        if self.current_level > 1:
            self.current_level -= 1
            self.level_start_time = time.time()
            if self.cheat_menu_open:
                self.pause_start_time = self.level_start_time
            self.maze_buffer = None
            self.cached_maze_level = -1
            self.cached_cellsize = -1
            self.player.pos_y = len(
                self.maze_levels[self.current_level - 1]) // 2
            self.player.pos_x = len(
                self.maze_levels[self.current_level - 1][0]) // 2
            self.spawn_ghosts()
        self.player.key_w = False
        self.player.key_s = False
        self.player.key_a = False
        self.player.key_d = False
        self.player.next_direction = None

    def next_level(self) -> None:
        max_levels = len(self.config.level_array_multiple_levels or [])
        if self.current_level < max_levels:
            self.current_level += 1
            self.level_start_time = time.time()
            if self.cheat_menu_open:
                self.pause_start_time = self.level_start_time
            self.maze_buffer = None
            self.cached_maze_level = -1
            self.cached_cellsize = -1
            self.player.pos_y = len(
                self.maze_levels[self.current_level - 1]) // 2
            self.player.pos_x = len(
                self.maze_levels[self.current_level - 1][0]) // 2
            self.spawn_ghosts()
        self.player.key_w = False
        self.player.key_s = False
        self.player.key_a = False
        self.player.key_d = False
        self.player.next_direction = None
        self.player.is_powered_up = False
        self.player.power_timer = 0.0

    def _get_cheat_menu_rect(self) -> tuple[int, int, int, int]:
        menu_w = min(480, max(300, int(self.width * 0.8)))
        menu_h = min(360, max(260, int(self.height * 0.8)))
        menu_x = (self.width - menu_w) // 2
        menu_y = (self.height - menu_h) // 2
        return (menu_x, menu_y, menu_w, menu_h)

    def _get_cheat_close_rect(self) -> tuple[int, int, int, int]:
        menu_x, menu_y, menu_w, _ = self._get_cheat_menu_rect()
        return (menu_x + menu_w - 30, menu_y + 10, 20, 20)

    def _get_cheat_buttons(self) -> list[dict]:
        menu_x, menu_y, menu_w, _ = self._get_cheat_menu_rect()

        btn_w = min(210, (menu_w - 60) // 2)
        btn_h = 34
        gap_x = menu_w - 40 - (btn_w * 2)
        col1_x = menu_x + 20
        col2_x = col1_x + btn_w + gap_x

        row1_y = menu_y + 80
        row2_y = menu_y + 122
        row3_y = menu_y + 164
        row4_y = menu_y + 206
        row5_y = menu_y + 248

        resume_w = menu_w - 40
        resume_x = menu_x + 20

        return [
            {"id": "life", "label": "+1 LIFE",
             "x": col1_x, "y": row1_y, "w": btn_w, "h": btn_h},
            {"id": "score", "label": "+500 PTS",
             "x": col2_x, "y": row1_y, "w": btn_w, "h": btn_h},
            {"id": "prev", "label": "PREV LEVEL",
             "x": col1_x, "y": row2_y, "w": btn_w, "h": btn_h},
            {"id": "next", "label": "NEXT LEVEL",
             "x": col2_x, "y": row2_y, "w": btn_w, "h": btn_h},
            {"id": "power", "label": "POWER UP",
             "x": col1_x, "y": row3_y, "w": btn_w, "h": btn_h},
            {"id": "kill", "label": "KILL GHOSTS",
             "x": col2_x, "y": row3_y, "w": btn_w, "h": btn_h},
            {"id": "invincible", "label": "INVINCIBLE",
             "x": col1_x, "y": row4_y, "w": btn_w, "h": btn_h},
            {"id": "noclip", "label": "NO CLIP",
             "x": col2_x, "y": row4_y, "w": btn_w, "h": btn_h},
            {"id": "resume", "label": "RESUME",
             "x": resume_x, "y": row5_y, "w": resume_w, "h": btn_h},
        ]

    def _apply_cheat(self, cheat_id: str) -> None:
        if cheat_id == "life":
            self.remaining_life += 1
        elif cheat_id == "score":
            if self.game_state.get_points() >= 2147483647:
                pass
            else:
                self.game_state.point += 500
        elif cheat_id == "prev":
            self.prev_level()
        elif cheat_id == "next":
            self.next_level()
        elif cheat_id == "power":
            self.player.is_powered_up = True
            self.player.power_timer = 10.0
            for ghost in self.ghosts:
                ghost.make_vulnerable()
        elif cheat_id == "kill":
            if self.ghosts_killed:
                self.ghosts_killed = False
                self.spawn_ghosts()
            else:
                for ghost in self.ghosts:
                    ghost.kill_permanently()
                self.ghosts_killed = True
        elif cheat_id == "invincible":
            self.invincible = not self.invincible
        elif cheat_id == "noclip":
            self.player.noclip = not self.player.noclip
        elif cheat_id == "resume":
            self.toggle_cheat_menu()

    def draw_cheat(self) -> None:
        button_x = (
            self.width - self.cheat_button_margin - self.cheat_button_size
        )
        button_y = self.cheat_button_margin

        button_w = self.cheat_button_img.width or self.cheat_button_size
        button_h = self.cheat_button_img.height or self.cheat_button_size
        if button_w > 0 and button_h > 0:
            button_scale = min(
                self.cheat_button_size / button_w,
                self.cheat_button_size / button_h,
            )
            draw_sprites(
                self.renderer,
                self.cheat_button_img,
                button_x,
                button_y,
                button_scale,
            )

        if not self.cheat_menu_open:
            return

        menu_x, menu_y, menu_w, menu_h = self._get_cheat_menu_rect()

        # 1. Fond sombre semi-transparent
        overlay = sdl2.SDL_Rect(menu_x, menu_y, menu_w, menu_h)
        sdl2.SDL_SetRenderDrawBlendMode(
            self.renderer, sdl2.SDL_BLENDMODE_BLEND
        )
        sdl2.SDL_SetRenderDrawColor(self.renderer, 10, 10, 20, 235)
        sdl2.SDL_RenderFillRect(self.renderer, ctypes.byref(overlay))

        # 2. Contours rouges (et pas bleu !)
        sdl2.SDL_SetRenderDrawColor(self.renderer, 255, 0, 0, 255)
        sdl2.SDL_RenderDrawRect(self.renderer, ctypes.byref(overlay))
        overlay_inner = sdl2.SDL_Rect(
            menu_x + 2, menu_y + 2, menu_w - 4, menu_h - 4
        )
        sdl2.SDL_RenderDrawRect(self.renderer, ctypes.byref(overlay_inner))

        # 3. Titre CHEAT MENU
        title_text = b"CHEAT MENU"
        w_val, h_val = ctypes.c_int(0), ctypes.c_int(0)
        sttf.TTF_SizeUTF8(
            self.font, title_text,
            ctypes.byref(w_val), ctypes.byref(h_val)
        )
        title_x = menu_x + (menu_w - w_val.value) // 2
        title_y = menu_y + 16
        draw_text(
            self.renderer, self.font, title_text,
            title_x, title_y, Color.RED, 1
        )

        # 4. Statut GAME PAUSED
        sub_text = b"* GAME PAUSED *"
        sttf.TTF_SizeUTF8(
            self.font, sub_text,
            ctypes.byref(w_val), ctypes.byref(h_val)
        )
        sub_x = menu_x + (menu_w - w_val.value) // 2
        sub_y = menu_y + 40
        draw_text(
            self.renderer, self.font, sub_text,
            sub_x, sub_y, Color.YELLOW, 1
        )

        # 5. Séparateur rouge
        sdl2.SDL_SetRenderDrawColor(self.renderer, 255, 0, 0, 200)
        sdl2.SDL_RenderDrawLine(
            self.renderer,
            menu_x + 16, menu_y + 66,
            menu_x + menu_w - 16, menu_y + 66
        )

        # 6. Bouton [X] en haut a droite
        cx, cy, cw, ch = self._get_cheat_close_rect()
        mx, my = ctypes.c_int(0), ctypes.c_int(0)
        sdl2.SDL_GetMouseState(ctypes.byref(mx), ctypes.byref(my))
        x_hovered = (
            cx <= mx.value <= cx + cw and cy <= my.value <= cy + ch
        )

        x_col = (255, 60, 60, 255) if x_hovered else (180, 180, 180, 255)
        sdl2.SDL_SetRenderDrawColor(self.renderer, *x_col)
        sdl2.SDL_RenderDrawLine(
            self.renderer, cx + 3, cy + 3, cx + cw - 3, cy + ch - 3
        )
        sdl2.SDL_RenderDrawLine(
            self.renderer, cx + cw - 3, cy + 3, cx + 3, cy + ch - 3
        )

        # 7. Boutons de cheat
        buttons = self._get_cheat_buttons()
        for btn in buttons:
            bx, by, bw, bh = btn["x"], btn["y"], btn["w"], btn["h"]
            btn_rect = sdl2.SDL_Rect(bx, by, bw, bh)
            is_hovered = (
                bx <= mx.value <= bx + bw and by <= my.value <= by + bh
            )
            is_active = (
                (btn["id"] == "kill" and self.ghosts_killed)
                or (btn["id"] == "invincible" and self.invincible)
                or (btn["id"] == "noclip" and self.player.noclip)
            )

            if is_active:
                sdl2.SDL_SetRenderDrawColor(self.renderer, 100, 80, 0, 230)
                sdl2.SDL_RenderFillRect(self.renderer, ctypes.byref(btn_rect))
                sdl2.SDL_SetRenderDrawColor(self.renderer, 255, 220, 0, 255)
                sdl2.SDL_RenderDrawRect(self.renderer, ctypes.byref(btn_rect))
                text_col = Color.YELLOW
            elif is_hovered:
                sdl2.SDL_SetRenderDrawColor(self.renderer, 60, 15, 15, 230)
                sdl2.SDL_RenderFillRect(self.renderer, ctypes.byref(btn_rect))
                sdl2.SDL_SetRenderDrawColor(self.renderer, 255, 50, 50, 255)
                sdl2.SDL_RenderDrawRect(self.renderer, ctypes.byref(btn_rect))
                text_col = Color.YELLOW
            else:
                sdl2.SDL_SetRenderDrawColor(self.renderer, 25, 10, 10, 220)
                sdl2.SDL_RenderFillRect(self.renderer, ctypes.byref(btn_rect))
                sdl2.SDL_SetRenderDrawColor(self.renderer, 200, 30, 30, 255)
                sdl2.SDL_RenderDrawRect(self.renderer, ctypes.byref(btn_rect))
                text_col = Color.WHITE

            label_bytes = btn["label"].encode("utf-8")
            sttf.TTF_SizeUTF8(
                self.font, label_bytes,
                ctypes.byref(w_val), ctypes.byref(h_val)
            )
            lbl_x = bx + (bw - w_val.value) // 2
            lbl_y = by + (bh - h_val.value) // 2
            draw_text(
                self.renderer, self.font, label_bytes,
                lbl_x, lbl_y, text_col, 1
            )

        # 8. Indication raccourci
        hint_text = b"[ESC] or [C] to resume"
        sttf.TTF_SizeUTF8(
            self.font, hint_text,
            ctypes.byref(w_val), ctypes.byref(h_val)
        )
        hint_x = menu_x + (menu_w - w_val.value) // 2
        hint_y = menu_y + menu_h - 26
        draw_text(
            self.renderer, self.font, hint_text,
            hint_x, hint_y, Color.GRAY, 1
        )

    def draw_pause(self) -> None:
        if not self.paused:
            return

        menu_w = min(460, max(300, int(self.width * 0.72)))
        menu_h = 260
        menu_x = (self.width - menu_w) // 2
        menu_y = (self.height - menu_h) // 2
        menu_rect = sdl2.SDL_Rect(menu_x, menu_y, menu_w, menu_h)

        sdl2.SDL_SetRenderDrawBlendMode(
            self.renderer, sdl2.SDL_BLENDMODE_BLEND
        )
        sdl2.SDL_SetRenderDrawColor(self.renderer, 10, 10, 20, 235)
        sdl2.SDL_RenderFillRect(self.renderer, ctypes.byref(menu_rect))
        sdl2.SDL_SetRenderDrawColor(self.renderer, 255, 0, 0, 255)
        sdl2.SDL_RenderDrawRect(self.renderer, ctypes.byref(menu_rect))

        inner_rect = sdl2.SDL_Rect(menu_x + 2, menu_y + 2,
                                   menu_w - 4, menu_h - 4)
        sdl2.SDL_RenderDrawRect(self.renderer, ctypes.byref(inner_rect))

        texts = [(b"GAME PAUSED", menu_y + 12, Color.RED),
             (b"SAVE NAME", menu_y + 40, Color.WHITE)]
        for text, text_y, color in texts:
            w_val, h_val = ctypes.c_int(0), ctypes.c_int(0)
            sttf.TTF_SizeUTF8(self.font, text,
                              ctypes.byref(w_val), ctypes.byref(h_val))
            text_x = menu_x + (menu_w - w_val.value) // 2
            draw_text(self.renderer, self.font, text, text_x, text_y,
                      color, 1)

        input_rect = sdl2.SDL_Rect(menu_x + 24, menu_y + 62,
                       menu_w - 48, 30)
        sdl2.SDL_SetRenderDrawColor(self.renderer, 30, 30, 45, 255)
        sdl2.SDL_RenderFillRect(self.renderer, ctypes.byref(input_rect))
        sdl2.SDL_SetRenderDrawColor(self.renderer, 255, 255, 0, 255)
        sdl2.SDL_RenderDrawRect(self.renderer, ctypes.byref(input_rect))
        name_text = self.save_name.encode("ascii") or b"_"
        draw_text(self.renderer, self.font, name_text,
                  menu_x + 34, menu_y + 68,
                  Color.WHITE if self.save_name else Color.GRAY, 1)

        if self.save_error:
            draw_text(self.renderer, self.font, self.save_error,
                      menu_x + 24, menu_y + 98, Color.RED, 1)

        for button in self._get_pause_buttons():
            button_rect = sdl2.SDL_Rect(button["x"], button["y"],
                                       button["w"], button["h"])
            mouse_x, mouse_y = ctypes.c_int(0), ctypes.c_int(0)
            sdl2.SDL_GetMouseState(ctypes.byref(mouse_x),
                                   ctypes.byref(mouse_y))
            hovered = (button["x"] <= mouse_x.value <= button["x"]
                       + button["w"] and button["y"] <= mouse_y.value
                       <= button["y"] + button["h"])
            fill_color = (60, 15, 15, 255) if hovered else (25, 10, 10, 255)
            border_color = (255, 220, 0, 255) if hovered else (200, 30, 30, 255)
            sdl2.SDL_SetRenderDrawColor(self.renderer, *fill_color)
            sdl2.SDL_RenderFillRect(self.renderer, ctypes.byref(button_rect))
            sdl2.SDL_SetRenderDrawColor(self.renderer, *border_color)
            sdl2.SDL_RenderDrawRect(self.renderer, ctypes.byref(button_rect))
            label = button["label"].encode("ascii")
            w_val, h_val = ctypes.c_int(0), ctypes.c_int(0)
            sttf.TTF_SizeUTF8(self.font, label,
                              ctypes.byref(w_val), ctypes.byref(h_val))
            draw_text(self.renderer, self.font, label,
                      button["x"] + (button["w"] - w_val.value) // 2,
                      button["y"] + (button["h"] - h_val.value) // 2,
                      Color.YELLOW if hovered else Color.WHITE, 1)

        draw_text(self.renderer, self.font, b"ESC TO RESUME",
              menu_x + 24, menu_y + 238, Color.GRAY, 1)

    def _get_pause_buttons(self) -> list[dict]:
        menu_w = min(460, max(300, int(self.width * 0.72)))
        menu_h = 260
        menu_x = (self.width - menu_w) // 2
        menu_y = (self.height - menu_h) // 2
        button_w = menu_w - 48
        return [
            {"id": "save", "label": "SAVE AND QUIT",
             "x": menu_x + 24, "y": menu_y + 135,
             "w": button_w, "h": 34},
            {"id": "quit", "label": "QUIT TO MENU",
             "x": menu_x + 24, "y": menu_y + 177,
             "w": button_w, "h": 34},
        ]

    def draw_maze(self, maze_matrix: list[list[int]], color_wall: int,
                  color_cel: int, start_x: int, start_y: int,
                  cellsize: int) -> None:
        """
        Dessine le labyrinthe directement depuis la matrice 2D sur le buffer.
        Mis en cache par niveau pour des performances maximales à 60 FPS.
        """
        if (self.maze_buffer is None or
                self.cached_maze_level != self.current_level or
                self.cached_cellsize != cellsize):
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

            maze_buffer = np.full((self.height, self.width), color_cel,
                                  dtype=np.uint32)

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
                        maze_buffer[v_start_y:v_end_y,
                                    v_start_x:v_end_x] = \
                            pre_wall[cell_val][src_start_y:src_end_y,
                                               src_start_x:src_end_x]

            self.maze_buffer = maze_buffer
            self.cached_maze_level = self.current_level
            self.cached_cellsize = cellsize

        if self.maze_buffer is not None:
            np.copyto(self.pixels, self.maze_buffer)

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

    def draw_pacman_icon(self, cx: int, cy: int, radius: int = 7) -> None:
        """
        Dessine une icône Pac-Man jaune avec la bouche ouverte.
        """
        sdl2.SDL_SetRenderDrawColor(self.renderer, 255, 255, 0, 255)
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if dx * dx + dy * dy <= radius * radius:
                    if dx > 0 and abs(dy) <= dx * 0.65:
                        continue
                    sdl2.SDL_RenderDrawPoint(self.renderer, cx + dx, cy + dy)
        sdl2.SDL_SetRenderDrawColor(self.renderer, 0, 0, 0, 255)
        sdl2.SDL_RenderDrawPoint(self.renderer, cx + 1, cy - radius // 2)

    def draw_info(self) -> None:
        """
        Dessine un petit rectangle avec les infos suivantes :
        - current_level
        - current_score
        - time_left
        - remaining_life (affiché via des icônes de pacman)
        """
        rect_x, rect_y = 20, 20
        rect_w, rect_h = 300, ((130 + (self.remaining_life // 7) * 20))

        sdl2.SDL_SetRenderDrawBlendMode(self.renderer,
                                        sdl2.SDL_BLENDMODE_BLEND)

        rect = sdl2.SDL_Rect(rect_x, rect_y, rect_w, rect_h)
        sdl2.SDL_SetRenderDrawColor(self.renderer, 10, 10, 25, 210)
        sdl2.SDL_RenderFillRect(self.renderer, ctypes.byref(rect))

        sdl2.SDL_SetRenderDrawColor(self.renderer, 255, 0, 0, 200)
        sdl2.SDL_RenderDrawRect(self.renderer, ctypes.byref(rect))
        rect_inner = sdl2.SDL_Rect(rect_x + 2, rect_y + 2, rect_w - 4,
                                   rect_h - 4)
        sdl2.SDL_RenderDrawRect(self.renderer, ctypes.byref(rect_inner))

        max_time = self._safe_int(self.config.level_max_time, 90)

        if ((self.cheat_menu_open or self.paused)
            and self.pause_start_time > 0.0):
            elapsed = self.pause_start_time - self.level_start_time
        else:
            elapsed = time.time() - self.level_start_time
        time_left = max(0, int(max_time - elapsed))

        text_x = rect_x + 15
        start_y = rect_y + 12
        line_step = 28

        draw_text(self.renderer, self.font,
                  f"LEVEL: {self.current_level}",
                  text_x, start_y, Color.WHITE, 1)

        draw_text(self.renderer, self.font,
                  f"SCORE: {self.game_state.get_points()}",
                  text_x, start_y + line_step, Color.WHITE, 1)

        draw_text(self.renderer, self.font,
                  f"TIME:  {time_left}",
                  text_x, start_y + line_step * 2, Color.WHITE, 1)

        draw_text(self.renderer, self.font,
                  "LIVES:",
                  text_x, start_y + line_step * 3, Color.WHITE, 1)

        icons_start_x = text_x + 120
        icon_cy = start_y + line_step * 3 + 8
        radius = 7
        old_i = 0

        for i in range(self.remaining_life):
            if i // 7 > old_i // 7:
                icon_cy += 20
                icons_start_x = text_x + 120
            icon_cx = icons_start_x + ((i % 7) * (radius * 2 + 8))
            self.draw_pacman_icon(icon_cx, icon_cy, radius)
            old_i = i

    def draw_infos(self) -> None:
        """
        Dessine les informations du jeu (niveau, score, etc.) sur l'écran.
        """
        self.draw_info()
