"""Candidate tower sites: local summits plus a regular grid."""
import numpy as np
from scipy.ndimage import maximum_filter


def candidate_sites(dem: np.ndarray, valid: np.ndarray, summit_window: int = 15,
                    grid_step: int = 36) -> list[tuple[int, int]]:
    """(col, row) sites, summits first, without duplicates.

    Summits see far; the grid makes sure every part of the sheet has candidates, so the
    placement never depends on the terrain having a convenient peak.
    """
    filled = np.where(valid, dem, -np.inf)
    summits = (filled == maximum_filter(filled, size=summit_window)) & valid
    sites = [(int(c), int(r)) for r, c in np.argwhere(summits)]
    rows, cols = dem.shape
    if grid_step > 0:
        sites += [(c, r) for r in range(grid_step // 2, rows, grid_step)
                  for c in range(grid_step // 2, cols, grid_step) if valid[r, c]]
    return list(dict.fromkeys(sites))
