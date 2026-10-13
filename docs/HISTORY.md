# Project history

Decisions and changes, newest first. Read this before starting new work and add a dated
entry after each working session.

---

## 2026-10-14: Rebuilt with real viewshed analysis, tested, moved to GitHub

**Origin.** The project started as a GIS course assignment ("CBS Final Pafta") in PyCharm on a
Linux machine (`projectAnalysis/fire2.py`, `test.py`, `DEM1.tif`, `pafta.tif`), developed in
a ChatGPT conversation ("Yangın Kulesi Görünürlük Analizi"). Goal: the fewest 20 m fire towers
that see every part of the green (forest) areas of a sheet. The original files are not on the
current computer.

**Review of the earlier script** (final version from that conversation):
- Its "visibility analysis" was `maximum_filter(size=20)`: it marks local maxima in a
  20 x 20 cell window and computes no line of sight; the result was not used afterwards.
- The 20 m tower height was used as a window size and compared with terrain elevation; it
  never entered a visibility calculation.
- Towers were the highest cell of each 300 x 300 block, sorted by elevation, capped at 20.
  On a 1088-cell sheet that gives at most 16 blocks; no coverage check, no minimum.
- `np.unravel_index(..., (300, 300))` assumes full blocks; in the smaller edge blocks it
  returns wrong cells. This caused the "index 1088 out of bounds" errors; the fix in the
  conversation only dropped those towers, leaving the edges without towers.
- The forest mask was not used in the final version.

**Test of the earlier script** on an open-data sheet like the original (1088 x 1088, 30 m,
Mugla forests, 86% tree cover): it placed 14 of the 20 requested towers; with a real viewshed
(20 m tower, 15 km) they see 60.7% of the forest surface (72.5% for smoke at 10 m). Two
towers sit at the wrong cell because of the index bug.

**Rebuild:** candidates (summits + grid) → GDAL viewshed per candidate → greedy set cover →
pruning. Same 14 towers now see 69.8% / 80.8%; 28 towers reach 90% for smoke at 10 m. Added a
colour-map mask (green areas of a scanned/exported JPEG or TIFF sheet), grid checks, a CLI,
outputs (GeoJSON, coverage GeoTIFF, summary, map) and 17 tests on synthetic terrain.

**Next steps**
- Run on the original sheet if `DEM1.tif` / `pafta.tif` turn up.
- Buffer the DEM around the area of interest to avoid edge towers.
- Optional exact optimum (integer programming) on aggregated cells for small areas.
- Weight target cells by fire risk (slope, aspect, fuel) instead of treating all forest equally.
- Contour extraction from a scanned topographic map (colour tracing → vector contours →
  interpolated DEM) when no DEM is available.
