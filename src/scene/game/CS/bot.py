from src.scene.helper import Vector2
from src.camera import Camera
from src.image import Image
from src.drawing_methods import draw_sprite_sheet
from src.bullet import Bullet
from src.game_state import GameState
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
                    Vector2(x=640, y=160),
                    Vector2(x=640, y=320),
                ],
                [
                    Vector2(x=896, y=96),
                    Vector2(x=896, y=544),
                ],
                [
                    Vector2(x=64, y=480),
                    Vector2(x=64, y=960),
                ],
        ]


class CsBot:
    def __init__(self, sprite: Image, cam: Camera, possible_target: list[Vector2]) -> None:
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
        self.possible_target: list[Vector2] = possible_target
        self.target_position: Vector2 = self.possible_target[1]
        self.pos_x: int = self.possible_target[0].x
        self.pos_y: int = self.possible_target[0].y
        self.speed: int = 3
        self.dx = 0
        self.dy = 0
        self.bullet_lst: list = []
        self.cooldown: float = 0.6

    def update(self, config: GameState) -> None:
        self.tick_counter += 1
        if self.tick_counter >= self.animation_speed:
            self.tick_counter = 0
            self.current_frame += 1
            self.current_frame = self.current_frame % self.frame_number
        self.cooldown -= config.dt

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

    def detect_player(self, player_x: int, player_y: int, renderer) -> None:
        detection_size: int = 128
        if (self.pos_x + detection_size > player_x and self.pos_x < player_x + detection_size and
            self.pos_y + detection_size > player_y and self.pos_y < player_y + detection_size):
                if self.cooldown < 0:
                    new_bullet = Bullet(renderer, self.pos_x, self.pos_y)
                    new_bullet.set_direction_target(player_x, player_y, self.pos_x, self.pos_y)
                    self.bullet_lst.append(new_bullet)
                    self.cooldown = 0.6

    def draw_bullet(self, offset_x, offset_y) -> None:
        for bullet in self.bullet_lst:
            bullet.draw_bullet(offset_x, offset_y)
            bullet.update_pos()

    def kill_bullet(self, tilemap) -> None:
        i = 0
        for bullet in self.bullet_lst:
            if bullet.max_travel < 0:
                self.bullet_lst.pop(i)
            if self.check_bullet_collide_wall(bullet.x + bullet.speed, bullet.y + bullet.speed, tilemap) is False:
                self.bullet_lst.pop(i)
        i += 1

    def check_bullet_collide_wall(self, pos_x: int, pos_y: int, tilemap) -> bool:
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

    def check_bullet_collide_ennemy(self, bullet_pos_x: int, bullet_pos_y: int, player_x: int, player_y: int) -> bool:
        bullet_size: int = 32
        if (bullet_pos_x + bullet_size > player_x and bullet_pos_x < player_x + 32 and
            bullet_pos_y + bullet_size > player_y and bullet_pos_y < player_y + 32):
            return True
        return False

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
