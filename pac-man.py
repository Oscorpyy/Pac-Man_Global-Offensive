import sys
from src.window import Window
from src.print_logs import print_error
from src.parsing import check_config_file, load_json_file
from src.game_state import GameConfig


def main() -> None:
    """Validate configuration file and run the game main loop."""
    if check_config_file(sys.argv) is False:
        print_error("Config file invalid")
        return
    try:
        content = load_json_file(sys.argv[1])
    except Exception as e:
        print_error(f"Caught error: {e}")
        return
    config = GameConfig(content)
    window = Window(config)
    window.main_loop()


if __name__ == "__main__":
    main()
