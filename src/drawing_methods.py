def put_pixels(pixels_array, x, y, width, height, color) -> None:
    if 0 <= x < width and 0 <= y < height:
        pixels_array[y * width + x] = color


def draw_rect_full(
        pixels,
        screen_width: int, screen_height: int,
        rect_width: int, rect_height: int,
        color,
        start_x: int = 0, start_y: int = 0
        ) -> None:
    for y in range(rect_height):
        for x in range(rect_width):
            put_pixels(pixels, x + start_x, y + start_y, screen_width, screen_height, color)
