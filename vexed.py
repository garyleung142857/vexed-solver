from __future__ import annotations
from copy import deepcopy
from dataclasses import dataclass
from collections import defaultdict
from math import inf


class Walls:
    def __init__(self, walls: tuple[tuple[bool]]):
        self.walls = walls
        self.width = len(self.walls[0])
        self.height = len(self.walls)
        self.empty_columns: list[tuple[int, int, int]] = []
        for col in range(self.width):
            empty_col_row_start: int = None
            for row in range(self.height + 1):
                is_wall = self.is_wall(row, col)
                if is_wall == (empty_col_row_start is None):
                    continue
                if is_wall:
                    if row - empty_col_row_start > 1:
                        self.empty_columns.append((col, empty_col_row_start, row))
                    empty_col_row_start = None
                else:
                    empty_col_row_start = row

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
class Block:
    color: int
    row: int
    col: int

    def distance_with(self, other: Block):
        return abs(self.row - other.row) + abs(self.col - other.col)

    @staticmethod
    def blocks_by_color(blocks: list[Block]) -> dict[int, list[Block]]:
        blocks_by_color = defaultdict(list[Block])
        for block in blocks:
            blocks_by_color[block.color].append(block)
        return blocks_by_color

    @staticmethod
    def merge(blocks: list[Block]) -> tuple[bool, list[Block]]:
        blocks_by_color = Block.blocks_by_color(blocks)

        was_settled = True
        new_blocks: list[Block] = []
        blocks_to_merge = set()
        for bs in blocks_by_color.values():
            if len(bs) == 1:
                new_blocks.append(bs[0])
                continue
            for i in range(len(bs) - 1):
                for j in range(i + 1, len(bs)):
                    if bs[i].distance_with(bs[j]) == 1:
                        was_settled = False
                        blocks_to_merge.add(bs[i])
                        blocks_to_merge.add(bs[j])
            for block in bs:
                if block in blocks_to_merge:
                    continue
                new_blocks.append(block)
        return was_settled, new_blocks

    @staticmethod
    def heuristics(blocks: list[Block]) -> int:
        """Not over-estimating estimate"""
        if len(blocks) == 0:
            return 0
        h = 1
        blocks_by_color = Block.blocks_by_color(blocks)
        for bs in blocks_by_color.values():
            x_coords = sorted(b.col for b in bs)
            color_heuristics = max(
                x_coords[i + 1] - x_coords[i] for i in range(len(bs) - 1)
            )
            if color_heuristics <= 1:
                continue
            h += color_heuristics - 1
        return h

    @staticmethod
    def from_str(
        s: str, wall_char: str = "X", empty_char: str = ".", new_line_char="/"
    ) -> frozenset[Block]:
        assigned_chars = []
        blocks = []
        for row, row_str in enumerate(s.split(new_line_char)):
            for col, char in enumerate(row_str):
                if char == wall_char or char == empty_char:
                    continue
                if char not in assigned_chars:
                    assigned_chars.append(char)
                color_index = assigned_chars.index(char) + 1
                blocks.append(Block(color_index, row, col))
        return frozenset(blocks)


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


class Level:
    walls: Walls
    blocks: frozenset[Block]

    def __init__(
        self, walls: Walls, blocks: frozenset[Block], list_repr: list[list[int]]
    ):
        self.walls = walls
        self.blocks = blocks
        if list_repr is None:
            self.list_repr = self.to_nested_list()
        else:
            self.list_repr = list_repr
        self.height = len(self.walls.walls)
        self.width = len(self.walls.walls[0])

    def to_nested_list(self) -> list[list[int]]:
        level = [
            [-1 if self.walls.walls[j][i] else 0 for j in range(len(self.walls.walls))]
            for i in range(len(self.walls.walls[0]))
        ]

        for block in self.blocks:
            level[block.col][block.row] = block.color

        return level

    def __repr__(self):
        row_lists = []
        for row in range(self.walls.height):
            row_list = []
            for col in range(self.walls.width):
                if self.walls.is_wall(row, col):
                    row_list.append("#")
                else:
                    row_list.append(" ")

            row_lists.append(row_list)
        for block in self.blocks:
            row_lists[block.row][block.col] = chr(block.color + 96)

        return "\n".join("".join(row_list) for row_list in row_lists)

    def _move(self, move: Move) -> Level:
        merge_settled = False
        list_repr = deepcopy(self.list_repr)
        list_repr[move.col][move.row] = 0
        list_repr[move.new_position()[1]][move.new_position()[0]] = move.color
        while not merge_settled:
            fall_settled = True
            for x, row_start, row_end in self.walls.empty_columns:
                for i in range(row_start, row_end - 1):
                    for j in range(row_end - 2, i - 1, -1):
                        if list_repr[x][j] <= 0:
                            continue
                        if list_repr[x][j + 1] != 0:
                            continue
                        list_repr[x][j + 1] = list_repr[x][j]
                        list_repr[x][j] = 0
                        fall_settled = False

            if fall_settled and merge_settled:
                break

            to_be_merged: set[tuple[int, int]] = set()

            for x in range(self.width):
                for y in range(self.height):
                    if list_repr[x][y] <= 0:
                        continue
                    if y < self.height - 1 and list_repr[x][y] == list_repr[x][y + 1]:
                        to_be_merged.add((x, y))
                        to_be_merged.add((x, y + 1))
                    if x < self.width - 1 and list_repr[x][y] == list_repr[x + 1][y]:
                        to_be_merged.add((x, y))
                        to_be_merged.add((x + 1, y))

            merge_settled = len(to_be_merged) == 0
            for x, y in to_be_merged:
                list_repr[x][y] = 0

        new_blocks: list[Block] = []
        for x, col in enumerate(list_repr):
            for y, color in enumerate(col):
                if color <= 0:
                    continue
                new_blocks.append(Block(color, y, x))

        return Level(self.walls, frozenset(new_blocks), list_repr)

    def move(self, move: Move) -> Level:
        assert any(
            (block.row, block.col) == move.original_position() for block in self.blocks
        )  # there is a block in the move location
        assert not self.walls.is_wall(*move.new_position())
        # not a wall in the new position
        assert not any(
            (block.row, block.col) == move.new_position() for block in self.blocks
        )  # not a block in the new position

        return self._move(move)

    def possible_moves(self) -> list[Move]:
        moves: list[Move] = []
        blocks_coords = tuple((block.row, block.col) for block in self.blocks)

        def _left_vacant(row, col):
            if (row, col - 1) in blocks_coords:
                return False
            return not self.walls.is_wall(row, col - 1)

        def _right_vacant(row, col):
            if (row, col + 1) in blocks_coords:
                return False
            return not self.walls.is_wall(row, col + 1)

        for block in self.blocks:
            if _left_vacant(block.row, block.col):
                moves.append(Move(block.row, block.col, block.color, True))
            if _right_vacant(block.row, block.col):
                moves.append(Move(block.row, block.col, block.color, False))
        return moves

    def children(self) -> dict[Level]:
        return {move: self._move(move) for move in self.possible_moves()}

    def is_win(self):
        return len(self.blocks) == 0

    def is_deadend(self):
        """
        early escape, return true if detected to be impossible
        returing False does not mean that the level is possible
        """

        for bs in Block.blocks_by_color(self.blocks).values():
            # check singleton
            if len(bs) == 1:
                return True
            if len(bs) <= 3:
                x_coords = [b.col for b in bs if b.row == len(self.walls.walls) - 1]
                if len(x_coords) < 2:
                    continue
                if any(self.walls.walls[-1][min(x_coords) + 1 : max(x_coords)]):
                    return True

        return False

    def __hash__(self):
        return hash(self.blocks)

    def __eq__(self, value: Level):
        return hash(self) == hash(value)

    @staticmethod
    def from_str(
        s: str, wall_char: str = "X", empty_char: str = ".", new_line_char="/"
    ) -> Level:
        return Level(
            walls=Walls.from_str(s, wall_char, new_line_char),
            blocks=Block.from_str(s, wall_char, empty_char, new_line_char),
            list_repr=None,
        )
