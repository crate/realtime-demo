from __future__ import annotations
from pathlib import Path
from typing import Optional, Sequence
import geopandas as gpd
from shapely.geometry import Point
from shapely.prepared import prep

class PointTester:
    """
    Point-in-polygon tester using a local .shp file.

    - Expects a Natural Earth / admin-level countries shapefile (or similar)
      that includes Germany as one of the features.
    - CRS is normalised to EPSG:4326 (lon/lat).
    - Border-inclusive by default (use covers). Switch to contains for strict interior.
    """

    # Common field names in country admin datasets
    _ISO3_FIELDS: Sequence[str] = ("ISO_A3", "iso_a3", "ADM0_A3", "WB_A3", "SOV_A3", "GU_A3")
    _NAME_FIELDS: Sequence[str] = ("NAME_EN", "NAME", "ADMIN", "admin", "COUNTRY")

    def __init__(
        self,
        shp_path: str | Path,
        country_iso3: str = "DEU",
        include_border: bool = True,
    ):
        shp_path = Path(shp_path)
        if not shp_path.exists():
            raise FileNotFoundError(f"Shapefile not found: {shp_path}")

        # Read the shapefile
        gdf = gpd.read_file(shp_path)

        # Normalise CRS to WGS84
        if gdf.crs is None:
            # Many global admin shapefiles are already WGS84; set if missing.
            gdf = gdf.set_crs(4326)
        elif gdf.crs.to_epsg() != 4326:
            gdf = gdf.to_crs(4326)

        # Try ISO3 first (robust across datasets)
        de = self._select_by_iso3(gdf, country_iso3)
        if de.empty:
            # Fallback by name (to Germany)
            de = self._select_by_name(gdf, "GERMANY")
        if de.empty:
            raise ValueError(
                "Could not find Germany in the provided shapefile. "
                "Tried ISO3 fields "
                f"{list(self._ISO3_FIELDS)} and name fields {list(self._NAME_FIELDS)}."
            )

        # Prepare geometry and bbox for fast queries
        self._geom_prepared = prep(de.unary_union)
        self._minx, self._miny, self._maxx, self._maxy = de.total_bounds
        self._include_border = include_border

    # Actual function that does the check
    def contains_latlon(self, lat: float, lon: float) -> bool:
        """Return True iff (lat, lon) is in Germany (border-inclusive by default)."""
        if not (self._minx <= lon <= self._maxx and self._miny <= lat <= self._maxy):
            return False
        pt = Point(lon, lat)  # shapely uses (x, y) == (lon, lat)
        return self._geom_prepared.covers(pt) if self._include_border else self._geom_prepared.contains(pt)

    # Get bounds so we don't get TOO much unnecessary data
    def bounds(self) -> list[float]:
        return [self._miny, self._minx, self._maxy, self._maxx]
 
    # Internal helpers
    def _select_by_iso3(self, gdf: gpd.GeoDataFrame, iso3: str) -> gpd.GeoDataFrame:
        for col in self._ISO3_FIELDS:
            if col in gdf.columns:
                de = gdf[gdf[col] == iso3]
                if not de.empty:
                    return de
        return gpd.GeoDataFrame(geometry=[], crs=gdf.crs)

    def _select_by_name(self, gdf: gpd.GeoDataFrame, name_upper: str) -> gpd.GeoDataFrame:
        for col in self._NAME_FIELDS:
            if col in gdf.columns:
                # compare uppercase for robustness
                series = gdf[col].astype(str).str.upper()
                de = gdf[series == name_upper]
                if not de.empty:
                    return de
        return gpd.GeoDataFrame(geometry=[], crs=gdf.crs)
