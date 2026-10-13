# CLAUDE.md — Fire Tower Placement

Fewest fire lookout towers that see a target area on a DEM: GDAL viewshed + greedy set cover.
Details: [README.md](README.md).

**At the start of a session read [docs/HISTORY.md](docs/HISTORY.md)**: origin, review of the
earlier script, results, next steps. Add a dated entry there (newest first) after each session.

## Rules
- Code, README, docs and commit messages in English.
- Visibility is always real line of sight (`firetower.viewshed`); never replace it with
  elevation heuristics.
- Distances and heights in metres; refuse geographic (degree) DEMs and masks on another grid
  instead of resampling silently.
- Tower height, range and target height are assumptions, not norms; say so in outputs/docs.
- Every change to placement or visibility needs a test on synthetic terrain with a known answer.
- `data/` and `results/` are not committed.

## Commands
```bash
run.bat -m unittest discover -s tests -v       # GDAL from QGIS
run.bat scripts/prepare_example_data.py        # example sheet into data/
run.bat -m firetower --dem data/dem.tif --mask data/forest.tif --target-height 10 --out results
run.bat scripts/compare_legacy.py data/dem.tif data/forest.tif 10
```
