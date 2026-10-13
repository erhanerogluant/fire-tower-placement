"""Choosing the fewest towers: greedy set cover on packed visibility masks.

Minimum set cover is NP-hard; the greedy choice (always the tower that adds the most unseen
target cells) is the standard approximation and is within a factor ln(n) of the optimum.
A pruning pass then drops towers that later choices made redundant.
"""
from dataclasses import dataclass

import numpy as np

from .params import PlacementParams


def pack(mask: np.ndarray, target: np.ndarray) -> np.ndarray:
    """The target cells of a visibility mask, packed 8 per byte."""
    return np.packbits(mask[target])


def count(packed: np.ndarray) -> int:
    return int(np.bitwise_count(packed).sum())


@dataclass
class Placement:
    chosen: list[int]            # indices into the candidate list, in order of choice
    gains: list[int]             # target cells each chosen tower added when it was chosen
    covered_cells: int
    target_cells: int
    reachable_cells: int         # target cells visible from at least one candidate

    @property
    def coverage(self) -> float:
        return self.covered_cells / self.target_cells if self.target_cells else 1.0

    @property
    def reachable(self) -> float:
        return self.reachable_cells / self.target_cells if self.target_cells else 1.0


def choose_towers(visibility: np.ndarray, target_cells: int, params: PlacementParams) -> Placement:
    """visibility: (n_candidates, n_bytes) packed masks over the target cells."""
    if visibility.shape[0] == 0:
        return Placement([], [], 0, target_cells, 0)
    reachable = count(np.bitwise_or.reduce(visibility, axis=0))
    goal_cells = params.goal * target_cells
    min_gain = max(1, int(params.min_gain * target_cells))

    covered = np.zeros(visibility.shape[1], dtype=np.uint8)
    chosen: list[int] = []
    gains: list[int] = []
    while count(covered) < goal_cells:
        if params.max_towers is not None and len(chosen) >= params.max_towers:
            break
        new = np.bitwise_count(visibility & ~covered).sum(axis=1)
        best = int(np.argmax(new))
        if new[best] < min_gain:
            break
        chosen.append(best)
        gains.append(int(new[best]))
        covered |= visibility[best]

    covered_cells = count(covered)
    chosen, gains = _prune(visibility, chosen, gains, min(covered_cells, goal_cells))
    final = count(np.bitwise_or.reduce(visibility[chosen], axis=0)) if chosen else 0
    return Placement(chosen, gains, final, target_cells, reachable)


def _prune(visibility: np.ndarray, chosen: list[int], gains: list[int],
           required: float) -> tuple[list[int], list[int]]:
    """Remove towers, smallest gain first, while the rest still reach the required coverage."""
    keep = list(zip(chosen, gains))
    for item in sorted(keep, key=lambda t: t[1]):
        rest = [i for i, _ in keep if i != item[0]]
        if rest and count(np.bitwise_or.reduce(visibility[rest], axis=0)) >= required:
            keep.remove(item)
    return [i for i, _ in keep], [g for _, g in keep]
