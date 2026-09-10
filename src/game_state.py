from enum import Enum
from sdl2 import (
    SDLK_LEFT, SDLK_RIGHT, SDLK_UP, SDLK_DOWN, SDLK_b, SDLK_a
)
from collections import deque
from typing import Any


class ScenePossible(Enum):
    INTRO = "introduction"
    MAIN = "main"
    GAME = "game"
    WIN = "win_screen"
    LOOSE = "loose_screen"
    CSGO = "global_offensive"


class GameState:
    def __init__(self) -> None:
        """Initialize the global game state attributes."""
        self.is_running: bool = True
        self.scene = ScenePossible.INTRO
        self.frame: int = 1
        self.konami_code_excepted: list[int] = [
            SDLK_UP, SDLK_UP, SDLK_DOWN,
            SDLK_DOWN, SDLK_LEFT, SDLK_RIGHT,
            SDLK_LEFT, SDLK_RIGHT,
            SDLK_b, SDLK_a
        ]
        self.konami_code_entered: list[int] = []
        self.fps_lst: deque[float] = deque(maxlen=30)
        self.fps: int = 0
        self.cs_round_win: int = 0
        self.cs_round_loose: int = 0
        self.dt: float = 0.0
        self._point: int = 0

    @property
    def point(self) -> int:
        """Get the current point score clamped to 32-bit signed max integer.

        Returns:
            The current point total.
        """
        if self._point > 2147483648:
            self._point = 2147483647
        return self._point

    @point.setter
    def point(self, value: int) -> None:
        """Set the current point score clamped to 32-bit signed max integer.

        Args:
            value: The new point value to set.
        """
        if value > 2147483648:
            self._point = 2147483647
        else:
            self._point = value

    def get_points(self) -> int:
        """Return the current player score.

        Returns:
            int: The player's total accumulated points.
        """
        return self.point

    def check_cs_finished(self) -> None:
        """Check if Counter-Strike game mode has ended and set scene."""
        if self.scene != ScenePossible.CSGO:
            return
        if self.cs_round_win >= 5:
            self.point += ((2147483647 // 6) * self.cs_round_win - (
                    2147483647 // 7) * self.cs_round_loose)
            self.scene = ScenePossible.WIN
        elif self.cs_round_loose >= 5:
            self.point += ((2147483647 // 6) * self.cs_round_win - (
                    2147483647 // 7) * self.cs_round_loose)
            if self.point < 0:
                self.point = 0
            self.scene = ScenePossible.LOOSE


class GameConfig:
    def __init__(self, config_content: dict[str, Any]) -> None:
        """Initialize game configuration from a parsed dictionary.

        Args:
            config_content: Dictionary of loaded configuration options.
        """
        self.config_content = config_content
        self.highscore_filename: str = str(
            config_content.get("highscore_filename", "scores.json")
        )
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
