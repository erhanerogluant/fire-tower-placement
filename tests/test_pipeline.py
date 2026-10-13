import json
import os
import tempfile
import unittest

import numpy as np
from osgeo import gdal

from firetower.__main__ import main
from firetower.mask import mask_from_classes, mask_from_green_color
from firetower.params import PlacementParams, ViewshedParams
from firetower.pipeline import place_towers
from firetower.raster import grid_from_array

GT_30M = (500000.0, 30.0, 0.0, 4100000.0, 0.0, -30.0)


def cone(rows, cols, apex_row, apex_col, height=300.0, slope=0.3, res=30.0):
    r, c = np.mgrid[0:rows, 0:cols]
    dist = np.hypot(r - apex_row, c - apex_col) * res
    return np.clip(height - slope * dist, 0, None)


class PipelineTest(unittest.TestCase):
    def test_one_tower_on_the_apex_sees_the_whole_cone(self):
        z = cone(61, 61, 30, 30)
        dem = grid_from_array(z, GT_30M)
        target = z > 0
        result = place_towers(dem, target, ViewshedParams(), PlacementParams(goal=1.0), grid_step=10)
        self.assertEqual(len(result.towers), 1)
        self.assertEqual((result.towers[0].col, result.towers[0].row), (30, 30))
        self.assertEqual(result.placement.coverage, 1.0)

    def test_two_far_cones_need_two_towers_when_range_is_short(self):
        z = np.maximum(cone(61, 141, 30, 30), cone(61, 141, 30, 110))
        dem = grid_from_array(z, GT_30M)
        target = z > 0
        view = ViewshedParams(max_distance=1500)
        result = place_towers(dem, target, view, PlacementParams(goal=1.0), grid_step=10)
        self.assertEqual(sorted((t.col, t.row) for t in result.towers), [(30, 30), (110, 30)])
        self.assertEqual(result.placement.coverage, 1.0)


class MaskTest(unittest.TestCase):
    def test_green_color(self):
        rgb = np.zeros((3, 1, 4), dtype=np.uint8)
        rgb[:, 0, 0] = (40, 160, 60)     # forest green
        rgb[:, 0, 1] = (200, 200, 200)   # grey
        rgb[:, 0, 2] = (60, 70, 200)     # blue water
        rgb[:, 0, 3] = (120, 130, 125)   # almost grey, below the margin
        self.assertEqual(mask_from_green_color(rgb).tolist(), [[True, False, False, False]])

    def test_classes(self):
        grid = grid_from_array(np.array([[10, 20], [30, 10]]), GT_30M)
        self.assertEqual(mask_from_classes(grid, [10]).tolist(), [[True, False], [False, True]])


class CommandLineTest(unittest.TestCase):
    def test_writes_all_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            dem_path = os.path.join(tmp, "dem.tif")
            ds = gdal.GetDriverByName("GTiff").Create(dem_path, 61, 61, 1, gdal.GDT_Float32)
            ds.SetGeoTransform(GT_30M)
            ds.GetRasterBand(1).WriteArray(cone(61, 61, 30, 30))
            ds = None
            out = os.path.join(tmp, "out")
            self.assertEqual(main(["--dem", dem_path, "--goal", "1", "--grid-step", "10", "--out", out]), 0)
            for name in ("summary.json", "towers.geojson", "coverage.tif", "map.png"):
                self.assertTrue(os.path.exists(os.path.join(out, name)), name)
            with open(os.path.join(out, "summary.json"), encoding="utf-8") as f:
                summary = json.load(f)
            self.assertEqual(summary["towers"], 1)
            self.assertEqual(summary["coverage"], 1.0)

    def test_rejects_a_mask_on_another_grid(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = {}
            for name, size in (("dem", 20), ("mask", 10)):
                paths[name] = os.path.join(tmp, f"{name}.tif")
                ds = gdal.GetDriverByName("GTiff").Create(paths[name], size, size, 1, gdal.GDT_Float32)
                ds.SetGeoTransform(GT_30M)
                ds.GetRasterBand(1).WriteArray(np.ones((size, size)))
                ds = None
            with self.assertRaises(ValueError):
                main(["--dem", paths["dem"], "--mask", paths["mask"], "--out", os.path.join(tmp, "o")])


if __name__ == "__main__":
    unittest.main()
