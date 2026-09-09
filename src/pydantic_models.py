from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator


class LevelConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    width: int = Field(ge=3, le=30)
    height: int = Field(ge=3, le=30)


class Config(BaseModel):
    model_config = ConfigDict(extra="forbid")

    highscore_filename: str = Field(min_length=1)
    level_array_multiple_levels: list[LevelConfig]
    lives: StrictInt = Field(ge=1, le=105)
    points_per_pacgum: int = Field(ge=0, le=2147483647)
    points_per_super_pacgum: int = Field(ge=0, le=2147483647)
    points_per_ghost: int = Field(ge=0, le=2147483647)
    seed: int
    level_max_time: int = Field(gt=0)
    screen_width: int = Field(gt=0)
    screen_height: int = Field(gt=0)

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
