from numpy import ndarray


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
