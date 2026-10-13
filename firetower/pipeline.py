"""DEM + target mask -> chosen towers and the coverage they give."""
import time
from dataclasses import dataclass

import numpy as np

from .candidates import candidate_sites
from .params import PlacementParams, ViewshedParams
from .placement import Placement, choose_towers, pack
from .raster import Grid
from .viewshed import visible_cells


@dataclass
class Tower:
    col: int
    row: int
    x: float
    y: float
    elevation: float
    gain_cells: int


@dataclass
class Result:
    towers: list[Tower]
    placement: Placement
    seen_count: np.ndarray       # per cell: number of chosen towers that see it
    candidates: int
    seconds: float


def place_towers(dem: Grid, target: np.ndarray, view: ViewshedParams, place: PlacementParams,
                 sites: list[tuple[int, int]] | None = None, summit_window: int = 15,
                 grid_step: int = 36, progress=None) -> Result:
    start = time.time()
    if sites is None:
        sites = candidate_sites(dem.array, dem.valid(), summit_window, grid_step)
    target_cells = int(target.sum())
    packed = np.empty((len(sites), (target_cells + 7) // 8), dtype=np.uint8)
    for i, (col, row) in enumerate(sites):
        packed[i] = pack(visible_cells(dem, col, row, view), target)
        if progress and (i + 1) % 200 == 0:
            progress(f"viewsheds {i + 1}/{len(sites)}")

    placement = choose_towers(packed, target_cells, place)

    towers, seen = [], np.zeros(dem.shape, dtype=np.int16)
    for idx, gain in zip(placement.chosen, placement.gains):
        col, row = sites[idx]
        x, y = dem.cell_center(col, row)
        towers.append(Tower(col, row, x, y, float(dem.array[row, col]), gain))
        seen += visible_cells(dem, col, row, view)
    return Result(towers, placement, seen, len(sites), time.time() - start)
