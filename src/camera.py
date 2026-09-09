class Camera:
    """Represent camera viewport coordinates."""

    def __init__(self) -> None:
        """Initialize camera offsets to origin."""
        self.offset_x: int = 0
        self.offset_y: int = 0
