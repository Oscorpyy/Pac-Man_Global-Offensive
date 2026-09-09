def print_error(text: str) -> None:
    """Print an error message formatted in red text.

    Args:
        text: Error message to display.
    """
    print(f"\033[31m[ERROR] {text}\033[0m")


def print_info(text: str) -> None:
    """Print an informational message formatted in blue text.

    Args:
        text: Info message to display.
    """
    print(f"\033[34m[INFO] {text}\033[0m")


def print_warning(text: str) -> None:
    """Print a warning message formatted in yellow text.

    Args:
        text: Warning message to display.
    """
    print(f"\033[33m[WARNING] {text}\033[0m")
