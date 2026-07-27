def print_error(text: str) -> None:
    print(f"\033[31m[ERROR] {text}\033[0m")

def print_info(text: str) -> None:
    print(f"\033[34m[INFO] {text}\033[0m")

def print_warning(text: str) -> None:
    print(f"\033[33m[WARNING] {text}\033[0m")
