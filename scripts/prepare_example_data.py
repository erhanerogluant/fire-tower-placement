"""Downloads an example area: a 1088 x 1088 cell (30 m) forested sheet near Mugla, Turkey.

Writes data/dem.tif (elevation) and data/forest.tif (1 = tree cover).
Only the needed window is read from the cloud-optimised GeoTIFFs (about 10 MB).

Sources:
- Copernicus DEM GLO-30, (c) DLR e.V. 2010-2014 and (c) Airbus Defence and Space GmbH 2014-2018,
  provided under COPERNICUS by the European Union and ESA.
- ESA WorldCover 10 m 2021 v200 (CC BY 4.0), class 10 = tree cover.
"""
import os

import numpy as np
from osgeo import gdal

gdal.UseExceptions()
gdal.SetConfigOption("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")

DEM_URL = ("/vsicurl/https://copernicus-dem-30m.s3.amazonaws.com/"
           "Copernicus_DSM_COG_10_N37_00_E028_00_DEM/Copernicus_DSM_COG_10_N37_00_E028_00_DEM.tif")
WORLDCOVER_URL = ("/vsicurl/https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/"
                  "ESA_WorldCover_10m_2021_v200_N36E027_Map.tif")
TREE_COVER = 10

SRS = "EPSG:32635"                  # UTM zone 35N
X_MIN, Y_MIN = 625000, 4105000      # lower-left corner (m)
SIZE, RES = 1088, 30
BOUNDS = (X_MIN, Y_MIN, X_MIN + SIZE * RES, Y_MIN + SIZE * RES)


def main(out_dir: str = "data") -> None:
    os.makedirs(out_dir, exist_ok=True)
    dem_path = os.path.join(out_dir, "dem.tif")
    gdal.Warp(dem_path, DEM_URL, dstSRS=SRS, outputBounds=BOUNDS, xRes=RES, yRes=RES,
              resampleAlg="bilinear", outputType=gdal.GDT_Float32, creationOptions=["COMPRESS=DEFLATE"])
    landcover = gdal.Warp("", WORLDCOVER_URL, format="MEM", dstSRS=SRS, outputBounds=BOUNDS,
                          xRes=RES, yRes=RES, resampleAlg="mode", outputType=gdal.GDT_Byte)
    forest = (landcover.ReadAsArray() == TREE_COVER).astype(np.uint8)

    ref = gdal.Open(dem_path)
    ds = gdal.GetDriverByName("GTiff").Create(os.path.join(out_dir, "forest.tif"), SIZE, SIZE, 1,
                                              gdal.GDT_Byte, ["COMPRESS=DEFLATE"])
    ds.SetGeoTransform(ref.GetGeoTransform())
    ds.SetProjection(ref.GetProjection())
    ds.GetRasterBand(1).WriteArray(forest)
    ds = None

    dem = ref.ReadAsArray()
    print(f"{dem_path}: {dem.shape}, elevation {dem.min():.0f}-{dem.max():.0f} m; "
          f"forest {forest.mean():.1%} of the area")


if __name__ == "__main__":
    main()
