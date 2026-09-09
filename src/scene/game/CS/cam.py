class CameraProps:
    """Manage animation frames and properties for in-game security cameras."""

    def __init__(self, current_frame: int = 0) -> None:
        """Initialize camera animation frame counters.

        Args:
            current_frame: Starting animation frame index.
        """
        self.current_frame: int = current_frame
        self.animation_speed: int = 9
        self.frame_number: int = 25
        self.tick_counter: int = 0

    def update(self) -> None:
        """Advance camera animation frame when tick threshold is reached."""
        self.tick_counter += 1
        if self.tick_counter >= self.animation_speed:
            self.tick_counter = 0
            self.current_frame += 1
            self.current_frame = self.current_frame % self.frame_number
