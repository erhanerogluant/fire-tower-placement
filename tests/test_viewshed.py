import unittest

import numpy as np

from firetower.params import ViewshedParams
from firetower.raster import grid_from_array
from firetower.viewshed import visible_cells

GT_10M = (500000.0, 10.0, 0.0, 4100000.0, 0.0, -10.0)


class ViewshedTest(unittest.TestCase):
    def test_flat_ground_is_fully_visible(self):
        dem = grid_from_array(np.zeros((101, 101)), GT_10M)
        seen = visible_cells(dem, 50, 50, ViewshedParams(max_distance=10000))
        self.assertTrue(seen.all())

    def test_wall_hides_the_ground_behind_it(self):
        z = np.zeros((101, 101))
        z[:, 50:52] = 200.0
        dem = grid_from_array(z, GT_10M)
        seen = visible_cells(dem, 20, 50, ViewshedParams(tower_height=20, max_distance=10000))
        self.assertTrue(seen[50, 5:48].all())
        self.assertFalse(seen[50, 55:].any())

    def test_target_height_makes_smoke_behind_a_low_wall_visible(self):
        z = np.zeros((101, 101))
        z[:, 50:52] = 30.0
        dem = grid_from_array(z, GT_10M)
        ground = visible_cells(dem, 20, 50, ViewshedParams(target_height=0, max_distance=10000))
        # sight line from the 20 m tower to 50 m of smoke passes the wall at 42.5 m (> 30 m)
        smoke = visible_cells(dem, 20, 50, ViewshedParams(target_height=50, max_distance=10000))
        self.assertFalse(ground[50, 60])
        self.assertTrue(smoke[50, 60])

    def test_window_near_the_corner_lands_in_the_right_place(self):
        dem = grid_from_array(np.zeros((101, 101)), GT_10M)
        seen = visible_cells(dem, 2, 3, ViewshedParams(max_distance=100))
        self.assertEqual(seen.shape, (101, 101))
        self.assertTrue(seen[3, 2] and seen[3, 10])
        self.assertFalse(seen[3, 20] or seen[50, 50])

    def test_nodata_cells_are_never_visible(self):
        z = np.zeros((51, 51))
        z[0:5, :] = -9999
        dem = grid_from_array(z, GT_10M, nodata=-9999)
        seen = visible_cells(dem, 25, 25, ViewshedParams(max_distance=10000))
        self.assertFalse(seen[0:5].any())


if __name__ == "__main__":
    unittest.main()
