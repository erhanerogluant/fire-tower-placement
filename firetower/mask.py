"""Target area (e.g. forest) masks."""
import numpy as np
from osgeo import gdal

from .raster import Grid, check_same_grid


def mask_from_classes(grid: Grid, values: list[float]) -> np.ndarray:
    """Cells whose value is one of `values` (e.g. land-cover class 10 = tree cover)."""
    return np.isin(grid.array, values)


def mask_from_green_color(rgb: np.ndarray, margin: int = 20) -> np.ndarray:
    """Green areas of a scanned or exported colour map (JPEG/TIFF), rgb shaped (3, rows, cols).

    A cell counts as green when its green channel exceeds both red and blue by `margin`.
    Check the result on the map: legends, text and hatching in green are picked up too.
    """
    r, g, b = (rgb[i].astype(np.int32) for i in range(3))
    return (g - r > margin) & (g - b > margin)


def load_target_mask(dem: Grid, path: str | None, values: list[float] | None,
                     green_color: bool) -> np.ndarray:
    """Target cells on the DEM grid. Without a mask file the whole valid DEM is the target."""
    if path is None:
        return dem.valid()
    ds = gdal.Open(path)
    band = ds.GetRasterBand(1)
    grid = Grid(ds, band.ReadAsArray().astype(np.float64), band.GetNoDataValue())
    check_same_grid(dem, grid, f"Mask {path}")
    if green_color:
        if ds.RasterCount < 3:
            raise ValueError(f"{path} has {ds.RasterCount} band(s); a colour map needs RGB.")
        mask = mask_from_green_color(ds.ReadAsArray()[:3])
    elif values:
        mask = mask_from_classes(grid, values)
    else:
        mask = grid.array != 0
    return mask & dem.valid()
