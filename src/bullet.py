import math
import sdl2
import ctypes
from src.drawing_methods import draw_sprites
from src.image import Image


class Bullet:
    """Represent a projectile in the bonus Counter-Strike mini-game."""

    def __init__(self, renderer: sdl2.render.SDL_Renderer,
                 x: int = 0, y: int = 0) -> None:
        """Initialize bullet position and load its sprite.

        Args:
            renderer: SDL2 renderer to bind the bullet sprite.
            x: Initial X coordinate.
            y: Initial Y coordinate.
        """
        self.x = float(x)
        self.y = float(y)
        self.dx: int = 0
        self.dy: int = 0
        self.speed: int = 8
        self.renderer = renderer
        self.img = Image(b"assets/3D_model/computer.png", renderer)
        self.max_travel: int = 1500

    def draw_bullet(self, offset_x: int, offset_y: int) -> None:
        """Draw bullet on screen and update its position.

        Args:
            offset_x: Camera horizontal offset.
            offset_y: Camera vertical offset.
        """
        draw_sprites(self.renderer, self.img, int((self.x - offset_x) * 2),
                     int((self.y - offset_y) * 2), 2)
        self.update_pos()

    def update_pos(self) -> None:
        """Update bullet position along its trajectory and decrease range."""
        dist = math.hypot(self.dx, self.dy)
        if dist != 0:
            dir_x = (self.dx / dist) * self.speed
            dir_y = (self.dy / dist) * self.speed
            self.x += dir_x
            self.y += dir_y
        self.max_travel -= self.speed

    def set_direction(self, mouse_x: ctypes.c_int, mouse_y: ctypes.c_int,
                      width: int, height: int) -> None:
        """Calculate bullet direction vector toward mouse position.

        Args:
            mouse_x: Mouse horizontal coordinate.
            mouse_y: Mouse vertical coordinate.
            width: Viewport width.
            height: Viewport height.
        """
        self.dx = mouse_x.value - (width // 2)
        self.dy = mouse_y.value - (height // 2)

    def set_direction_target(self, target_x: int, target_y: int,
                             bot_x: int, bot_y: int) -> None:
        """Calculate bullet direction vector toward target position.

        Args:
            target_x: Target horizontal coordinate.
            target_y: Target vertical coordinate.
            bot_x: Origin bot horizontal coordinate.
            bot_y: Origin bot vertical coordinate.
        """
        self.dx = target_x - bot_x
        self.dy = target_y - bot_y
