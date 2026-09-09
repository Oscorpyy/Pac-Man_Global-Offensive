import sdl2
import sdl2.sdlimage as sdim
import ctypes
import json
import re
import sdl2.sdlttf as sttf

from typing import Any
from src.color import Color
from src.drawing_methods import draw_sprites_fullscreen, draw_text
from src.game_state import GameState, ScenePossible
from src.image import Image


class EndScreen:
    def __init__(self, renderer: sdl2.render.SDL_Renderer,
                 game_state: GameState, width: int,
                 height: int, image_path: str, highscore_filename: str,
                 quit_callback: Any) -> None:
        """Initialize the end game screen (win/loss) with UI elements.

        Args:
            renderer: SDL renderer instance.
            game_state: Global game state.
            width: Screen width in pixels.
            height: Screen height in pixels.
            image_path: Path to background outcome image.
            highscore_filename: Path to high score JSON file.
            quit_callback: Callback function invoked when quitting to menu.
        """
        self.renderer = renderer
        self.game_state = game_state
        self.width = width
        self.height = height
        self.highscore_filename = highscore_filename
        self.quit_callback = quit_callback
        self.image = Image(image_path, renderer)
        self.font = sttf.TTF_OpenFont(
            b"assets/Press_Start_2P/PressStart2P-Regular.ttf", 16)
        self.save_popup_open = False
        self.save_name = ""
        self.save_error = ""
        self.max_save_name_length = 10
        self.ignore_next_text_input = False

    @staticmethod
    def is_valid_save_name(save_name: str) -> bool:
        """Check whether candidate player name contains valid characters.

        Args:
            save_name: Player name string.

        Returns:
            True if name contains only alphanumeric and space characters.
        """
        return bool(re.fullmatch(r"[A-Za-z0-9 ]+", save_name))

    def save_and_quit(self, save_name: str, on_success: Any = None) -> bool:
        """Save the current score and run the navigation callback."""
        if not self.is_valid_save_name(save_name):
            self.save_error = "INVALID NAME"
            return False
        try:
            with open(self.highscore_filename, "r") as score_file:
                score_data = json.load(score_file)
            scores = score_data.get("scores", [])
            scores.append({
                "name": save_name,
                "point": self.game_state.get_points(),
            })
            with open(self.highscore_filename, "w") as score_file:
                json.dump({"scores": scores}, score_file, indent=4)
        except (OSError, TypeError, ValueError):
            self.save_error = "SCORE NOT SAVED"
            return False
        if on_success is None:
            on_success = self.quit_callback
        on_success()
        return True

    def _get_buttons(self) -> list[dict]:
        """Compute layout rectangles and metadata for main end buttons.

        Returns:
            List of dictionaries containing button properties.
        """
        button_w = min(700, self.width - 120)
        button_x = (self.width - button_w) // 2
        button_y = self.height // 2 + 170
        return [
            {"id": "save", "label": "SAVE AND QUIT", "x": button_x,
             "y": button_y, "w": button_w, "h": 48},
            {"id": "quit", "label": "QUIT TO MENU", "x": button_x,
             "y": button_y + 64, "w": button_w, "h": 48},
        ]

    def _select(self, button_id: str) -> None:
        """Trigger action associated with selected button ID.

        Args:
            button_id: Identifier of button clicked ('save' or 'quit').
        """
        if button_id == "save":
            self.save_popup_open = True
            self.save_name = ""
            self.save_error = ""
            self.ignore_next_text_input = False
            sdl2.SDL_StartTextInput()
        else:
            self.quit_callback()

    def _get_popup_buttons(self) -> list[dict]:
        """Compute layout rectangles for save popup confirm/cancel buttons.

        Returns:
            List of dictionaries containing popup button specifications.
        """
        popup_w = min(700, self.width - 120)
        popup_x = (self.width - popup_w) // 2
        popup_y = (self.height - 280) // 2
        button_w = popup_w - 48
        return [
            {"id": "confirm", "label": "CONFIRM SAVE", "x": popup_x + 24,
             "y": popup_y + 170, "w": button_w, "h": 42},
            {"id": "cancel", "label": "CANCEL", "x": popup_x + 24,
             "y": popup_y + 222, "w": button_w, "h": 42},
        ]

    def _close_popup(self) -> None:
        """Close the save score popup and stop SDL text input mode."""
        self.save_popup_open = False
        self.save_error = ""
        sdl2.SDL_StopTextInput()

    def _confirm_save(self) -> None:
        """Validate input name and persist score to highscores file."""
        save_name = self.save_name
        if not save_name:
            self.save_error = "NAME REQUIRED"
            return
        if self.save_and_quit(save_name):
            self._close_popup()

    def _append_name(self, text: str) -> None:
        """Append filtered characters to the active save name buffer.

        Args:
            text: Raw character text entered by player.
        """
        available = self.max_save_name_length - len(self.save_name)
        valid_text = "".join(
            char for char in text
            if re.fullmatch(r"[A-Za-z0-9 ]", char)
        )
        invalid_count = len(text) - len(valid_text)
        if invalid_count > 0:
            self.save_error = "INVALID CHARACTER"
        if available <= 0:
            self.save_error = f"NAME TOO LONG ({
                        self.max_save_name_length} MAX)"
            return
        if len(valid_text) > available:
            self.save_error = f"NAME TOO LONG ({
                        self.max_save_name_length} MAX)"
        elif invalid_count == 0:
            self.save_error = ""
        self.save_name += valid_text[:available]

    def _handle_popup_click(self, mouse_x: int, mouse_y: int) -> None:
        """Process mouse clicks inside the save popup dialog.

        Args:
            mouse_x: Click horizontal coordinate.
            mouse_y: Click vertical coordinate.
        """
        for button in self._get_popup_buttons():
            if (button["x"] <= mouse_x <= button["x"] + button["w"]
                    and button["y"] <= mouse_y
                    <= button["y"] + button["h"]):
                if button["id"] == "confirm":
                    self._confirm_save()
                else:
                    self._close_popup()
                return

    def handle_event(self, event: sdl2.events.SDL_Event) -> None:
        """Handle keyboard and mouse events on the end game screen.

        Args:
            event: Incoming SDL event to process.
        """
        if self.game_state.scene not in (ScenePossible.WIN,
                                         ScenePossible.LOOSE):
            return
        if self.save_popup_open:
            if event.type == sdl2.SDL_TEXTINPUT:
                if self.ignore_next_text_input:
                    self.ignore_next_text_input = False
                    return
                if event.text.text:
                    text_bytes = bytes(event.text.text).split(b"\0", 1)[0]
                    text = text_bytes.decode("utf-8", errors="ignore")
                    self._append_name(text)
                return
            if event.type == sdl2.SDL_KEYDOWN:
                key = event.key.keysym.sym
                if key == sdl2.SDLK_BACKSPACE:
                    self.save_name = self.save_name[:-1]
                elif key in (sdl2.SDLK_RETURN, sdl2.SDLK_KP_ENTER):
                    self._confirm_save()
                elif key == sdl2.SDLK_ESCAPE:
                    self._close_popup()
                elif sdl2.SDLK_a <= key <= sdl2.SDLK_z:
                    self._append_name(chr(key))
                    self.ignore_next_text_input = True
                elif sdl2.SDLK_0 <= key <= sdl2.SDLK_9:
                    self._append_name(chr(key))
                    self.ignore_next_text_input = True
                return
            if event.type == sdl2.SDL_MOUSEBUTTONDOWN:
                if event.button.button == sdl2.SDL_BUTTON_LEFT:
                    self._handle_popup_click(event.button.x, event.button.y)
                return
        if event.type == sdl2.SDL_KEYDOWN:
            key = event.key.keysym.sym
            if key in (sdl2.SDLK_1, sdl2.SDLK_RETURN):
                self._select("save")
            elif key in (sdl2.SDLK_2, sdl2.SDLK_ESCAPE):
                self._select("quit")
        elif event.type == sdl2.SDL_MOUSEBUTTONDOWN:
            if event.button.button != sdl2.SDL_BUTTON_LEFT:
                return
            mouse_x = event.button.x
            mouse_y = event.button.y
            for button in self._get_buttons():
                if (button["x"] <= mouse_x <= button["x"] + button["w"]
                        and button["y"] <= mouse_y
                        <= button["y"] + button["h"]):
                    self._select(button["id"])
                    return

    def draw(self) -> None:
        """Render the end screen background, score, and UI buttons."""
        draw_sprites_fullscreen(
            self.renderer, self.image, 0, 0, 1, self.width, self.height
        )
        score = f"SCORE: {self.game_state.get_points()}"
        score_w, score_h = ctypes.c_int(0), ctypes.c_int(0)
        sttf.TTF_SizeUTF8(self.font, score.encode(),
                          ctypes.byref(score_w), ctypes.byref(score_h))
        draw_text(self.renderer, self.font, score,
                  (self.width - score_w.value) // 2 - 70, 40,
                  Color.WHITE, 2)

        if self.save_popup_open:
            self._draw_save_popup()
            return

        for button in self._get_buttons():
            button_rect = sdl2.SDL_Rect(button["x"], button["y"],
                                        button["w"], button["h"])
            sdl2.SDL_SetRenderDrawColor(self.renderer, 20, 20, 30, 230)
            sdl2.SDL_RenderFillRect(self.renderer, ctypes.byref(button_rect))
            sdl2.SDL_SetRenderDrawColor(self.renderer, 255, 220, 0, 255)
            sdl2.SDL_RenderDrawRect(self.renderer, ctypes.byref(button_rect))
            label = button["label"]
            label_w, label_h = ctypes.c_int(0), ctypes.c_int(0)
            sttf.TTF_SizeUTF8(self.font, label.encode(),
                              ctypes.byref(label_w), ctypes.byref(label_h))
            draw_text(self.renderer, self.font, label,
                      button["x"] + (button["w"] - label_w.value) // 2,
                      button["y"] + (button["h"] - label_h.value) // 2,
                      Color.YELLOW, 1)

        hint = b"1 / ENTER: SAVE    2 / ESC: QUIT"
        hint_w, hint_h = ctypes.c_int(0), ctypes.c_int(0)
        sttf.TTF_SizeUTF8(self.font, hint, ctypes.byref(hint_w),
                          ctypes.byref(hint_h))
        draw_text(self.renderer, self.font, hint,
                  (self.width - hint_w.value) // 2, self.height - 70,
                  Color.WHITE, 1)

    def _draw_save_popup(self) -> None:
        """Render modal save score dialog with text field and buttons."""
        popup_w = min(700, self.width - 120)
        popup_h = 280
        popup_x = (self.width - popup_w) // 2
        popup_y = (self.height - popup_h) // 2
        popup_rect = sdl2.SDL_Rect(popup_x, popup_y, popup_w, popup_h)
        sdl2.SDL_SetRenderDrawBlendMode(
            self.renderer, sdl2.SDL_BLENDMODE_BLEND)
        sdl2.SDL_SetRenderDrawColor(self.renderer, 10, 10, 20, 245)
        sdl2.SDL_RenderFillRect(self.renderer, ctypes.byref(popup_rect))
        sdl2.SDL_SetRenderDrawColor(self.renderer, 255, 220, 0, 255)
        sdl2.SDL_RenderDrawRect(self.renderer, ctypes.byref(popup_rect))

        title = b"SAVE SCORE"
        title_w, title_h = ctypes.c_int(0), ctypes.c_int(0)
        sttf.TTF_SizeUTF8(self.font, title, ctypes.byref(title_w),
                          ctypes.byref(title_h))
        draw_text(self.renderer, self.font, title,
                  popup_x + (popup_w - title_w.value) // 2, popup_y + 18,
                  Color.YELLOW, 1)
        draw_text(self.renderer, self.font, b"PLAYER NAME",
                  popup_x + 24, popup_y + 55, Color.WHITE, 1)

        input_rect = sdl2.SDL_Rect(popup_x + 24, popup_y + 82,
                                   popup_w - 48, 36)
        sdl2.SDL_SetRenderDrawColor(self.renderer, 30, 30, 45, 255)
        sdl2.SDL_RenderFillRect(self.renderer, ctypes.byref(input_rect))
        sdl2.SDL_SetRenderDrawColor(self.renderer, 255, 220, 0, 255)
        sdl2.SDL_RenderDrawRect(self.renderer, ctypes.byref(input_rect))
        name_text = self.save_name.encode("ascii", errors="ignore")
        if not name_text:
            name_text = b"ENTER NAME"
        draw_text(self.renderer, self.font, name_text,
                  popup_x + 34, popup_y + 91,
                  Color.WHITE if self.save_name else Color.GRAY, 1)

        if self.save_error:
            draw_text(self.renderer, self.font, self.save_error,
                      popup_x + 24, popup_y + 128, Color.RED, 1)

        for button in self._get_popup_buttons():
            button_rect = sdl2.SDL_Rect(button["x"], button["y"],
                                        button["w"], button["h"])
            sdl2.SDL_SetRenderDrawColor(self.renderer, 20, 20, 30, 255)
            sdl2.SDL_RenderFillRect(self.renderer, ctypes.byref(button_rect))
            sdl2.SDL_SetRenderDrawColor(self.renderer, 255, 220, 0, 255)
            sdl2.SDL_RenderDrawRect(self.renderer, ctypes.byref(button_rect))
            label = button["label"]
            label_w, label_h = ctypes.c_int(0), ctypes.c_int(0)
            sttf.TTF_SizeUTF8(self.font, label.encode(),
                              ctypes.byref(label_w), ctypes.byref(label_h))
            draw_text(self.renderer, self.font, label,
                      button["x"] + (button["w"] - label_w.value) // 2,
                      button["y"] + (button["h"] - label_h.value) // 2,
                      Color.YELLOW, 1)

    def clean_up(self) -> None:
        """Free loaded textures, fonts, and clean up SDL subsystems."""
        sdl2.SDL_DestroyTexture(self.image.texture)
        sttf.TTF_CloseFont(self.font)
        sdim.IMG_Quit()
