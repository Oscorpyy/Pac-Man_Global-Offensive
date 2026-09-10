import math
import json
import sdl2
import sdl2.sdlimage as sdim
import sdl2.sdlttf as sttf
import numpy as np
from src.color import Color
from src.drawing_methods import (
    draw_fps,
    clear_background,
    draw_sin_a,
    draw_text,
    draw_sprites,
    Button,
)
from src.scene.helper import get_ptr
from src.print_logs import print_error
from src.game_state import GameConfig, GameState, ScenePossible
from src.scene.main_menu.settings import SettingsWindow
from src.scene.main_menu.instruction import InstructionWindow
from src.image import Image
from src.transition import Transition


class MenuDrawingState:
    def __init__(self) -> None:
        """Initialize menu sub-view state tracker."""
        self.state_lst: list[str] = ["main", "instruction", "settings"]
        self.current = self.state_lst[0]


class MainMenu:
    def __init__(self, renderer: sdl2.render.SDL_Renderer,
                 game_state: GameState,
                 game_config: GameConfig, transition: Transition) -> None:
        """Initialize the main menu scene, buttons, and sub-windows.

        Args:
            renderer: SDL renderer instance.
            game_state: Global game state object.
            game_config: Game configuration options.
            transition: Transition animation controller.
        """
        self.game_state = game_state
        self.menu_state = MenuDrawingState()
        self.game_config = game_config
        self.renderer = renderer
        self.top_score = self.get_highscore()
        self.scores: list[dict[str, int]] = self.top_score.get("scores", [])
        if self.scores is not None:
            self.scores.sort(key=lambda item: item['point'], reverse=True)
        sdim.IMG_Init(sdim.IMG_INIT_PNG)
        self.logo = Image(b"assets/game_logo.png", renderer)
        sttf.TTF_Init()
        self.font_size: int = 16
        self.font = sttf.TTF_OpenFont(
            b"assets/Press_Start_2P/PressStart2P-Regular.ttf", self.font_size)
        if not self.font:
            print_error(f"can't charge font {sttf.TTF_GetError()}")
        self.width: int = self.game_config.screen_width
        self.height: int = self.game_config.screen_height
        self.pixels = np.zeros((self.height, self.width), dtype=np.uint32)
        self.settings_win = SettingsWindow(
            self.width, self.height, renderer, self.pixels, self.font,
            on_close=self.set_can_draw_main
        )
        self.instruction_win = InstructionWindow(
            self.width, self.height, renderer, self.pixels, self.font,
            on_close=self.set_can_draw_main
        )
        self.transition = transition
        self.background = sdl2.SDL_CreateTexture(
            renderer,
            sdl2.SDL_PIXELFORMAT_ARGB8888,
            sdl2.SDL_TEXTUREACCESS_STREAMING,
            self.width,
            self.height
        )
        btn_width = 200
        self.btn_list: list[Button] = [
            Button(self.renderer, self.pixels,
                   self.font, (self.width // 2 - (btn_width // 2)),
                   self.height // 3, btn_width, 50, Color.GRAY, Color.WHITE,
                   self.next_scene, b"Start Game"),
            Button(self.renderer, self.pixels,
                   self.font, (self.width // 2 - (btn_width // 2)) - (
                    btn_width + 32), self.height // 3, btn_width, 50,
                   Color.GRAY, Color.WHITE, self.set_can_draw_settings,
                   b"Settings"),
            Button(self.renderer, self.pixels,
                   self.font, (self.width // 2 - (btn_width // 2)) + (
                    btn_width + 32), self.height // 3, btn_width, 50,
                   Color.GRAY, Color.WHITE, self.set_can_draw_instructions,
                   b"Instructions"),
            Button(self.renderer, self.pixels,
                   self.font, self.game_config.screen_width - 105,
                   5, 100, 50,
                   Color.WHITE, Color.RED,
                   self.close_game, b"Exit")
        ]
        self.pitch_background = self.width * 4
        self.time: float = 0.0
        self.background_color = 0xFF0000FF

    def get_highscore(self) -> dict[str, list[dict[str, int]]]:
        """Read and parse the high score JSON file.

        Returns:
            Dictionary containing score records.
        """
        content: dict[str, list[dict[str, int]]] = {}
        try:
            with open(self.game_config.highscore_filename, "r") as f:
                content = json.load(f)
        except (FileNotFoundError, PermissionError, ValueError) as e:
            print_error(f"Caught error: {e}")
        return content

    def refresh_scores(self) -> None:
        """Reload high scores from disk and sort them in descending order."""
        self.top_score = self.get_highscore()
        self.scores = self.top_score.get("scores", [])
        self.scores.sort(key=lambda item: item.get('point', 0), reverse=True)

    def clean_up(self) -> None:
        """Release allocated textures, fonts, and sub-window resources."""
        sdim.IMG_Quit()
        sttf.TTF_CloseFont(self.font)
        sttf.TTF_Quit()
        sdl2.SDL_DestroyTexture(self.logo.texture)
        sdl2.SDL_DestroyTexture(self.background)
        self.settings_win.clean_up()
        self.instruction_win.clean_up()

    def next_scene(self) -> None:
        """Trigger transition into the active gameplay scene."""
        self.transition.start_image_transition(ScenePossible.GAME)

    def draw_scores(self) -> None:
        """Render top high score entries onto the main menu screen."""
        scores = self.scores
        draw_text(self.renderer, self.font, b"HIGHSCORE",
                  self.width // 2 - (len("HIGHSCORE") * 16 // 2),
                  self.height // 2, Color.WHITE)
        y_offset: int = self.height // 2 + 30
        if scores is not None:
            if len(scores) == 0:
                draw_text(self.renderer, self.font, b"HIGHSCORE",
                          self.width // 2 - (len("HIGHSCORE") * 16 // 2),
                          self.height // 2, Color.WHITE)
            else:
                i = 0
                for stat in scores:
                    if i > 9:
                        continue
                    txt_str: str = f"{stat.get('name')}: {stat.get('point')}"
                    txt: bytes = txt_str.encode("utf-8")
                    draw_text(self.renderer, self.font, txt,
                              self.width // 2 - (len(txt) * 16 // 2),
                              y_offset, Color.WHITE)
                    y_offset += 30
                    i += 1

    def set_can_draw_main(self) -> None:
        """Set active menu state back to the primary main menu."""
        self.menu_state.current = self.menu_state.state_lst[0]
        if hasattr(self, 'instruction_win') and hasattr(
                self.instruction_win, 'reset'):
            self.instruction_win.reset()

    def handle_escape(self) -> bool:
        """Handle ESC key press to exit sub-menus back to main menu.

        Returns:
            True if a sub-menu was closed, False if already on main menu.
        """
        if self.menu_state.current != self.menu_state.state_lst[0]:
            self.set_can_draw_main()
            return True
        return False

    def handle_event(self, event: sdl2.events.SDL_Event) -> bool:
        """Dispatch SDL input event to active sub-menu window.

        Args:
            event: Incoming SDL event.

        Returns:
            True if the event was consumed by a sub-menu, False otherwise.
        """
        if self.menu_state.current == self.menu_state.state_lst[1]:
            if hasattr(self.instruction_win, 'handle_event'):
                return self.instruction_win.handle_event(event)
        return False

    def set_can_draw_settings(self) -> None:
        """Switch active menu view to settings window."""
        self.menu_state.current = self.menu_state.state_lst[2]

    def set_can_draw_instructions(self) -> None:
        """Switch active menu view to instructions window."""
        self.menu_state.current = self.menu_state.state_lst[1]

    def close_game(self) -> None:
        """Stop the main game loop and exit application."""
        self.game_state.is_running = False

    def draw_background(self) -> None:
        """Render animated rainbow background, logo, and menu buttons."""
        clear_background(self.pixels, self.get_rainbow_color(self.time * 0.2))
        draw_sin_a(self.pixels, self.width, self.height,
                   int(self.height * 0.5), 50, 0.01, 100,
                   Color.ST_WHITE, self.time)
        draw_sin_a(self.pixels, self.width, self.height,
                   int(self.height * 0.5), 50, -0.02, 60,
                   Color.ST_WHITE, self.time)
        for btn in self.btn_list:
            btn.draw_background()
        pixel_ptr = get_ptr(self.pixels)
        sdl2.SDL_UpdateTexture(self.background, None, pixel_ptr,
                               self.pitch_background)
        sdl2.SDL_RenderCopy(self.renderer, self.background, None, None)
        draw_sprites(self.renderer, self.logo, ((
            self.width // 2) - (self.logo.width * 5 // 2)), 0, 5)
        for btn in self.btn_list:
            btn.draw_text(Color.BLACK)
        self.draw_scores()

    def get_rainbow_color(self, time_var: float) -> int:
        """Compute cycling ARGB color based on sine oscillations.

        Args:
            time_var: Time parameter controlling color phase.

        Returns:
            32-bit ARGB color integer.
        """
        center = 100
        amp = 40
        r = int(center + amp * math.sin(time_var))
        g = int(center + amp * math.sin(time_var + 2))
        b = int(center + amp * math.sin(time_var + 4))
        return (0xFF << 24) | (r << 16) | (g << 8) | b

    def draw_main_menu(self) -> None:
        """Render current menu state, active sub-window, and FPS overlay."""
        if self.menu_state.current == self.menu_state.state_lst[2]:
            self.settings_win.draw_settings(
                self.time, self.get_rainbow_color(self.time * 0.2))
        elif self.menu_state.current == self.menu_state.state_lst[1]:
            self.instruction_win.draw_instructions(
                self.time, self.get_rainbow_color(self.time * 0.2))
        elif self.menu_state.current == self.menu_state.state_lst[0]:
            self.draw_background()
        draw_fps(self.renderer, self.font, self.game_state.fps)
        if self.game_state.scene != ScenePossible.MAIN:
            self.clean_up()
        self.time += 0.1
