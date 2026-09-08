class CameraProps:
    def __init__(self, current_frame: int = 0) -> None:
        self.current_frame: int = current_frame
        self.animation_speed: int = 9
        self.frame_number: int = 25
        self.tick_counter: int = 0

    def update(self) -> None:
        self.tick_counter += 1
        if self.tick_counter >= self.animation_speed:
            self.tick_counter = 0
            self.current_frame += 1
            self.current_frame = self.current_frame % self.frame_number

