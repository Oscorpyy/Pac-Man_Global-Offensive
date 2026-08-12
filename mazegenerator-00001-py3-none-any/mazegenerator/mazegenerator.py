import random
from collections import deque
from typing import Iterator


class MazeGenerator:

    def __init__(self, size: tuple[int, int] = (15, 15), perfect: bool = False,
                 entry_cell: tuple[int, int] = (0, 0),
                 exit_cell: tuple[int, int] = (-1, -1),
                 seed: int = 0) -> None:
        self._width = size[0]
        self._height = size[1]
        self._perfect = perfect
        self._seed = seed
        self._entryx = (entry_cell[0]
                        if 0 <= entry_cell[0] < self._width else 0)
        self._entryy = (entry_cell[1]
                        if 0 <= entry_cell[1] < self._height else 0)
        self._exitx = (exit_cell[0]
                       if 0 <= exit_cell[0] < self._width else self._width-1)
        self._exity = (exit_cell[1]
                       if 0 <= exit_cell[1] < self._height else self._height-1)
        self._maze: list[list[int]] = []
        self._path: list[list[int]] = []
        self._shortest_path: str | bool = False
        self.generate(self._seed)
        return None

    @property
    def maze(self) -> list[list[int]]:
        return self._maze

    @property
    def shortest_path(self) -> str | bool:
        return self._shortest_path

    @property
    def maze_entry(self) -> tuple[int, int]:
        return self._entryx, self._entryy

    @property
    def maze_exit(self) -> tuple[int, int]:
        return self._exitx, self._exity

    def generate(self, seed: int = 0) -> None:
        random.seed(seed) if seed > 0 else random.seed()
        self._seed = seed
        self._create_empty_maze()
        self._add_42_to_maze()
        self._generate_maze(self._entryx, self._entryy, 0)
        self._find_short_path()

#    Private functions

    def _create_empty_maze(self) -> None:
        self._maze = [[8] + [0] * (self._width-2) +
                      [2] for _ in range(self._height-2)]
        self._maze.insert(0, [9] + [1] * (self._width-2) + [3])
        self._maze.append([12] + [4] * (self._width-2) + [6])
        self._path = [[0] * self._width for _ in range(self._height)]

    def _add_42_to_maze(self) -> None:
        ft_small = [[1, 0, 0, 0, 1, 1, 1],
                    [1, 0, 0, 0, 0, 0, 1],
                    [1, 1, 1, 0, 1, 1, 1],
                    [0, 0, 1, 0, 1, 0, 0],
                    [0, 0, 1, 0, 1, 1, 1]
                    ]
        if len(ft_small)*2 > self._height or len(ft_small[0])*2 > self._width:
            print("MazeGenerator Warning: maze is too small to add '42' in it")
            return
        posy = int((self._height - len(ft_small)) / 2)
        posx = int((self._width - len(ft_small[0])) / 2)
        for y in range(len(ft_small)):
            for x in range(len(ft_small[0])):
                if ft_small[y][x] == 1:
                    self._maze[posy+y][posx+x] = 15
                    self._maze[posy+y][posx+x-1] |= 2
                    self._maze[posy+y][posx+x+1] |= 8
                    self._maze[posy+y-1][posx+x] |= 4
                    self._maze[posy+y+1][posx+x] |= 1
                    self._path[posy+y][posx+x] = 1

    def _is_available(self, x: int, y: int) -> bool:
        if (
                0 <= y < self._height and
                0 <= x < self._width and self._path[y][x] == 0
        ):
            return True
        return False

    def _get_neighbors(self, x: int,
                       y: int) -> Iterator[tuple[int, int, int, int]]:
        directions = [(1, 0, 2, 8), (-1, 0, 8, 2), (0, 1, 4, 1), (0, -1, 1, 4)]
        random.shuffle(directions)
        for dw, dh, code, opp_code in directions:
            nx, ny = x + dw, y + dh
            if self._is_available(nx, ny):
                yield nx, ny, code, opp_code
            else:
                if (
                        self._perfect is False and random.randint(0, 5) == 0
                        and 0 <= ny < self._height and 0 <= nx < self._width
                ):
                    if (
                            self._maze[ny][nx] != 15 and
                            (self._maze[y][x] & (~code)) != 0 and
                            (self._maze[ny][nx] & (~opp_code)) != 0
                    ):
                        self._maze[y][x] = self._maze[y][x] & (~code)
                        self._maze[ny][nx] = self._maze[ny][nx] & (~opp_code)

    def _generate_maze(self, x: int, y: int, from_code: int) -> None:
        self._path[y][x] = 1
        non_mutable = self._maze[y][x]
        self._maze[y][x] = 15 & ~from_code
        for nx, ny, code, opp_code in self._get_neighbors(x, y):
            if code & non_mutable:
                continue
            self._maze[y][x] = self._maze[y][x] & (~code)
            self._generate_maze(nx, ny, opp_code)

    def _find_short_path(self) -> None:
        directions = [(0, 1, 4, 'S'), (1, 0, 2, 'E'),
                      (-1, 0, 8, 'W'), (0, -1, 1, 'N')]
        if (self._entryx, self._entryy) == (self._exitx, self._exity):
            self._shortest_path = ''
            return
        visited = [[False] * self._width for _ in range(self._height)]
        visited[self._entryy][self._entryx] = True
        queue: deque[tuple[int, int, str]] = deque(
            [(self._entryx, self._entryy, '')])
        while queue:
            x, y, ways = queue.popleft()
            for dx, dy, code, way in directions:
                if (self._maze[y][x] & code) != 0:
                    continue
                nx, ny = x + dx, y + dy
                if not (0 <= nx < self._width and 0 <= ny < self._height):
                    continue
                if visited[ny][nx]:
                    continue
                if (nx, ny) == (self._exitx, self._exity):
                    self._shortest_path = ways + way
                    return
                visited[ny][nx] = True
                queue.append((nx, ny, ways + way))
        print("MazeGenerator Class error: no shortest path found.")
        return
