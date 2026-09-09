from numpy import ndarray, arange, sin, clip
from src.color import Color, color_to_sdl_color
from src.image import Image
from collections.abc import Callable
import sdl2
import ctypes
import sdl2.sdlttf as sttf
from typing import Any


def draw_fps(renderer: sdl2.render.SDL_Renderer,
             font: ctypes.c_void_p, fps: int) -> None:
    """Render the current FPS counter text onto the screen.

    Args:
        renderer: SDL renderer used for rendering text.
        font: Loaded TTF font pointer.
        fps: Current frames per second value.
    """
    draw_text(renderer, font, f"FPS: {fps}", 5, 5, Color.BLACK)


def put_pixels(pixels_array: ndarray, x: int, y: int, width: int,
               height: int, color: Color) -> None:
    """Set the pixel color at coordinates (x, y) if within bounds.

    Args:
        pixels_array: Flat 1D numpy array of screen pixels.
        x: Horizontal pixel coordinate.
        y: Vertical pixel coordinate.
        width: Screen width in pixels.
        height: Screen height in pixels.
        color: ARGB color value to write.
    """
    if 0 <= x < width and 0 <= y < height:
        pixels_array[y * width + x] = color


def put_pixels_alpha(pixels: ndarray, x: int, y: int, width: int,
                     height: int, color: Color) -> None:
    """Alpha-blend and write a single pixel into the pixel buffer.

    Args:
        pixels: 2D numpy array of screen pixels (height x width).
        x: Horizontal coordinate.
        y: Vertical coordinate.
        width: Pixel buffer width.
        height: Pixel buffer height.
        color: ARGB color value with alpha channel.
    """
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
        r_final = ((r_extract * a_extract) + (br_extract * (
                    255 - a_extract))) // 255
        g_final = ((g_extract * a_extract) + (bg_extract * (
                    255 - a_extract))) // 255
        b_final = ((b_extract * a_extract) + (bb_extract * (
                    255 - a_extract))) // 255
        final_color = (0xFF << 24) | (r_final << 16) | (g_final << 8) | (
            b_final)
        pixels[y, x] = final_color


def draw_rect_full(
    pixels: ndarray,
    rect_width: int, rect_height: int,
    color: Color,
    x: int = 0, y: int = 0
) -> None:
    """Fill a solid rectangle into a 2D numpy pixel buffer.

    Args:
        pixels: 2D numpy array of screen pixels.
        rect_width: Width of rectangle in pixels.
        rect_height: Height of rectangle in pixels.
        color: Color to fill.
        x: Starting horizontal coordinate.
        y: Starting vertical coordinate.
    """
    pixels[y: y + rect_height, x: x + rect_width] = color


def draw_rect_not_full(
    pixels: ndarray,
    rect_width: int, rect_height: int,
    color: Color,
    thickness: int,
    x: int = 0, y: int = 0
) -> None:
    """Draw a hollow rectangle outline into a 2D numpy pixel buffer.

    Args:
        pixels: 2D numpy array of screen pixels.
        rect_width: Width of the rectangle bounding box.
        rect_height: Height of the rectangle bounding box.
        color: Color for rectangle borders.
        thickness: Border thickness in pixels.
        x: Starting horizontal coordinate.
        y: Starting vertical coordinate.
    """
    pixels[y: y + thickness, x: x + rect_width] = color
    pixels[rect_height + y: rect_height + y + thickness,
           x: x + rect_width] = color
    pixels[y: y + rect_height, x: x + thickness] = color
    pixels[y: y + rect_height + thickness,
           x + rect_width: x + rect_width + thickness] = color


def clear_background(pixels: ndarray, color: int) -> None:
    """Fill the entire pixel buffer with a solid color.

    Args:
        pixels: 2D numpy pixel array.
        color: ARGB color value to clear buffer with.
    """
    pixels[:, :] = color


def draw_sprites(renderer: sdl2.render.SDL_Renderer, img: Image,
                 x: int, y: int, scale: float) -> None:
    """Render a scaled image sprite to the screen.

    Args:
        renderer: SDL renderer instance.
        img: Source Image object to draw.
        x: Destination X screen coordinate.
        y: Destination Y screen coordinate.
        scale: Scaling multiplier for image dimensions.
    """
    dest_w: int = int(img.width * scale)
    dest_h: int = int(img.height * scale)
    dest_rect = sdl2.SDL_Rect(x, y, dest_w, dest_h)
    sdl2.SDL_RenderCopy(renderer, img.texture, None, ctypes.byref(dest_rect))


def draw_sprites_fullscreen(renderer: sdl2.render.SDL_Renderer,
                            img: Image, x: int, y: int,
                            scale: float, dest_w: int, dest_h: int) -> None:
    """Render a sprite stretched to specified destination dimensions.

    Args:
        renderer: SDL renderer instance.
        img: Source Image object to draw.
        x: Destination X screen coordinate.
        y: Destination Y screen coordinate.
        scale: Unused scale parameter preserved for API compatibility.
        dest_w: Destination width in pixels.
        dest_h: Destination height in pixels.
    """
    dest_rect = sdl2.SDL_Rect(x, y, dest_w, dest_h)
    sdl2.SDL_RenderCopy(renderer, img.texture, None, ctypes.byref(dest_rect))


def draw_sprite_sheet(renderer: sdl2.render.SDL_Renderer,
                      img: Image, x: int, y: int,
                      frame: int, scale: int) -> None:
    """Draw an individual 32x32 frame from a sprite sheet texture.

    Args:
        renderer: SDL renderer instance.
        img: Sprite sheet Image object.
        x: Destination X screen coordinate.
        y: Destination Y screen coordinate.
        frame: 0-indexed frame index to extract.
        scale: Integer scale factor.
    """
    frame_nb_width: int = img.width // 32
    frame_draw_w: int = frame % frame_nb_width
    frame_draw_h: int = frame // frame_nb_width
    frame_x = 32 * frame_draw_w
    frame_y = 32 * frame_draw_h
    dest_rect = sdl2.SDL_Rect(x, y, 32 * scale, 32 * scale)
    src_rect = sdl2.SDL_Rect(frame_x, frame_y, 32, 32)
    sdl2.SDL_RenderCopy(renderer, img.texture, ctypes.byref(src_rect),
                        ctypes.byref(dest_rect))


def draw_text(renderer: sdl2.render.SDL_Renderer,
              font: ctypes.c_void_p,
              text: str | bytes, x: int, y: int,
              color: Color, scale: int = 1) -> None:
    """Render multiline text to the screen using SDL TTF.

    Args:
        renderer: SDL renderer instance.
        font: Loaded TTF font pointer.
        text: String or bytes text to render.
        x: Starting X coordinate.
        y: Starting Y coordinate.
        color: Text color.
        scale: Integer font scaling factor.
    """
    if isinstance(text, bytes):
        text_bytes = text
    else:
        text_bytes = text.encode("utf-8")

    text_split: list[bytes] = text_bytes.split(b"\n")
    for i in range(len(text_split)):
        text_surface = sttf.TTF_RenderText_Solid(font,
                                                 text_split[i],
                                                 color_to_sdl_color(color))
        line_w = text_surface.contents.w
        line_h = text_surface.contents.h
        text_texture = sdl2.SDL_CreateTextureFromSurface(renderer,
                                                         text_surface)
        sdl2.SDL_FreeSurface(text_surface)
        dest_rect = sdl2.SDL_Rect(x, y + (line_h * i * scale),
                                  line_w * scale, line_h * scale)
        sdl2.SDL_RenderCopy(renderer, text_texture, None,
                            ctypes.byref(dest_rect))
        sdl2.SDL_DestroyTexture(text_texture)


def draw_line(pixels: ndarray, start_x: int, start_y: int,
              end_x: int, end_y: int, color: Color,
              thick: int) -> None:
    """Draw a Bresenham line segment onto a 2D numpy pixel buffer.

    Args:
        pixels: 2D numpy array representing screen pixels.
        start_x: Line start X coordinate.
        start_y: Line start Y coordinate.
        end_x: Line end X coordinate.
        end_y: Line end Y coordinate.
        color: Color of the line.
        thick: Unused thickness parameter.
    """
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


def draw_sin(pixels: ndarray, width: int, height: int, center: int, amp: int,
             frq: float, thickness: int, color: Color, frame: float) -> None:
    """Draw an opaque sine wave across the pixel buffer.

    Args:
        pixels: 2D numpy pixel array.
        width: Screen width.
        height: Screen height.
        center: Vertical center baseline.
        amp: Sine wave amplitude in pixels.
        frq: Frequency of the sine wave.
        thickness: Line thickness in pixels.
        color: ARGB color.
        frame: Phase offset for animation.
    """
    x_coords = arange(width)
    y_coords = center + amp * sin(x_coords * frq + frame)
    y_coords = y_coords.astype(int)
    offset = thickness // 2
    offsets = arange(-offset, offset + 1)[:, None]
    y_thick = clip(y_coords + offsets, 0, height - 1)
    pixels[y_thick, x_coords] = color


def draw_sin_a(pixels: ndarray, width: int, height: int, center: int, amp: int,
               frq: float, thickness: int, color: Color, frame: float) -> None:
    """Draw an alpha-blended animated sine wave across the pixel buffer.

    Args:
        pixels: 2D numpy pixel array.
        width: Screen width.
        height: Screen height.
        center: Vertical center baseline.
        amp: Sine wave amplitude in pixels.
        frq: Frequency of the sine wave.
        thickness: Line thickness in pixels.
        color: ARGB color with alpha component.
        frame: Phase offset for animation.
    """
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


class Button:
    def __init__(self, renderer: sdl2.render.SDL_Renderer,
                 pixels: ndarray, font: ctypes.c_void_p,
                 x: int, y: int, w: int,
                 h: int, color_rect: Color, color_hover: Color,
                 function: Callable[..., Any],
                 text: str | bytes, scale: int = 1) -> None:
        """Initialize an interactive UI button with label and click handler.

        Args:
            renderer: SDL renderer instance.
            pixels: 2D pixel array for rendering button background.
            font: TTF font pointer for rendering button text.
            x: X position of the button bounding box.
            y: Y position of the button bounding box.
            w: Width of the button.
            h: Height of the button.
            color_rect: Normal background color.
            color_hover: Hovered background color.
            function: Callback invoked when button is clicked.
            text: Button label text.
            scale: Text rendering scale factor.
        """
        self.renderer = renderer
        self.pixels = pixels
        self.font = font
        self.color_rect = color_rect
        self.color_hover = color_hover
        self.scale = scale
        self.action = function
        self.hold_boutton_state = False
        self.text = text
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def draw_background(self) -> None:
        """Render the button rectangle and trigger click action on press."""
        mouse_x, mouse_y = ctypes.c_int(0), ctypes.c_int(0)
        button_state = sdl2.mouse.SDL_GetMouseState(ctypes.byref(mouse_x),
                                                    ctypes.byref(mouse_y))
        if (mouse_x.value >= self.x and mouse_x.value <= self.x + self.w) and (
                mouse_y.value >= self.y and mouse_y.value <= self.y + self.h):
            draw_rect_full(self.pixels, self.w, self.h, self.color_hover,
                           self.x, self.y)
            if button_state == 1 and not self.hold_boutton_state:
                self.action()
                self.hold_boutton_state = True
            elif button_state == 0 and self.hold_boutton_state:
                self.hold_boutton_state = False
        else:
            draw_rect_full(self.pixels, self.w, self.h, self.color_rect,
                           self.x, self.y)
            if button_state == 0:
                self.hold_boutton_state = False

    def draw_text(self, color: Color) -> None:
        """Render centered label text on top of the button.

        Args:
            color: Text color to render.
        """
        if isinstance(self.text, bytes):
            text_bytes = self.text
        else:
            text_bytes = self.text.encode("utf-8")

        text_split: list[bytes] = text_bytes.split(b"\n")
        for i in range(len(text_split)):
            text_surface = sttf.TTF_RenderText_Solid(self.font, text_split[i],
                                                     color_to_sdl_color(color))
            line_w = text_surface.contents.w
            line_h = text_surface.contents.h
            center_y: int = int(self.y + (self.h // 2) - (line_h // 2))
            center_x: int = int(self.x + (self.w // 2) - (line_w // 2))
            text_texture = sdl2.SDL_CreateTextureFromSurface(self.renderer,
                                                             text_surface)
            sdl2.SDL_FreeSurface(text_surface)
            dest_rect = sdl2.SDL_Rect(center_x,
                                      center_y + (line_h * i * self.scale),
                                      line_w * self.scale, line_h * self.scale)
            sdl2.SDL_RenderCopy(self.renderer, text_texture, None,
                                ctypes.byref(dest_rect))
            sdl2.SDL_DestroyTexture(text_texture)
