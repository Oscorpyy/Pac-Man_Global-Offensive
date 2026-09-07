from enum import Enum
from sdl2 import (
    SDLK_LEFT, SDLK_RIGHT, SDLK_UP, SDLK_DOWN, SDLK_b, SDLK_a
)
from collections import deque


class ScenePossible(Enum):
    INTRO = "introduction"
    MAIN = "main"
    GAME = "game"
    WIN = "win_screen"
    LOOSE = "loose_screen"
    CSGO = "global_offensive"


class GameState:
    def __init__(self) -> None:
        self.is_running: bool = True
        self.scene = ScenePossible.INTRO
        self.frame: int = 1
        self.konami_code_excepted: list = [
            SDLK_UP, SDLK_UP, SDLK_DOWN,
            SDLK_DOWN, SDLK_LEFT, SDLK_RIGHT,
            SDLK_LEFT, SDLK_RIGHT,
            SDLK_b, SDLK_a
        ]
        self.konami_code_entered: list = []
        self.fps_lst = deque(maxlen=30)
        self.fps: int = 0
        self.cs_round_win: int = 0
        self.cs_round_loose: int = 0
        self.dt: float = 0.0
        self._point: int = 0

    @property
    def point(self) -> int:
        if self._point > 2147483647:
            self._point = 2147483647
        return self._point

    def get_points(self) -> int:
        """Retourne le nombre de points du joueur."""
        return self.point

    @point.setter
    def point(self, value: int) -> None:
        if value > 2147483647:
            self._point = 2147483647
        else:
            self._point = value

    def check_cs_finished(self) -> None:
        if self.cs_round_win >= 5:
            self.scene = ScenePossible.WIN
        if self.cs_round_loose >= 5:
            self.scene = ScenePossible.LOOSE


class GameConfig:
    def __init__(self, config_content: dict) -> None:
        self.config_content = config_content
        self.highscore_filename = config_content.get("highscore_filename")
        self.level_array_multiple_levels = config_content.get(
            "level_array_multiple_levels", None)
        self.lives = config_content.get("lives", None)
        self.pacgum = config_content.get("pacgum", None)
        self.points_per_pacgum = config_content.get("points_per_pacgum", None)
        self.points_per_super_pacgum = config_content.get(
            "points_per_super_pacgum", None)
        self.points_per_ghost = config_content.get("points_per_ghost", None)
        self.seed = config_content.get("seed", None)
        self.level_max_time = config_content.get("level_max_time", None)
        self.screen_width = config_content.get("screen_width", 800)
        self.screen_height = config_content.get("screen_height", 600)
