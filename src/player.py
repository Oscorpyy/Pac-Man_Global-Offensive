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

    def update(self) -> None:
        self.tick_counter += 1
        if self.tick_counter >= self.animation_speed:
            self.tick_counter = 0
            self.current_frame += 1
            self.current_frame = self.current_frame % self.frame_number

    def draw_player(self, renderer,  scale: int) -> None:
        if self.key_a is True and self.key_w is True:
            draw_sprite_sheet(renderer, self.sprite, (self.pos_x - self.cam.offset_x) * scale, (self.pos_y - self.cam.offset_y) * scale, self.current_frame + 125, scale)
        elif self.key_a is True and self.key_s is True:
            draw_sprite_sheet(renderer, self.sprite, (self.pos_x - self.cam.offset_x) * scale, (self.pos_y - self.cam.offset_y) * scale, self.current_frame + 101, scale)
        elif self.key_d is True and self.key_s is True:
            draw_sprite_sheet(renderer, self.sprite, (self.pos_x - self.cam.offset_x) * scale, (self.pos_y - self.cam.offset_y) * scale, self.current_frame + 150, scale)
        elif self.key_d is True and self.key_w is True:
            draw_sprite_sheet(renderer, self.sprite, (self.pos_x - self.cam.offset_x) * scale, (self.pos_y - self.cam.offset_y) * scale, self.current_frame + 175, scale)
        elif self.key_w is True:
            draw_sprite_sheet(renderer, self.sprite, (self.pos_x - self.cam.offset_x) * scale, (self.pos_y - self.cam.offset_y) * scale, self.current_frame + 75, scale)
        elif self.key_a is True:
            draw_sprite_sheet(renderer, self.sprite, (self.pos_x - self.cam.offset_x) * scale, (self.pos_y - self.cam.offset_y) * scale, self.current_frame + 50, scale)
        elif self.key_d is True:
            draw_sprite_sheet(renderer, self.sprite, (self.pos_x - self.cam.offset_x) * scale, (self.pos_y - self.cam.offset_y) * scale, self.current_frame + 26, scale)
        else:
            draw_sprite_sheet(renderer, self.sprite, (self.pos_x - self.cam.offset_x) * scale, (self.pos_y - self.cam.offset_y) * scale, self.current_frame, scale)


class PacPlayer:
    def __init__(self) -> None:
        pass
