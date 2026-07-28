from src.window import Window
from src.print_logs import print_error
from src.parsing import check_config_file
import sys

def main() -> None:
    if len(sys.argv) > 2 or len(sys.argv) < 2:
        print_error("with the number of args given")
        return
    if check_config_file(sys.argv) is False:
        print_error("Config file invalid")
        return
    window = Window()
    window.main_loop()


if __name__ == "__main__":
    main()
