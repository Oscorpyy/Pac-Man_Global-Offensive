from pydantic import BaseModel


class LevelConfig(BaseModel):
    name: str
    width: int
    height: int


class Config(BaseModel):
    highscore_filename: str
    level_array_multiple_levels: list[LevelConfig]
    lives: int
    pacgum: int
    points_per_pacgum: int
    points_per_super_pacgum: int
    points_per_ghost: int
    seed: int
    level_max_time: int


class Score(BaseModel):
    name: str
    point: int


class Highscore(BaseModel):
    scores: list[Score]
