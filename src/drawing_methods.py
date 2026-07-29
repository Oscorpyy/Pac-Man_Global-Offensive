from numpy import ndarray
import sdl2
import ctypes


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
