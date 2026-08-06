

class CsPlayer:
    def __init__(self) -> None:
        self.pos_x: int = 0
        self.pos_y: int = 0
        self.can_move: bool = True
        self.can_collide: bool = True
        self.can_shoot: bool = True


class PacPlayer:
    def __init__(self) -> None:
        pass
