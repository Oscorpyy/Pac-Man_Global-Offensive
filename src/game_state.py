from enum import Enum


class ScenePossible(Enum):
    MAIN = "main"
    GAME = "game"
    WIN = "win_screen"
    LOOSE = "loose_screen"


class GameState:
    def __init__(self) -> None:
        self.is_running: bool = True
        self.scene = ScenePossible.MAIN
        self.frame: int = 1
