from astar import AStar
from vexed import Level, Move, Block
from math import inf


class VexedSolver(AStar):
    def __init__(self, level: Level):
        self.level: Level = level

    def heuristic_cost_estimate(self, current: Level, goal):
        if current.is_deadend():
            return inf
        return Block.heuristics(current.blocks)

    def distance_between(self, n1, n2):
        return 1

    def neighbors(self, node: Level):
        if node.is_deadend():
            return []
        return list(node.children().values())

    def is_goal_reached(self, current: Level, goal):
        return current.is_win()

    @staticmethod
    def nodes_to_moves(path: list[Level]):
        moves: list[Move] = []
        for i in range(len(path) - 1):
            cur_node = path[i]
            next_node = path[i + 1]
            for move, node in cur_node.children().items():
                if node == next_node:
                    moves.append(move)
                    break
        return moves

    def astar(self, start):
        path = super().astar(start, None)
        if path is None:
            return None
        return self.nodes_to_moves(list(path))


if __name__ == "__main__":
    # level_str = ".hf...e./.eab..fh/.XXX..XX/.Xc....X/..b.a.c."
    level_str = "..bac.X/.XXXX.a/...d..e/e..e..b/c.bc..g/bceXagd"
    level = Level.from_str(level_str)
    print(level)
    level_solver = VexedSolver(level)
    solution = level_solver.astar(level)
    print(solution)
