"""Measures what the earlier script's towers really see, next to the viewshed-based placement.

The earlier script (written with ChatGPT) picked the highest cell of each 300 x 300 block
and called a local-maximum filter "visibility analysis"; it never computed line of sight.
Its selection logic is reproduced unchanged below.

    run.bat scripts/compare_legacy.py data/dem.tif data/forest.tif [target_height]
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from firetower.mask import load_target_mask  # noqa: E402
from firetower.params import PlacementParams, ViewshedParams  # noqa: E402
from firetower.pipeline import place_towers  # noqa: E402
from firetower.raster import open_grid  # noqa: E402
from firetower.viewshed import visible_cells  # noqa: E402


def legacy_select_best_tower_positions(elevation_map, num_towers=10, tower_height=20, grid_size=300):
    """Unchanged from the earlier script. Note: tower_height is compared with terrain elevation,
    and unravel_index assumes full 300 x 300 blocks, which misplaces towers in edge blocks."""
    height, width = elevation_map.shape
    best = []
    for y in range(0, height, grid_size):
        for x in range(0, width, grid_size):
            idx = np.unravel_index(np.argmax(elevation_map[y:y + grid_size, x:x + grid_size]),
                                   (grid_size, grid_size))
            pos = (x + idx[1], y + idx[0])
            if pos[0] < width and pos[1] < height:
                if elevation_map[pos[1], pos[0]] >= tower_height:
                    best.append(pos)
    best.sort(key=lambda p: elevation_map[p[1], p[0]], reverse=True)
    return best[:num_towers]


def main() -> None:
    dem_path, mask_path = sys.argv[1], sys.argv[2]
    target_height = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
    dem = open_grid(dem_path)
    target = load_target_mask(dem, mask_path, None, False)
    view = ViewshedParams(target_height=target_height)

    legacy = legacy_select_best_tower_positions(dem.array, num_towers=20)
    seen = np.zeros(dem.shape, dtype=bool)
    for col, row in legacy:
        seen |= visible_cells(dem, col, row, view)
    legacy_cov = (seen & target).sum() / target.sum()

    same_count = place_towers(dem, target, view, PlacementParams(goal=1.0, max_towers=len(legacy)))
    print(f"target height {target_height:g} m, tower 20 m, range 15 km")
    print(f"earlier script : {len(legacy)} towers (20 requested), target seen {legacy_cov:.1%}")
    print(f"viewshed-based : {len(same_count.towers)} towers, target seen "
          f"{same_count.placement.coverage:.1%}")
    for goal in (0.90, 0.95):
        r = place_towers(dem, target, view, PlacementParams(goal=goal))
        print(f"viewshed-based : {len(r.towers)} towers needed for {goal:.0%} "
              f"(reached {r.placement.coverage:.1%})")


if __name__ == "__main__":
    main()
