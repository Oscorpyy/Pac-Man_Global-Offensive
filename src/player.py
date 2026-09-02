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

    def update(self) -> None:
        self.tick_counter += 1
        if self.tick_counter >= self.animation_speed:
            self.tick_counter = 0
            self.current_frame += 1
            self.current_frame = self.current_frame % self.frame_number

    def draw_player(self, renderer,  scale: int) -> None:
        if self.key_a is True and self.key_w is True:
            draw_sprite_sheet(renderer, self.sprite,
                              (self.pos_x - self.cam.offset_x) * scale,
                              (self.pos_y - self.cam.offset_y) * scale,
                              self.current_frame + 125, scale)
        elif self.key_a is True and self.key_s is True:
            draw_sprite_sheet(renderer, self.sprite,
                              (self.pos_x - self.cam.offset_x) * scale,
                              (self.pos_y - self.cam.offset_y) * scale,
                              self.current_frame + 101, scale)
        elif self.key_d is True and self.key_s is True:
            draw_sprite_sheet(renderer, self.sprite,
                              (self.pos_x - self.cam.offset_x) * scale,
                              (self.pos_y - self.cam.offset_y) * scale,
                              self.current_frame + 150, scale)
        elif self.key_d is True and self.key_w is True:
            draw_sprite_sheet(renderer, self.sprite,
                              (self.pos_x - self.cam.offset_x) * scale,
                              (self.pos_y - self.cam.offset_y) * scale,
                              self.current_frame + 175, scale)
        elif self.key_w is True:
            draw_sprite_sheet(renderer, self.sprite,
                              (self.pos_x - self.cam.offset_x) * scale,
                              (self.pos_y - self.cam.offset_y) * scale,
                              self.current_frame + 75, scale)
        elif self.key_a is True:
            draw_sprite_sheet(renderer, self.sprite,
                              (self.pos_x - self.cam.offset_x) * scale,
                              (self.pos_y - self.cam.offset_y) * scale,
                              self.current_frame + 50, scale)
        elif self.key_d is True:
            draw_sprite_sheet(renderer, self.sprite,
                              (self.pos_x - self.cam.offset_x) * scale,
                              (self.pos_y - self.cam.offset_y) * scale,
                              self.current_frame + 26, scale)
        else:
            draw_sprite_sheet(renderer, self.sprite,
                              (self.pos_x - self.cam.offset_x) * scale,
                              (self.pos_y - self.cam.offset_y) * scale,
                              self.current_frame, scale)


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
        self.animation_speed: int = 5
        self.tick_counter: int = 0

        self.move_cooldown: int = 12
        self.move_tick: int = 0

        self.key_w: bool = False
        self.key_s: bool = False
        self.key_a: bool = False
        self.key_d: bool = False

        self.is_powered_up: bool = False
        self.power_timer: int = 0

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
                        items_matrix: list[list[int]]) -> None:
        """
        Déplace Pac-Man selon les murs (bits 1=Nord, 2=Est, 4=Sud, 8=Ouest)
        et consomme les pacgums sur son passage.
        """
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
            elif item == 2:  # Super-pacgum
                items_matrix[self.pos_y][self.pos_x] = 0
                self.is_powered_up = True
                self.power_timer = 600  # 10 secondes (60 frames * 10)

    def draw_player_pixels(self, pixels: np.ndarray, start_x: int,
                           start_y: int, cellsize: int, color: int) -> None:
        """
        Dessine Pac-Man avec un effet de couleur
        clignotant s'il est en mode super-pacgum.
        """
        cx = start_x + (self.pos_x * cellsize) + (cellsize // 2)
        cy = start_y + (self.pos_y * cellsize) + (cellsize // 2)

        radius = max(3, int(cellsize * 0.4))

        draw_color = color
        if self.is_powered_up:
            if (10 > (self.power_timer % 10) > 0):
                draw_color = Color.PURPLE
            elif (20 > (self.power_timer % 10) > 10):
                draw_color = Color.BLUE
            elif (30 > (self.power_timer % 10) > 10):
                draw_color = Color.GREEN
            elif (40 > (self.power_timer % 10) > 10):
                draw_color = Color.YELLOW
            elif (50 > (self.power_timer % 10) > 10):
                draw_color = Color.RED
            elif (60 > (self.power_timer % 10) > 10):
                draw_color = Color.PURPLE
            elif (70 > (self.power_timer % 10) > 10):
                draw_color = Color.BLUE
            elif (80 > (self.power_timer % 10) > 10):
                draw_color = Color.GREEN
            elif (90 > (self.power_timer % 10) > 10):
                draw_color = Color.YELLOW
            else:
                draw_color = Color.WHITE
            print(f"Power timer: {self.power_timer}, Draw color: {draw_color}")

        height, width = pixels.shape
        y1 = max(0, cy - radius)
        y2 = min(height, cy + radius)
        x1 = max(0, cx - radius)
        x2 = min(width, cx + radius)

        if y2 > y1 and x2 > x1:
            pixels[y1:y2, x1:x2] = draw_color

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
