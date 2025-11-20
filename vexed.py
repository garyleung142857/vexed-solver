from __future__ import annotations
from copy import deepcopy
from dataclasses import dataclass
from collections import defaultdict
from functools import lru_cache
from math import inf


class Walls:
    __slots__ = ("walls", "width", "height", "empty_columns")

    def __init__(self, walls: tuple[tuple[bool]]):
        self.walls = walls
        self.width = len(self.walls[0])
        self.height = len(self.walls)
        _empty_columns: list[tuple[int, int, int]] = []
        for col in range(self.width):
            empty_col_row_start: int = None
            for row in range(self.height + 1):
                is_wall = self.is_wall(row, col)
                if is_wall == (empty_col_row_start is None):
                    continue
                if is_wall:
                    if row - empty_col_row_start > 1:
                        _empty_columns.append((col, empty_col_row_start, row))
                    empty_col_row_start = None
                else:
                    empty_col_row_start = row
        self.empty_columns = nested_list_to_nested_tuple(_empty_columns)

    def __hash__(self):
        return hash(self.walls)

    def is_wall(self, row: int, col: int):
        if row >= self.height:
            return True
        if col < 0 or col >= self.width:
            return True
        return self.walls[row][col]

    @staticmethod
    def from_str(s: str, wall_char: str = "X", new_line_char: str = "/") -> Walls:
        rows = []
        for row in s.split(new_line_char):
            rows.append(tuple(char == wall_char for char in row))
        return Walls(walls=tuple(rows))


@dataclass(frozen=True)
class Move:
    row: int
    col: int
    color: int
    to_left: bool

    def __str__(self):
        if self.to_left:
            return f"{self.row}{self.col}<"
        return f"{self.row}{self.col}>"

    def __repr__(self):
        return str(self)

    def original_position(self) -> tuple[int]:
        return (self.row, self.col)

    def new_position(self) -> tuple[int]:
        if self.to_left:
            d_col = -1
        else:
            d_col = 1

        return (self.row, self.col + d_col)


@lru_cache
def color_heuristics(x_coords: tuple[int]):
    if len(x_coords) == 2:
        return max(x_coords[1] - x_coords[0] - 1, 0)
    dists = tuple(
        max(x_coords[i + 1] - x_coords[i] - 1, 0) for i in range(len(x_coords) - 1)
    )
    h = dists[0] + dists[-1]
    for dist, next_dist in zip(dists[:-1], dists[1:]):
        h += min(dist, next_dist)
    return h


def nested_tuple_to_nested_list(tuple_repr: tuple[tuple[int]]) -> list[list[int]]:
    return [list(inner) for inner in tuple_repr]


def nested_list_to_nested_tuple(list_repr: list[list[int]]) -> tuple[tuple[int]]:
    return tuple(tuple(inner) for inner in list_repr)


class Level:
    __slots__ = ("walls", "list_repr", "tuple_repr", "heuristics")

    def __init__(self, walls: Walls, tuple_repr: tuple[tuple[int]]):
        self.walls = walls
        self.tuple_repr = tuple_repr
        self.heuristics: int = self._heuristics()

    def __repr__(self):
        row_lists = [[] for _ in range(self.walls.height)]
        for col in self.tuple_repr:
            for i, cell in enumerate(col):
                if cell == -1:
                    row_lists[i].append("#")
                elif cell == 0:
                    row_lists[i].append(" ")
                else:
                    row_lists[i].append(chr(cell + 96))

        return "\n".join("".join(row_list) for row_list in row_lists)

    def _move(self, move: Move, list_repr: list[list[int]]) -> Level:
        merge_settled = False
        list_repr[move.col][move.row] = 0
        list_repr[move.new_position()[1]][move.new_position()[0]] = move.color
        while not merge_settled:
            fall_settled = True
            for x, row_start, row_end in self.walls.empty_columns:
                for i in range(row_start, row_end - 1):
                    for j in range(row_end - 2, i - 1, -1):
                        if list_repr[x][j] == 0 or list_repr[x][j + 1] != 0:
                            continue
                        list_repr[x][j + 1] = list_repr[x][j]
                        list_repr[x][j] = 0
                        fall_settled = False

            if fall_settled and merge_settled:
                break

            to_be_merged: set[tuple[int, int]] = set()

            for x in range(self.walls.width):
                for y in range(self.walls.height):
                    if list_repr[x][y] <= 0:
                        continue
                    if (
                        y < self.walls.height - 1
                        and list_repr[x][y] == list_repr[x][y + 1]
                    ):
                        to_be_merged.add((x, y))
                        to_be_merged.add((x, y + 1))
                    if (
                        x < self.walls.width - 1
                        and list_repr[x][y] == list_repr[x + 1][y]
                    ):
                        to_be_merged.add((x, y))
                        to_be_merged.add((x + 1, y))

            merge_settled = len(to_be_merged) == 0
            for x, y in to_be_merged:
                list_repr[x][y] = 0

        return Level(self.walls, nested_list_to_nested_tuple(list_repr))

    def move(self, move: Move) -> Level:
        assert self.tuple_repr[move.col][move.row] == move.color
        assert self.tuple_repr[move.new_position()[1]][move.new_position()[0]] == 0
        list_repr = nested_tuple_to_nested_list(self.tuple_repr)
        return self._move(move, list_repr)

    def possible_moves(self) -> list[Move]:
        moves: list[Move] = []
        for x, col in enumerate(self.tuple_repr[:-1]):
            for y, cell in enumerate(col):
                right_cell = self.tuple_repr[x + 1][y]
                if cell == 0 and right_cell >= 0:
                    moves.append(Move(y, x + 1, right_cell, True))
                elif right_cell == 0 and cell >= 0:
                    moves.append(Move(y, x, cell, False))
        return moves

    def children(self) -> dict[Move, Level]:
        list_repr = nested_tuple_to_nested_list(self.tuple_repr)
        return {
            move: self._move(move, deepcopy(list_repr))
            for move in self.possible_moves()
        }

    def _heuristics(self) -> int:
        blocks_by_color = defaultdict(list[tuple[int, int]])
        for x, col in enumerate(self.tuple_repr):
            for y, cell in enumerate(col):
                if cell <= 0:
                    continue
                blocks_by_color[cell].append((x, y))

        if len(blocks_by_color) == 0:
            return 0
        h = 0
        for bs in blocks_by_color.values():
            n_blocks = len(bs)
            if n_blocks == 1:
                return inf
            if n_blocks <= 3:
                x_coords = [b[0] for b in bs if b[1] == self.walls.height - 1]
                if len(x_coords) >= 2 and any(
                    self.walls.walls[-1][x_coords[0] + 1 : x_coords[-1]]
                ):
                    return inf
            h += color_heuristics(tuple(b[0] for b in bs))
        return max(h, 1)

    def is_win(self):
        return self.heuristics == 0

    def __hash__(self):
        return hash(self.tuple_repr)

    def __eq__(self, value: Level):
        return hash(self) == hash(value)

    @staticmethod
    def from_str(
        s: str, wall_char: str = "X", empty_char: str = ".", new_line_char="/"
    ) -> Level:
        walls = Walls.from_str(s, wall_char, new_line_char)
        assigned_chars = []
        cols = [[None for _ in range(walls.height)] for _ in range(walls.width)]
        for i, row in enumerate(s.split(new_line_char)):
            for j, char in enumerate(row):
                if char == wall_char:
                    cols[j][i] = -1
                    continue
                elif char == empty_char:
                    cols[j][i] = 0
                    continue
                if char not in assigned_chars:
                    assigned_chars.append(char)
                cols[j][i] = assigned_chars.index(char) + 1

        return Level(walls, nested_list_to_nested_tuple(cols))
