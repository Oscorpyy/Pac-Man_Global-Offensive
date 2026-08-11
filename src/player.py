from src.camera import Camera
from src.image import Image
from src.drawing_methods import draw_sprites


class CsPlayer:
    def __init__(self, sprite: Image, cam: Camera) -> None:
        self.pos_x: int = 0
        self.pos_y: int = 0
        self.can_move: bool = True
        self.can_collide: bool = True
        self.can_shoot: bool = True
        self.sprite: Image = sprite
        self.cam = cam

    def draw_player(self, renderer,  scale: int) -> None:
        draw_sprites(renderer, self.sprite, (self.pos_x - self.cam.offset_x) * scale, (self.pos_y - self.cam.offset_y) * scale, scale)


class PacPlayer:
    def __init__(self) -> None:
        pass
