"""Line-of-sight visibility from one tower, using GDAL's viewshed algorithm."""
import numpy as np
from osgeo import gdal

from .params import ViewshedParams
from .raster import Grid


def visible_cells(dem: Grid, col: int, row: int, params: ViewshedParams) -> np.ndarray:
    """Boolean array (same shape as the DEM): cells whose target height is visible from the tower."""
    x, y = dem.cell_center(col, row)
    result = gdal.ViewshedGenerate(
        dem.band, "MEM", "", [], x, y,
        params.tower_height, params.target_height,
        1, 0, 0, 0,                       # visible, invisible, out-of-range, nodata values
        params.curvature_coeff, gdal.GVM_Edge, params.max_distance)

    # GDAL returns only the window within max_distance; place it on the full grid.
    full = np.zeros(dem.shape, dtype=bool)
    gt, vgt = dem.geotransform, result.GetGeoTransform()
    c0 = int(round((vgt[0] - gt[0]) / gt[1]))
    r0 = int(round((vgt[3] - gt[3]) / gt[5]))
    part = result.GetRasterBand(1).ReadAsArray().astype(bool)
    rows, cols = dem.shape
    rs, cs = max(r0, 0), max(c0, 0)
    re, ce = min(r0 + part.shape[0], rows), min(c0 + part.shape[1], cols)
    full[rs:re, cs:ce] = part[rs - r0:re - r0, cs - c0:ce - c0]
    return full & dem.valid()
