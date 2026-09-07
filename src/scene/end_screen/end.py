import sdl2
import sdl2.sdlimage as sdim

from src.drawing_methods import draw_sprites_fullscreen
from src.game_state import GameState, ScenePossible
from src.image import Image


class EndScreen:
    def __init__(self, renderer, game_state: GameState, width: int,
                 height: int, image_path: str, reset_callback) -> None:
        self.renderer = renderer
        self.game_state = game_state
        self.width = width
        self.height = height
        self.reset_callback = reset_callback
        self.image = Image(image_path, renderer)

    def handle_event(self, event) -> None:
        if event.type != sdl2.SDL_KEYDOWN:
            return
        if self.game_state.scene not in (ScenePossible.WIN,
                                         ScenePossible.LOOSE):
            return
        self.reset_callback()
        self.game_state.scene = ScenePossible.MAIN

    def draw(self) -> None:
        draw_sprites_fullscreen(
            self.renderer, self.image, 0, 0, 1, self.width, self.height
        )

    def clean_up(self) -> None:
        sdl2.SDL_DestroyTexture(self.image.texture)
        sdim.IMG_Quit()
