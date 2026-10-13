from dataclasses import dataclass

# Standard atmospheric refraction coefficient used by GDAL / ArcGIS viewshed tools.
DEFAULT_CURVATURE_COEFF = 0.85714


@dataclass(frozen=True)
class ViewshedParams:
    """Line-of-sight settings. Heights and distances in metres (the DEM's units)."""

    tower_height: float = 20.0
    # Height above ground that must be visible: 0 = the ground surface itself,
    # > 0 = e.g. a smoke column above the canopy.
    target_height: float = 0.0
    max_distance: float = 15000.0
    curvature_coeff: float = DEFAULT_CURVATURE_COEFF


@dataclass(frozen=True)
class PlacementParams:
    """When to stop adding towers."""

    # Stop once this share of the target cells is seen.
    goal: float = 0.90
    # Never place more than this many towers (None = no limit).
    max_towers: int | None = None
    # Stop when the next tower would add less than this share of the target cells.
    min_gain: float = 0.0005
