"""Actual published protection polygons, grouped into analytical island sectors."""
import numpy as np
import pandas as pd
import shapely
from shapely.geometry import shape, mapping, box
from shapely.ops import unary_union
from pyproj import Geod


def mpa_sectors(collection, sites, bounds=(141.5, 26.2, 143.0, 28.1)):
    """Retain whole intersecting components; group by nearest island-group centre.

    The sectors are derived analytical groups, not separate official MPAs.
    The published boundary coordinates are not simplified, buffered, or clipped.
    """
    region = box(*bounds)
    parts_by_site = [[] for _ in range(len(sites))]
    geod = Geod(ellps="WGS84")
    for feature in collection["features"]:
        geometry = shape(feature["geometry"])
        if not geometry.is_valid:
            raise ValueError("Published MPA geometry is invalid; inspect before analysis.")
        parts = list(geometry.geoms) if geometry.geom_type == "MultiPolygon" else [geometry]
        for part in parts:
            if not part.intersects(region):
                continue
            centre = part.representative_point()
            _, _, distance = geod.inv(np.full(len(sites), centre.x),
                                     np.full(len(sites), centre.y),
                                     sites.target_lon.to_numpy(), sites.target_lat.to_numpy())
            parts_by_site[int(np.argmin(distance))].append(part)
    if any(not parts for parts in parts_by_site):
        raise ValueError("At least one island group has no protected-area component.")
    geometries = [unary_union(parts) for parts in parts_by_site]
    features = [{"type": "Feature", "geometry": mapping(g),
                 "properties": {"sector": name + " — Ordinary Zone sector",
                                "parent_site": "Ogasawara - Ordinary Zone",
                                "components": len(parts),
                                "classification": "derived analytical sector; not a separate designation"}}
                for g, name, parts in zip(geometries, sites.name, parts_by_site)]
    return geometries, {"type": "FeatureCollection", "features": features}


def polygon_encounters(ds, sites, geometries, released, min_age_days, max_age_days):
    """Physical encounters with real polygons, using active sampled positions."""
    arrays = {name: ds[name].transpose("trajectory", "time").values
              for name in ["lon", "lat", "status", "age_seconds", "origin_marker"]}
    marker = arrays["origin_marker"]
    has_source = np.isfinite(marker)
    if not has_source.any(axis=1).all():
        raise ValueError("A trajectory has no source marker.")
    sources = marker[np.arange(len(marker)), has_source.argmax(axis=1)].astype(int)
    if (sources < 0).any() or (sources >= len(sites)).any():
        raise ValueError("Unknown source marker.")
    if not np.array_equal(np.bincount(sources, minlength=len(sites)), released):
        raise ValueError("Release denominators do not match trajectory sources.")
    age = arrays["age_seconds"] / 86400
    valid = (np.isfinite(arrays["lon"]) & np.isfinite(arrays["lat"])
             & (arrays["status"] == 0) & (age >= min_age_days) & (age <= max_age_days))
    counts = np.zeros((len(sites), len(geometries)), dtype=int)
    for dest, geometry in enumerate(geometries):
        shapely.prepare(geometry)
        hit = np.zeros(valid.shape, dtype=bool)
        hit[valid] = shapely.intersects_xy(geometry, arrays["lon"][valid], arrays["lat"][valid])
        counts[:, dest] = np.bincount(sources[hit.any(axis=1)], minlength=len(sites))
    names = sites.name.tolist()
    result = pd.DataFrame(counts, index=names, columns=[n + " MPA sector" for n in names])
    result.index.name = "release_source"
    return result, result.div(np.asarray(released), axis=0)
