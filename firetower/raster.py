"""Reading and writing rasters with GDAL."""
from dataclasses import dataclass

import numpy as np
from osgeo import gdal

gdal.UseExceptions()


@dataclass
class Grid:
    """A single-band raster: the GDAL dataset plus its array."""

    dataset: gdal.Dataset
    array: np.ndarray
    nodata: float | None

    @property
    def band(self) -> gdal.Band:
        return self.dataset.GetRasterBand(1)

    @property
    def geotransform(self) -> tuple:
        return self.dataset.GetGeoTransform()

    @property
    def shape(self) -> tuple[int, int]:
        return self.array.shape

    def valid(self) -> np.ndarray:
        """Cells that hold data."""
        if self.nodata is None:
            return np.isfinite(self.array)
        return np.isfinite(self.array) & (self.array != self.nodata)

    def cell_center(self, col: int, row: int) -> tuple[float, float]:
        gt = self.geotransform
        return gt[0] + (col + 0.5) * gt[1] + (row + 0.5) * gt[2], \
            gt[3] + (col + 0.5) * gt[4] + (row + 0.5) * gt[5]


def open_grid(path: str) -> Grid:
    ds = gdal.Open(path)
    band = ds.GetRasterBand(1)
    return Grid(ds, band.ReadAsArray().astype(np.float64), band.GetNoDataValue())


def grid_from_array(array: np.ndarray, geotransform: tuple, projection_wkt: str = "",
                    nodata: float | None = None) -> Grid:
    """In-memory grid, used by the tests and for derived rasters."""
    rows, cols = array.shape
    ds = gdal.GetDriverByName("MEM").Create("", cols, rows, 1, gdal.GDT_Float32)
    ds.SetGeoTransform(geotransform)
    if projection_wkt:
        ds.SetProjection(projection_wkt)
    band = ds.GetRasterBand(1)
    if nodata is not None:
        band.SetNoDataValue(nodata)
    band.WriteArray(array.astype(np.float32))
    return Grid(ds, array.astype(np.float64), nodata)


def check_same_grid(a: Grid, b: Grid, what: str) -> None:
    """Refuse rasters that do not line up instead of silently resampling them."""
    if a.shape != b.shape or not np.allclose(a.geotransform, b.geotransform):
        raise ValueError(
            f"{what} does not match the DEM grid (size {b.shape} vs {a.shape}, "
            f"geotransform {b.geotransform} vs {a.geotransform}). "
            "Align it first, e.g. gdalwarp -tr <res> <res> -te <xmin ymin xmax ymax> -r near.")


def write_like(reference: Grid, array: np.ndarray, path: str,
               data_type: int = gdal.GDT_Int16, nodata: float | None = None) -> None:
    rows, cols = array.shape
    ds = gdal.GetDriverByName("GTiff").Create(path, cols, rows, 1, data_type, ["COMPRESS=DEFLATE"])
    ds.SetGeoTransform(reference.geotransform)
    ds.SetProjection(reference.dataset.GetProjection())
    band = ds.GetRasterBand(1)
    if nodata is not None:
        band.SetNoDataValue(nodata)
    band.WriteArray(array)
    ds = None
