import sdl2
import sdl2.sdlimage as sdim
from src.print_logs import print_error


class Image:
    def __init__(self, img_path: str | bytes, renderer) -> None:
        if isinstance(img_path, bytes):
            load_path = img_path
        else:
            load_path = img_path.encode("utf-8")

        self.img_surface = sdim.IMG_Load(load_path)
        if not self.img_surface:
            print_error(f"can't charge image {sdim.IMG_GetError()}")
        self.width = self.img_surface.contents.w
        self.height = self.img_surface.contents.h
        self.texture = sdl2.SDL_CreateTextureFromSurface(
            renderer, self.img_surface
        )
        sdl2.SDL_FreeSurface(self.img_surface)

