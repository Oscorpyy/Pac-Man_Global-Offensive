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

def draw_text(renderer, font, text: str, scale: int) -> None:
    len_text: int = len(text)
    text_split: list = text.split(b"\n")
    for i in range(len(text_split)):
        text_surface = sttf.TTF_RenderText_Solid(font, text_split[i], sdl2.SDL_Color(255, 255, 255, 255))
        line_w = text_surface.contents.w
        line_h = text_surface.contents.h
        text_texture = sdl2.SDL_CreateTextureFromSurface(renderer, text_surface)
        sdl2.SDL_FreeSurface(text_surface)
        dest_rect = sdl2.SDL_Rect(0,line_h * i * scale, line_w * scale, line_h * scale)
        sdl2.SDL_RenderCopy(renderer, text_texture, None, ctypes.byref(dest_rect))
