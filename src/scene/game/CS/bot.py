from src.scene.helper import Vector2
from src.camera import Camera
from src.image import Image
from src.drawing_methods import draw_sprite_sheet
import random
import math


class ZoneMovement:
    def __init__(self) -> None:
        self.zone_lst: list = [
                [
                    Vector2(x=32, y=128),
                    Vector2(x=256, y=128),
                ],
                [
                    Vector2(x=160, y=544),
                    Vector2(x=320, y=736),
                ],
                [
                    Vector2(x=32, y=128),
                    Vector2(x=256, y=128),
                ],
                [
                    Vector2(x=32, y=128),
                    Vector2(x=256, y=128),
                ],
                [
                    Vector2(x=32, y=128),
                    Vector2(x=256, y=128),
                ],
        ]

    def get_random_zone(self) -> list[Vector2]:
        return self.zone_lst[random.randint(0, len(self.zone_lst) - 1)]


class CsBot:
    def __init__(self, sprite: Image, cam: Camera) -> None:
        self.cam: Camera = cam
        self.can_move: bool = True
        self.can_collide: bool = True
        self.can_shoot: bool = True
        self.sprite: Image = sprite
        self.current_frame: int = 0
        self.frame_number: int = 24
        self.animation_speed: int = 5
        self.tick_counter: int = 0
        self.zone = ZoneMovement()
        self.possible_target: list[Vector2] = self.zone.get_random_zone()
        self.target_position: Vector2 = self.possible_target[1]
        self.pos_x: int = self.possible_target[0].x
        self.pos_y: int = self.possible_target[0].y
        self.speed: int = 3
        self.dx = 0
        self.dy = 0

    def update(self) -> None:
        self.tick_counter += 1
        if self.tick_counter >= self.animation_speed:
            self.tick_counter = 0
            self.current_frame += 1
            self.current_frame = self.current_frame % self.frame_number

    def get_next_location(self) -> None:
        if self.pos_x == self.target_position.x and self.pos_y == self.target_position.y:
            if self.target_position == self.possible_target[1]:
                self.target_position = self.possible_target[0]
            else:
                self.target_position = self.possible_target[1]

    def move_bot(self) -> None:
        self.dx = self.target_position.x - self.pos_x
        self.dy = self.target_position.y - self.pos_y
        dist = math.hypot(self.dx, self.dy)
        if dist > 0:
            if dist <= self.speed:
                self.pos_x = self.target_position.x
                self.pos_y = self.target_position.y
            else:
                self.pos_x += int((self.dx / dist) * self.speed)
                self.pos_y += int((self.dy / dist) * self.speed)

    def detect_player(self) -> None:
        pass

    def draw_bot(self, renderer,  scale: int) -> None:
        pos_x = (self.pos_x - self.cam.offset_x) * scale
        pos_y = (self.pos_y - self.cam.offset_y) * scale
        dx = self.dx
        dy = self.dy
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
