import unittest

import numpy as np

from firetower.params import PlacementParams
from firetower.placement import choose_towers, pack


def packed_sets(sets: list[set[int]], n: int) -> np.ndarray:
    target = np.ones(n, dtype=bool)
    rows = []
    for s in sets:
        mask = np.zeros(n, dtype=bool)
        mask[list(s)] = True
        rows.append(pack(mask, target))
    return np.array(rows)


class ChooseTowersTest(unittest.TestCase):
    def test_covers_everything_with_two_disjoint_halves(self):
        vis = packed_sets([{0, 1, 2, 3, 4}, {5, 6, 7, 8, 9}, {3, 4, 5, 6}], 10)
        p = choose_towers(vis, 10, PlacementParams(goal=1.0))
        self.assertEqual(sorted(p.chosen), [0, 1])
        self.assertEqual(p.coverage, 1.0)

    def test_stops_at_goal(self):
        vis = packed_sets([{0, 1, 2, 3, 4}, {5, 6, 7, 8, 9}], 10)
        p = choose_towers(vis, 10, PlacementParams(goal=0.5))
        self.assertEqual(len(p.chosen), 1)
        self.assertEqual(p.coverage, 0.5)

    def test_respects_max_towers(self):
        vis = packed_sets([{0, 1}, {2, 3}, {4, 5}], 6)
        p = choose_towers(vis, 6, PlacementParams(goal=1.0, max_towers=2))
        self.assertEqual(len(p.chosen), 2)

    def test_prunes_tower_made_redundant_by_later_choices(self):
        # greedy takes the largest set first, then the two halves make it redundant
        vis = packed_sets([{1, 2, 3, 4}, {0, 1, 2}, {3, 4, 5}], 6)
        p = choose_towers(vis, 6, PlacementParams(goal=1.0))
        self.assertEqual(sorted(p.chosen), [1, 2])
        self.assertEqual(p.coverage, 1.0)

    def test_reports_cells_no_candidate_can_see(self):
        vis = packed_sets([{0, 1, 2, 3, 4}], 10)
        p = choose_towers(vis, 10, PlacementParams(goal=1.0))
        self.assertEqual(p.chosen, [0])
        self.assertEqual(p.reachable, 0.5)
        self.assertEqual(p.coverage, 0.5)

    def test_no_candidates(self):
        p = choose_towers(np.empty((0, 2), dtype=np.uint8), 10, PlacementParams())
        self.assertEqual(p.chosen, [])
        self.assertEqual(p.coverage, 0.0)


if __name__ == "__main__":
    unittest.main()
