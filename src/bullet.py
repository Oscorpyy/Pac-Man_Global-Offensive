import math
from src.drawing_methods import draw_sprites
from src.image import Image


class Bullet:
    def __init__(self, renderer, x: int = 0, y: int = 0) -> None:
        self.x = float(x)
        self.y = float(y)
        self.dx: int = 0
        self.dy: int = 0
        self.speed: int = 8
        self.renderer = renderer
        self.img = Image(b"assets/3D_model/computer.png", renderer)
        self.max_travel: int = 1500

    def draw_bullet(self, offset_x, offset_y) -> None:
        draw_sprites(self.renderer, self.img, int((self.x - offset_x) * 2), int((self.y - offset_y) * 2), 2)
        self.update_pos()

    def update_pos(self) -> None:
        dist = math.hypot(self.dx, self.dy)
        if dist != 0:
            dir_x = (self.dx / dist) * self.speed
            dir_y = (self.dy / dist) * self.speed
            self.x += dir_x
            self.y += dir_y
        self.max_travel -= self.speed


    def set_direction(self, mouse_x, mouse_y, width: int, height: int) -> None:
        self.dx = mouse_x.value - (width // 2)
        self.dy = mouse_y.value - (height // 2)

    def set_direction_target(self, target_x, target_y, bot_x: int, bot_y: int) -> None:
        self.dx = target_x - bot_x
        self.dy = target_y - bot_y
