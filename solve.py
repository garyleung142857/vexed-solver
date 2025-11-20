from math import inf
from typing import Dict, Union, TypeVar, Generic
from math import inf as infinity
import sortedcontainers  # type: ignore

from vexed import Level

# introduce generic type
T = TypeVar("T")


################################################################################
class SearchNode(Generic[T]):
    """Representation of a search node"""

    __slots__ = ("data", "hash", "gscore", "fscore", "came_from", "in_openset")

    def __init__(
        self, data: T, gscore: float = infinity, fscore: float = infinity
    ) -> None:
        self.data = data
        self.hash = hash(data)
        self.gscore = gscore
        self.fscore = fscore
        self.in_openset = False
        self.came_from: Union[None, int] = None

    def __lt__(self, b: "SearchNode[T]") -> bool:
        """Natural order is based on the fscore value & is used by heapq operations"""
        return self.fscore < b.fscore


################################################################################
SNType = TypeVar("SNType", bound=SearchNode)


class OpenSet(Generic[SNType]):
    def __init__(self) -> None:
        self.sortedlist = sortedcontainers.SortedList(key=lambda x: x.fscore)

    def push(self, item: SNType) -> None:
        item.in_openset = True
        self.sortedlist.add(item)

    def pop(self) -> SNType:
        item = self.sortedlist.pop(0)
        item.in_openset = False
        return item

    def remove(self, item: SNType) -> None:
        self.sortedlist.remove(item)
        item.in_openset = False

    def __len__(self) -> int:
        return len(self.sortedlist)


class VexedSolver:
    maximal_cost: float = None

    def __init__(self, level: Level):
        self.level: Level = level

    def astar(self, start: Level, maximal_cost: float = inf):
        if maximal_cost is not None and maximal_cost != inf:
            self.maximal_cost = maximal_cost
        if start.is_win():
            return [start]

        openSet: OpenSet[SearchNode[Level]] = OpenSet()
        searchNodes: Dict[int, SearchNode[T]] = dict()
        startNode = searchNodes[start] = SearchNode(
            start, gscore=0.0, fscore=start.heuristics
        )
        openSet.push(startNode)

        previous_f_score = 0
        while openSet:
            current = openSet.pop()

            if current.data.is_win():
                print(len(searchNodes), "\n")
                result = []
                while current.came_from is not None:
                    result.append(current.hash)
                    for sn in searchNodes.values():
                        if sn.hash == current.came_from:
                            current = sn
                            break

                moves = []
                level: Level = start
                while result:
                    h = result.pop()
                    for move, child in level.children().items():
                        if hash(child) == h:
                            moves.append(move)
                            level = child
                            break
                return moves

            if (
                self.maximal_cost is not None
                and current.data.heuristics > self.maximal_cost
            ):
                del current.data
                del current.came_from
                continue

            for n in current.data.children().values():
                h = hash(n)
                if h not in searchNodes:
                    neighbor = SearchNode(n)
                    searchNodes[h] = neighbor
                    if current.fscore > previous_f_score:
                        previous_f_score = current.fscore
                        closed_nodes = tuple(
                            sn.gscore
                            for sn in searchNodes.values()
                            if not hasattr(sn, "data")
                        )
                        print(
                            len(searchNodes),
                            len(closed_nodes),
                            (
                                f"{sum(closed_nodes) / len(closed_nodes):.02f}"
                                if len(closed_nodes) > 0
                                else 0
                            ),
                            current.fscore,
                        )
                else:
                    neighbor = searchNodes[h]
                    if not hasattr(neighbor, "data"):
                        continue

                tentative_gscore = current.gscore + 1

                if tentative_gscore >= neighbor.gscore:
                    continue

                if neighbor.in_openset:
                    openSet.remove(neighbor)

                # update the node
                neighbor.came_from = current.hash
                neighbor.gscore = tentative_gscore
                neighbor.fscore = tentative_gscore + neighbor.data.heuristics

                openSet.push(neighbor)
            del current.data
        print(len(searchNodes), "\n")
        return None


if __name__ == "__main__":
    # level_str = ".hf...e./.eab..fh/.XXX..XX/.Xc....X/..b.a.c."
    # level_str = "b.XXXXa.aX/X.Xb..c.dX/X.XX..e.eX/Xb.ed.c.cg/XXXXe.X.ge/XXXXc.X.XX"
    level_str = "XXXX.gXX/XXXh.XXX/a.eg.e../X.XXXh.a"
    level = Level.from_str(level_str)
    print(level)
    level_solver = VexedSolver(level)
    solution = level_solver.astar(level, 20)
    print(solution)
