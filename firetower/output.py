"""Result files: towers (GeoJSON), coverage raster, summary (JSON) and a map (PNG)."""
import json
import os
from dataclasses import asdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from osgeo import gdal, osr  # noqa: E402

from .params import PlacementParams, ViewshedParams  # noqa: E402
from .pipeline import Result  # noqa: E402
from .raster import Grid, write_like  # noqa: E402


def write_outputs(out_dir: str, dem: Grid, target: np.ndarray, result: Result,
                  view: ViewshedParams, place: PlacementParams) -> dict:
    os.makedirs(out_dir, exist_ok=True)
    p = result.placement
    summary = {
        "towers": len(result.towers),
        "target_cells": p.target_cells,
        "coverage": round(p.coverage, 4),
        "reachable_from_any_candidate": round(p.reachable, 4),
        "candidates": result.candidates,
        "seconds": round(result.seconds, 1),
        "viewshed": asdict(view),
        "placement": asdict(place),
    }
    with open(os.path.join(out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    _write_towers(os.path.join(out_dir, "towers.geojson"), dem, result, p.target_cells)
    covered = np.where(target, result.seen_count, -1).astype(np.int16)
    write_like(dem, covered, os.path.join(out_dir, "coverage.tif"), gdal.GDT_Int16, nodata=-1)
    _write_map(os.path.join(out_dir, "map.png"), dem, target, result)
    return summary


def _write_towers(path: str, dem: Grid, result: Result, target_cells: int) -> None:
    features, total = [], 0
    for k, t in enumerate(result.towers, start=1):
        total += t.gain_cells
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [round(t.x, 2), round(t.y, 2)]},
            "properties": {"id": k, "col": t.col, "row": t.row,
                           "elevation_m": round(t.elevation, 1),
                           "adds_share": round(t.gain_cells / target_cells, 4) if target_cells else 0},
        })
    collection = {"type": "FeatureCollection", "features": features}
    srs = osr.SpatialReference(wkt=dem.dataset.GetProjection()) if dem.dataset.GetProjection() else None
    if srs is not None and srs.GetAuthorityCode(None):
        collection["crs"] = {"type": "name", "properties": {
            "name": f"EPSG:{srs.GetAuthorityCode(None)}"}}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(collection, f)


def _write_map(path: str, dem: Grid, target: np.ndarray, result: Result) -> None:
    elev = np.where(dem.valid(), dem.array, np.nan)
    res = abs(dem.geotransform[1])
    dy, dx = np.gradient(np.nan_to_num(elev, nan=np.nanmin(elev)), res)
    slope = np.hypot(dx, dy)
    shade = np.clip(0.7 / np.sqrt(1 + slope ** 2) + 0.3 * (dx - dy) / (slope + 1e-9), 0, 1)
    rgb = np.dstack([shade] * 3) * 0.75
    seen = result.seen_count > 0
    rgb[target & seen] = rgb[target & seen] * 0.4 + np.array([0.1, 0.6, 0.2]) * 0.6
    rgb[target & ~seen] = rgb[target & ~seen] * 0.4 + np.array([0.85, 0.15, 0.1]) * 0.6

    fig, ax = plt.subplots(figsize=(8, 8))
    ax.imshow(rgb)
    ax.scatter([t.col for t in result.towers], [t.row for t in result.towers], marker="^", s=70,
               c="yellow", edgecolors="black", linewidths=0.8)
    p = result.placement
    ax.set_title(f"{len(result.towers)} towers, target area seen {p.coverage:.1%}\n"
                 "green: seen, red: not seen by any tower", fontsize=10)
    ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)
