from enum import Enum
from sdl2 import SDLK_LEFT, SDLK_RIGHT, SDLK_UP, SDLK_DOWN
from collections import deque


class ScenePossible(Enum):
    MAIN = "main"
    GAME = "game"
    WIN = "win_screen"
    LOOSE = "loose_screen"
    CSGO = "global_offensive"


class GameState:
    def __init__(self) -> None:
        self.is_running: bool = True
        self.scene = ScenePossible.MAIN
        self.frame: int = 1
        self.konami_code_excepted: list = [SDLK_UP, SDLK_UP, SDLK_DOWN, SDLK_DOWN, SDLK_LEFT, SDLK_RIGHT, SDLK_LEFT, SDLK_RIGHT]
        self.konami_code_entered: list = []
        self.fps_lst = deque(maxlen=30)
        self.fps: int = 0


class GameConfig:
    def __init__(self, config_content: dict) -> None:
        self.config_content = config_content
        self.highscore_filename = config_content.get("highscore_filename")
        self.level_array_multiple_levels = config_content.get("level_array_multiple_levels", None)
        self.lives = config_content.get("lives", None)
        self.pacgum = config_content.get("pacgum", None)
        self.points_per_pacgum = config_content.get("points_per_pacgum", None)
        self.points_per_super_pacgum = config_content.get("points_per_super_pacgum", None)
        self.points_per_ghost = config_content.get("points_per_ghost", None)
        self.seed = config_content.get("seed", None)
        self.level_max_time = config_content.get("level_max_time", None)
        self.screen_width = config_content.get("screen_width", 800)
        self.screen_height = config_content.get("screen_height", 600)
