# Pac-Man-Global-Offensive

## Function use

This document lists **all MiniLibX (MLX / MLX42) functions** and their exact equivalents in **SDL2** (both C/C++ and PySDL2 in Python), including the required extension libraries that must be installed.

---

### 1. Required Libraries & Package Installation

To replicate all MiniLibX functionality (window management, loading XPM/PNG images, font/text rendering, audio), standard core **SDL2** alone is not sufficient. You must install **SDL2 extension libraries**.

#### 🐧 Linux (Debian / Ubuntu)
```bash
# SDL2 Core + Extensions (Images, TTF Fonts, Audio, Graphic Primitives)
sudo apt update
sudo apt install -y libsdl2-dev libsdl2-image-dev libsdl2-ttf-dev libsdl2-mixer-dev libsdl2-gfx-dev
```

#### 🍏 macOS (Homebrew)
```bash
brew install sdl2 sdl2_image sdl2_ttf sdl2_mixer sdl2_gfx
```

#### 🐍 Python (uv / pip)
```bash
# Python dependencies (PySDL2 and native binaries)
uv add PySDL2 pysdl2-dll
# Or via pip:
# pip install PySDL2 pysdl2-dll
```

---

### 2. Complete Equivalence Table: MLX vs SDL2

| Category | MiniLibX Function (MLX / MLX42) | SDL2 Equivalent (C/C++) | PySDL2 Equivalent (Python) | Required Extension |
| :--- | :--- | :--- | :--- | :--- |
| **Initialization** | `mlx_init()` | `SDL_Init(SDL_INIT_VIDEO)` | `sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO)` | SDL2 Core |
| **Cleanup** | `mlx_destroy_display(mlx)` | `SDL_Quit()` | `sdl2.SDL_Quit()` | SDL2 Core |
| **Create Window** | `mlx_new_window(mlx, w, h, title)` | `SDL_CreateWindow(title, x, y, w, h, flags)` | `sdl2.SDL_CreateWindow(...)` | SDL2 Core |
| **Destroy Window**| `mlx_destroy_window(mlx, win)` | `SDL_DestroyWindow(win)` | `sdl2.SDL_DestroyWindow(win)` | SDL2 Core |
| **Clear Window** | `mlx_clear_window(mlx, win)` | `SDL_RenderClear(renderer)` | `sdl2.SDL_RenderClear(renderer)` | SDL2 Core |
| **Screen Size** | `mlx_get_screen_size(mlx, &w, &h)` | `SDL_GetDisplayBounds(0, &rect)` | `sdl2.SDL_GetDisplayBounds(0, rect)` | SDL2 Core |
| **Draw Pixel** | `mlx_pixel_put(mlx, win, x, y, color)` | `SDL_SetRenderDrawColor()` + `SDL_RenderDrawPoint()` | `sdl2.SDL_SetRenderDrawColor()` + `sdl2.SDL_RenderDrawPoint()` | SDL2 Core |
| **Sync / Refresh**| `mlx_do_sync(mlx)` | `SDL_RenderPresent(renderer)` | `sdl2.SDL_RenderPresent(renderer)` | SDL2 Core |
| **Create Image** | `mlx_new_image(mlx, w, h)` | `SDL_CreateRGBSurface()` or `SDL_CreateTexture()` | `sdl2.SDL_CreateRGBSurface()` / `sdl2.SDL_CreateTexture()` | SDL2 Core |
| **Image Buffer** | `mlx_get_data_addr(img, &bpp, &size, &endian)` | Direct access `surface->pixels` or `SDL_LockTexture()` | `surface.contents.pixels` | SDL2 Core |
| **Put Image** | `mlx_put_image_to_window(mlx, win, img, x, y)` | `SDL_UpdateTexture()` + `SDL_RenderCopy()` + `SDL_RenderPresent()` | `sdl2.SDL_UpdateTexture()` + `sdl2.SDL_RenderCopy()` | SDL2 Core |
| **Destroy Image** | `mlx_destroy_image(mlx, img)` | `SDL_FreeSurface(surf)` / `SDL_DestroyTexture(tex)` | `sdl2.SDL_FreeSurface(surf)` / `sdl2.SDL_DestroyTexture(tex)` | SDL2 Core |
| **Load XPM** | `mlx_xpm_file_to_image(mlx, file, &w, &h)` | `IMG_Load(file)` | `sdl2.sdlimage.IMG_Load(file)` | **SDL2_image** |
| **XPM Memory** | `mlx_xpm_to_image(mlx, xpm_data, &w, &h)` | `IMG_ReadXPMMem(xpm_data)` | `sdl2.sdlimage.IMG_ReadXPMMem(...)` | **SDL2_image** |
| **Load PNG** | `mlx_png_file_to_image(mlx, file, &w, &h)` / `mlx_load_png` | `IMG_Load(file)` | `sdl2.sdlimage.IMG_Load(file)` | **SDL2_image** |
| **Draw String** | `mlx_string_put(mlx, win, x, y, color, str)` | `TTF_OpenFont()` + `TTF_RenderText_Solid()` + `SDL_CreateTextureFromSurface()` + `SDL_RenderCopy()` | `sdl2.sdlttf.TTF_OpenFont()` + `TTF_RenderText_Solid()` | **SDL2_ttf** |
| **Game Loop** | `mlx_loop(mlx)` | `while (running) { while (SDL_PollEvent(&e)) { ... } }` | `while running: sdl2.SDL_PollEvent(...)` | SDL2 Core |
| **Frame Hook** | `mlx_loop_hook(mlx, func, param)` | Executed inside the main `while (running)` loop body | Placed inside the main `while` loop body | SDL2 Core |
| **Key Hook** | `mlx_key_hook(win, func, param)` | `event.type == SDL_KEYDOWN` / `SDL_KEYUP` | `event.type == sdl2.SDL_KEYDOWN` | SDL2 Core |
| **Mouse Hook** | `mlx_mouse_hook(win, func, param)` | `event.type == SDL_MOUSEBUTTONDOWN` / `UP` | `event.type == sdl2.SDL_MOUSEBUTTONDOWN` | SDL2 Core |
| **Generic Hook** | `mlx_hook(win, x_event, mask, func, param)` | `switch (event.type)` (`SDL_QUIT`, `SDL_KEYDOWN`, etc.) | `if event.type == sdl2.SDL_QUIT:` | SDL2 Core |
| **Hide Mouse** | `mlx_mouse_hide(mlx, win)` | `SDL_ShowCursor(SDL_DISABLE)` | `sdl2.SDL_ShowCursor(sdl2.SDL_DISABLE)` | SDL2 Core |
| **Show Mouse** | `mlx_mouse_show(mlx, win)` | `SDL_ShowCursor(SDL_ENABLE)` | `sdl2.SDL_ShowCursor(sdl2.SDL_ENABLE)` | SDL2 Core |
| **Move Mouse** | `mlx_mouse_move(mlx, win, x, y)` | `SDL_WarpMouseInWindow(win, x, y)` | `sdl2.SDL_WarpMouseInWindow(win, x, y)` | SDL2 Core |
| **Get Mouse Pos**| `mlx_mouse_get_pos(mlx, win, &x, &y)` | `SDL_GetMouseState(&x, &y)` | `sdl2.SDL_GetMouseState(x, y)` | SDL2 Core |
| **Disable Repeat**| `mlx_do_key_autorepeatoff(mlx)` | `event.key.repeat == 0` (Manual state tracking) | `event.key.repeat == 0` | SDL2 Core |
| **Enable Repeat** | `mlx_do_key_autorepeaton(mlx)` | Default SDL2 key repeat behavior | Default behavior | SDL2 Core |
| **Audio / Sound**| *(Not available in standard MLX)* | `Mix_OpenAudio()` + `Mix_LoadWAV()` + `Mix_PlayChannel()` | `sdl2.sdlmixer.Mix_OpenAudio(...)` | **SDL2_mixer** |

---
