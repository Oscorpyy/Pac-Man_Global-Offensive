from pydantic import BaseModel, Field


class LevelConfig(BaseModel):
    name: str
    width: int
    height: int


class Config(BaseModel):
    highscore_filename: str
    level_array_multiple_levels: list[LevelConfig]
    lives: int = Field(ge=1, le=105)
    points_per_pacgum: int
    points_per_super_pacgum: int
    points_per_ghost: int
    seed: int
    level_max_time: int
    screen_width: int
    screen_height: int


class Score(BaseModel):
    name: str
    point: int


class Highscore(BaseModel):
    scores: list[Score]
