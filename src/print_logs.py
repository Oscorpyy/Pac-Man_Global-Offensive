def print_error(text: str) -> None:
    print(f"\033[31m{text}\033[0m")

def print_info(text: str) -> None:
    print(f"\033[34m{text}\033[0m")

def print_warning(text: str) -> None:
    print(f"\033[33m{text}\033[0m")
