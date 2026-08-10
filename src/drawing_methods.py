from numpy import ndarray, arange, sin, clip
from src.color import Color, color_to_sdl_color
from src.image import Image
import sdl2
import ctypes
import sdl2.sdlttf as sttf


def draw_fps(renderer, font, fps: int) -> None:
    draw_text(renderer, font, f"FPS: {str(fps)}".encode(), 0, 0, Color.GREEN)

def put_pixels(pixels_array: ndarray, x: int, y: int, width: int, height: int, color: Color) -> None:
    if 0 <= x < width and 0 <= y < height:
        pixels_array[y * width + x] = color


def put_pixels_alpha(pixels: ndarray, x: int, y: int, width: int, height: int, color: Color) -> None:
    if 0 <= x < width and 0 <= y < height:
        a_extract = color >> 24 & 0xFF
        if a_extract == 0:
            return
        if a_extract == 255:
            pixels[y, x] = color
        pixel_extract = pixels[y, x]
        br_extract = pixel_extract >> 16 & 0xFF
        bg_extract = pixel_extract >> 8 & 0xFF
        bb_extract = pixel_extract & 0xFF

        r_extract = color >> 16 & 0xFF
        g_extract = color >> 8 & 0xFF
        b_extract = color & 0xFF
        r_final = ((r_extract * a_extract) + (br_extract * (255 - a_extract))) // 255
        g_final = ((g_extract * a_extract) + (bg_extract * (255 - a_extract))) // 255
        b_final = ((b_extract * a_extract) + (bb_extract * (255 - a_extract))) // 255
        final_color = (0xFF << 24) | (r_final << 16) | (g_final << 8) | (b_final)
        pixels[y, x] = final_color


def draw_rect_full(
    pixels: ndarray,
    rect_width: int, rect_height: int,
    color,
    x: int = 0, y: int = 0
) -> None:
    pixels[y: y + rect_height, x: x + rect_width] = color


def draw_rect_not_full(
    pixels: ndarray,
    rect_width: int, rect_height: int,
    color,
    thickness,
    x: int = 0, y: int = 0
) -> None:
    pixels[y: y + thickness, x: x + rect_width] = color
    pixels[rect_height + y: rect_height + y + thickness, x: x + rect_width] = color
    pixels[y : y + rect_height, x: x + thickness] = color
    pixels[y : y + rect_height + thickness, x + rect_width: x + rect_width + thickness] = color


def clear_background(pixels: ndarray, color: int) -> None:
    pixels[:, :] = color


def draw_sprites(renderer, img: Image, x: int, y: int, scale: int) -> None:
    dest_rect = sdl2.SDL_Rect(x, y, 32 * scale, 32 * scale)
    sdl2.SDL_RenderCopy(renderer, img.texture, None, ctypes.byref(dest_rect))


def draw_sprite_sheet(renderer, img: Image, x: int, y: int, frame: int, scale: int) -> None:
    frame_nb_width: int = img.width // 32
    frame_draw_w: int = frame % frame_nb_width
    frame_draw_h: int = frame // frame_nb_width
    frame_x = 32 * frame_draw_w
    frame_y = 32 * frame_draw_h
    dest_rect = sdl2.SDL_Rect(x, y, 32 * scale, 32 * scale)
    src_rect = sdl2.SDL_Rect(frame_x, frame_y, 32, 32)
    sdl2.SDL_RenderCopy(renderer, img.texture, ctypes.byref(src_rect), ctypes.byref(dest_rect))


def draw_text(renderer, font, text: str, x: int, y: int, color: Color, scale: int = 1) -> None:
    text_split: list = text.split(b"\n")
    for i in range(len(text_split)):
        text_surface = sttf.TTF_RenderText_Solid(font, text_split[i], color_to_sdl_color(color))
        line_w = text_surface.contents.w
        line_h = text_surface.contents.h
        text_texture = sdl2.SDL_CreateTextureFromSurface(renderer, text_surface)
        sdl2.SDL_FreeSurface(text_surface)
        dest_rect = sdl2.SDL_Rect(x, y + (line_h * i * scale), line_w * scale, line_h * scale)
        sdl2.SDL_RenderCopy(renderer, text_texture, None, ctypes.byref(dest_rect))
        sdl2.SDL_DestroyTexture(text_texture)


def draw_line(pixels: ndarray, start_x: int, start_y: int, end_x: int, end_y: int, color, thick: int) -> None:
    x_diff = abs(start_x - end_x)
    y_diff = abs(start_y - end_y)
    error = x_diff - y_diff
    if start_y < end_y:
        s_y = 1
    else:
        s_y = -1
    if start_x < end_x:
        s_x = 1
    else:
        s_x = -1
    x_res = []
    y_res = []
    while (True):
        if (start_x == end_x and start_y == end_y):
            break
        x_res.append(start_x)
        y_res.append(start_y)
        error_temp = error * 2
        if error_temp > -y_diff:
            error = error - y_diff
            start_x = start_x + s_x
        if error_temp < x_diff:
            error = error + x_diff
            start_y = start_y + s_y
    pixels[y_res, x_res] = color


def draw_sin(pixels: ndarray, width: int, height: int, center: int, amp: int, frq: float, thickness, color, frame: float) -> None:
    x_coords = arange(width)
    y_coords = center + amp * sin(x_coords * frq + frame)
    y_coords = y_coords.astype(int)
    offset = thickness // 2
    offsets = arange(-offset, offset + 1)[:, None]
    y_thick = clip(y_coords + offsets, 0, height - 1)
    pixels[y_thick, x_coords] = color


def draw_sin_a(pixels: ndarray, width: int, height: int, center: int, amp: int, frq: float, thickness, color, frame: float) -> None:
    a_extract = color >> 24 & 0xFF
    if a_extract == 0:
        return
    x_coords = arange(width)
    y_coords = center + amp * sin(x_coords * frq + frame)
    y_coords = y_coords.astype(int)
    offset = thickness // 2
    offsets = arange(-offset, offset + 1)[:, None]
    y_thick = clip(y_coords + offsets, 0, height - 1)
    if a_extract == 255:
        pixels[y_thick, x_coords] = color
        return
    r_extract = color >> 16 & 0xFF
    g_extract = color >> 8 & 0xFF
    b_extract = color & 0xFF
    inverse_alpha = 255 - a_extract
    r_term = r_extract * a_extract
    g_term = g_extract * a_extract
    b_term = b_extract * a_extract
    pixel_extract = pixels[y_thick, x_coords]
    br_extract = pixel_extract >> 16 & 0xFF
    bg_extract = pixel_extract >> 8 & 0xFF
    bb_extract = pixel_extract & 0xFF


    r_final = ((r_term) + (br_extract * (inverse_alpha))) >> 8
    g_final = ((g_term) + (bg_extract * (inverse_alpha))) >> 8
    b_final = ((b_term) + (bb_extract * (inverse_alpha))) >> 8
    final_color = (0xFF << 24) | (r_final << 16) | (g_final << 8) | (b_final)
    pixels[y_thick, x_coords] = final_color


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

    def draw_text(self, color: Color) -> None:
        text_split: list = self.text.split(b"\n")
        for i in range(len(text_split)):
            text_surface = sttf.TTF_RenderText_Solid(self.font, text_split[i], color_to_sdl_color(color))
            line_w = text_surface.contents.w
            line_h = text_surface.contents.h
            center_y: int = int(self.y + (self.h // 2) - (line_h // 2))
            center_x: int = int(self.x + (self.w // 2) - (line_w // 2))
            text_texture = sdl2.SDL_CreateTextureFromSurface(self.renderer, text_surface)
            sdl2.SDL_FreeSurface(text_surface)
            dest_rect = sdl2.SDL_Rect(center_x, center_y + (line_h * i * self.scale), line_w * self.scale, line_h * self.scale)
            sdl2.SDL_RenderCopy(self.renderer, text_texture, None, ctypes.byref(dest_rect))
            sdl2.SDL_DestroyTexture(text_texture)
