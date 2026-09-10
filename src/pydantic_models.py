from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator


class LevelConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    width: int = Field(ge=3, le=30)
    height: int = Field(ge=3, le=30)


def generate_default_levels() -> list[LevelConfig]:
    return [
        LevelConfig(name="level1", width=10, height=10),
        LevelConfig(name="level2", width=15, height=15),
        LevelConfig(name="level3", width=15, height=15),
        LevelConfig(name="level4", width=10, height=10),
        LevelConfig(name="level5", width=15, height=15),
        LevelConfig(name="level6", width=15, height=15),
        LevelConfig(name="level7", width=15, height=15),
        LevelConfig(name="level8", width=10, height=10),
        LevelConfig(name="level9", width=15, height=15),
        LevelConfig(name="level10", width=15, height=15),
    ]


class Config(BaseModel):
    model_config = ConfigDict(extra="forbid")

    highscore_filename: str = Field(min_length=1, default="scores.json")
    level_array_multiple_levels: list[LevelConfig] = Field(
        default_factory=generate_default_levels
    )
    lives: StrictInt = Field(ge=1, le=105, default=3)
    points_per_pacgum: int = Field(ge=0, le=2147483647, default=10)
    points_per_super_pacgum: int = Field(ge=0, le=2147483647, default=50)
    points_per_ghost: int = Field(ge=0, le=2147483647, default=200)
    seed: int = Field(gt=0, default=42)
    level_max_time: int = Field(gt=0, le=2147483647, default=90)
    screen_width: int = Field(gt=0, default=1920)
    screen_height: int = Field(gt=0, default=1080)

    @field_validator("highscore_filename")
    @classmethod
    def highscore_filename_must_not_be_blank(cls, value: str) -> str:
        """Validate that highscore_filename is not blank.

        Args:
            value: Highscore file path string to validate.

        Returns:
            str: Validated highscore file path string.

        Raises:
            ValueError: If the file path string is blank.
        """
        if not value.strip():
            raise ValueError("highscore_filename must not be empty")
        return value


class Score(BaseModel):
    name: str
    point: int


class Highscore(BaseModel):
    scores: list[Score]
