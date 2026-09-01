import math
from src.camera import Camera
from src.image import Image
from src.drawing_methods import draw_sprite_sheet


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
    def __init__(self) -> None:
        pass
