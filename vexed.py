from __future__ import annotations
from dataclasses import dataclass
from collections import Counter, defaultdict
from math import inf


class Walls:
    def __init__(self, walls: tuple[tuple[bool]]):
        self.walls = walls
        self.width = len(self.walls[0])
        self.height = len(self.walls)
        self.empty_columns: list[EmptyColumn] = []
        for col in range(self.width):
            empty_col_row_start: int = None
            for row in range(self.height + 1):
                is_wall = self.is_wall(row, col)
                if is_wall == (empty_col_row_start is None):
                    continue
                if is_wall:
                    self.empty_columns.append(
                        EmptyColumn(col, empty_col_row_start, row)
                    )
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
        for bs in blocks_by_color.values():
            blocks_to_merge_indices = set()
            if len(bs) == 1:
                new_blocks.append(bs[0])
                continue
            for i in range(len(bs) - 1):
                for j in range(i + 1, len(bs)):
                    if bs[i].distance_with(bs[j]) == 1:
                        was_settled = False
                        blocks_to_merge_indices.add(i)
                        blocks_to_merge_indices.add(j)
            for i, block in enumerate(bs):
                if i in blocks_to_merge_indices:
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
            color_count = len(bs)
            if color_count == 1:
                return inf
            if 2 == color_count:
                h_dist = abs(bs[0].col - bs[1].col)
                h += max(0, h_dist - 1)
            if color_count == 3:
                x_coords = [b.col for b in bs]
                h_dist = max(x_coords) - min(x_coords)
                h += max(0, h_dist - 2)
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


class EmptyColumn:
    def __init__(self, col: int, row_start: int, row_end: int):
        self.col = col
        self.row_start = row_start
        self.row_end = row_end
        assert self.row_end > self.row_start
        self.length = self.row_end - self.row_start

    def fall(self, blocks: list[Block]) -> tuple[bool, list[Block]]:
        if self.length == 1 or len(blocks) == 0:
            return True, blocks
        arr = sorted((block.row, block.color) for block in blocks)
        new_blocks = [
            Block(el[1], self.length + i - len(blocks) + self.row_start, self.col)
            for i, el in enumerate(arr)
        ]

        was_settled = arr[0][0] == new_blocks[0].row
        return was_settled, new_blocks

    def corresponding_blocks(self, blocks: list[Block]) -> list[Block]:
        return [
            block
            for block in blocks
            if block.col == self.col and self.row_start <= block.row < self.row_end
        ]

    @staticmethod
    def columns_fall(
        columns: list[EmptyColumn], blocks: list[Block]
    ) -> tuple[bool, list[Block]]:
        bs = []
        fall_settled = True
        for empty_col in columns:
            col_blocks = empty_col.corresponding_blocks(blocks)
            col_fall_settled, col_new_blocks = empty_col.fall(col_blocks)
            fall_settled = col_fall_settled and fall_settled
            bs.extend(col_new_blocks)
        return fall_settled, bs


@dataclass(frozen=True)
class Move:
    row: int
    col: int
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


@dataclass(frozen=True)
class Level:
    walls: Walls
    blocks: frozenset[Block]

    # def __post_init__(self):
    #     print(self)

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
        new_blocks = []
        for block in self.blocks:
            if (block.row, block.col) == move.original_position():
                new_blocks.append(Block(block.color, *move.new_position()))
            else:
                new_blocks.append(block)

        merge_settled = False
        while not merge_settled:
            fall_settled = True
            fall_settled, bs = EmptyColumn.columns_fall(
                self.walls.empty_columns, new_blocks
            )

            if fall_settled and merge_settled:
                break

            merge_settled, bs = Block.merge(bs)
            new_blocks = bs.copy()

        return Level(self.walls, frozenset(new_blocks))

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
                moves.append(Move(block.row, block.col, True))
            if _right_vacant(block.row, block.col):
                moves.append(Move(block.row, block.col, False))
        return moves

    def children(self) -> dict[Level]:
        if self.is_deadend():
            return {}
        return {move: self._move(move) for move in self.possible_moves()}

    def is_win(self):
        return len(self.blocks) == 0

    def is_deadend(self):
        """
        early escape, return true if detected to be impossible
        returing False does not mean that the level is possible
        """
        # check singleton
        if any(v == 1 for v in Counter(b.color for b in self.blocks).values()):
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
        )
