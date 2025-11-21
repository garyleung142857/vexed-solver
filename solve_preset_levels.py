import csv
import os
from solve import VexedSolver
from vexed import Level


level_folder = "levels"
solution_folder = "solutions"

level_fn = "classic_ii_levels.txt"

level_file = os.path.join(level_folder, level_fn)
solution_fn = level_fn.split(".")[0] + ".csv"
solution_file = os.path.join(solution_folder, solution_fn)
with (
    open(level_file, "r", encoding="latin-1") as f_level,
    open(solution_file, "w", encoding="latin-1") as f_sol,
):
    solution_writer = csv.writer(f_sol)
    for line in f_level.readlines():
        name, level_str, target_moves = line.split(";")
        target_moves = int(target_moves)
        level = Level.from_str(level_str)
        print(level, "\n")
        solver = VexedSolver(level)
        solution = solver.astar(level, target_moves)
        if solution is None:
            solution_writer.writerow(
                [
                    name,
                    target_moves,
                    -1,
                    "No solution",
                ]
            )
            continue
        solution_writer.writerow(
            [
                name,
                target_moves,
                len(solution),
                "|".join(str(move) for move in solution),
            ]
        )
        f_sol.flush()
