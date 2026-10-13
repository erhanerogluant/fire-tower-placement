"""Command line: python -m firetower --dem DEM.tif [--mask forest.tif ...] --out results"""
import argparse
import sys

from .mask import load_target_mask
from .output import write_outputs
from .params import PlacementParams, ViewshedParams
from .pipeline import place_towers
from .raster import open_grid


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="firetower", description=__doc__)
    ap.add_argument("--dem", required=True, help="elevation raster (projected CRS, metres)")
    ap.add_argument("--mask", help="target area raster on the same grid (default: whole DEM)")
    ap.add_argument("--mask-values", type=float, nargs="+",
                    help="mask cell values that are target (default: any non-zero value)")
    ap.add_argument("--green-color", action="store_true",
                    help="mask is an RGB colour map; green areas are the target")
    ap.add_argument("--tower-height", type=float, default=20.0)
    ap.add_argument("--target-height", type=float, default=0.0,
                    help="height above ground that must be visible, e.g. 10 for smoke (default 0)")
    ap.add_argument("--max-distance", type=float, default=15000.0)
    ap.add_argument("--goal", type=float, default=0.90, help="share of the target to see (0-1)")
    ap.add_argument("--max-towers", type=int)
    ap.add_argument("--grid-step", type=int, default=36, help="candidate grid spacing in cells")
    ap.add_argument("--summit-window", type=int, default=15, help="summit search window in cells")
    ap.add_argument("--out", default="results")
    args = ap.parse_args(argv)

    dem = open_grid(args.dem)
    if abs(dem.geotransform[1]) < 0.01:
        print("The DEM looks geographic (degrees). Reproject it to a metric CRS first.", file=sys.stderr)
        return 2
    target = load_target_mask(dem, args.mask, args.mask_values, args.green_color)
    if not target.any():
        print("The target mask is empty.", file=sys.stderr)
        return 2

    view = ViewshedParams(args.tower_height, args.target_height, args.max_distance)
    place = PlacementParams(args.goal, args.max_towers)
    result = place_towers(dem, target, view, place, summit_window=args.summit_window,
                          grid_step=args.grid_step, progress=print)
    summary = write_outputs(args.out, dem, target, result, view, place)
    print(f"{summary['towers']} towers see {summary['coverage']:.1%} of the target area "
          f"(at most {summary['reachable_from_any_candidate']:.1%} is visible from any candidate). "
          f"Results in {args.out}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
