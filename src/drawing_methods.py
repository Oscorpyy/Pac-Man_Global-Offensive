from numpy import ndarray
import sdl2
import ctypes
import sdl2.sdlttf as sttf


def put_pixels(pixels_array, x, y, width, height, color) -> None:
    if 0 <= x < width and 0 <= y < height:
        pixels_array[y * width + x] = color


def draw_rect_full(
    pixels: ndarray,
    rect_width: int, rect_height: int,
    color,
    x: int = 0, y: int = 0
) -> None:
    pixels[y: y + rect_height, x: x + rect_width] = color


def clear_background(pixels: ndarray, color: int) -> None:
    pixels[:, :] = color


def draw_sprites(renderer, img_texture, x: int, y: int, scale: int) -> None:
    dest_rect = sdl2.SDL_Rect(x, y, 32 * scale, 32 * scale)
    sdl2.SDL_RenderCopy(renderer, img_texture, None, ctypes.byref(dest_rect))


def draw_sprite_sheet(renderer, img_texture, x: int, y: int, frame: int, scale: int) -> None:
    frame_to_draw: int = 0 + (32 * frame)
    dest_rect = sdl2.SDL_Rect(x, y, 32 * scale, 32 * scale)
    src_rect = sdl2.SDL_Rect(frame_to_draw, 0, 32, 32)
    sdl2.SDL_RenderCopy(renderer, img_texture, ctypes.byref(src_rect), ctypes.byref(dest_rect))


def draw_text(renderer, font, text: str, x: int, y: int, scale: int = 1) -> None:
    text_split: list = text.split(b"\n")
    for i in range(len(text_split)):
        text_surface = sttf.TTF_RenderText_Solid(font, text_split[i], sdl2.SDL_Color(255, 255, 255, 255))
        line_w = text_surface.contents.w
        line_h = text_surface.contents.h
        text_texture = sdl2.SDL_CreateTextureFromSurface(renderer, text_surface)
        sdl2.SDL_FreeSurface(text_surface)
        dest_rect = sdl2.SDL_Rect(x, y + (line_h * i * scale), line_w * scale, line_h * scale)
        sdl2.SDL_RenderCopy(renderer, text_texture, None, ctypes.byref(dest_rect))


# some thing will need to be simplified
class Button:
    def __init__(self, renderer, pixels: ndarray, font, x: int, y: int, w: int, h: int, color_rect, color_hover, function: callable, text: str, scale: int = 1):
        self.renderer = renderer
        self.pixels = pixels
        self.font = font
        self.color_rect = color_rect
        self.color_hover = color_hover
        self.scale = scale
        self.action = function
        self.text = text
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def draw_background(self) -> None:
        mouse_x, mouse_y = ctypes.c_int(0), ctypes.c_int(0)
        button_state = sdl2.mouse.SDL_GetMouseState(ctypes.byref(mouse_x), ctypes.byref(mouse_y))
        if (mouse_x.value >= self.x and mouse_x.value <= self.x + self.w) and (mouse_y.value >= self.y and mouse_y.value <= self.y + self.h):
            draw_rect_full(self.pixels, self.w, self.h, self.color_hover, self.x, self.y)
            if button_state == 1:
                self.action()
        else:
            draw_rect_full(self.pixels, self.w, self.h, self.color_rect, self.x, self.y)

    def draw_text(self) -> None:
        text_split: list = self.text.split(b"\n")
        for i in range(len(text_split)):
            text_surface = sttf.TTF_RenderText_Solid(self.font, text_split[i], sdl2.SDL_Color(255, 255, 255, 255))
            line_w = text_surface.contents.w
            line_h = text_surface.contents.h
            center_y: int = int(self.y + (self.h // 2) - (line_h // 2))
            center_x: int = int(self.x + (self.w // 2) - (line_w // 2))
            text_texture = sdl2.SDL_CreateTextureFromSurface(self.renderer, text_surface)
            sdl2.SDL_FreeSurface(text_surface)
            dest_rect = sdl2.SDL_Rect(center_x, center_y + (line_h * i * self.scale), line_w * self.scale, line_h * self.scale)
            sdl2.SDL_RenderCopy(self.renderer, text_texture, None, ctypes.byref(dest_rect))
