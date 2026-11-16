"""Turn the open region boundaries into light SVG paths for the dashboard map (dashboard/map.js).

    python scripts/build_map.py

Source: geoBoundaries gbOpen SAU ADM1 (simplified), built from OpenStreetMap data,
Open Data Commons Open Database License 1.0. (c) OpenStreetMap contributors.
https://www.geoboundaries.org/  -  boundary id SAU-ADM1-25081817
The boundaries are used only to draw the map; no number in the analysis depends on them.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data_raw" / "geo" / "geoBoundaries-SAU-ADM1_simplified.geojson"
TARGET = ROOT / "dashboard" / "map.js"

ISO_TO_REGION = {"SA-01": "riyadh", "SA-02": "makkah", "SA-03": "madinah", "SA-04": "eastern", "SA-05": "qassim",
                 "SA-06": "hail", "SA-07": "tabuk", "SA-08": "northern_borders", "SA-09": "jazan", "SA-10": "najran",
                 "SA-11": "albaha", "SA-12": "aljawf", "SA-14": "aseer"}
WIDTH = 560
TOLERANCE_DEG = 0.035          # about 4 km: invisible at this size
MIN_RING_AREA_DEG2 = 0.02      # drop small islands


def simplify(points: list, tol: float) -> list:
    """Douglas-Peucker, iterative."""
    if len(points) < 3:
        return points
    keep = [False] * len(points)
    keep[0] = keep[-1] = True
    stack = [(0, len(points) - 1)]
    while stack:
        a, b = stack.pop()
        (x1, y1), (x2, y2) = points[a], points[b]
        dx, dy = x2 - x1, y2 - y1
        norm = math.hypot(dx, dy) or 1e-12
        worst, at = 0.0, None
        for i in range(a + 1, b):
            d = abs(dy * (points[i][0] - x1) - dx * (points[i][1] - y1)) / norm
            if d > worst:
                worst, at = d, i
        if at is not None and worst > tol:
            keep[at] = True
            stack += [(a, at), (at, b)]
    return [p for p, k in zip(points, keep) if k]


def simplify_ring(ring: list, tol: float) -> list:
    """A closed ring starts and ends at the same point, so split it at its farthest point first."""
    far = max(range(len(ring)), key=lambda i: math.hypot(ring[i][0] - ring[0][0], ring[i][1] - ring[0][1]))
    return simplify(ring[:far + 1], tol)[:-1] + simplify(ring[far:], tol)


def area(ring: list) -> float:
    return abs(sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]))) / 2


def centroid(ring: list) -> tuple:
    a = cx = cy = 0.0
    for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
        cross = x1 * y2 - x2 * y1
        a += cross
        cx += (x1 + x2) * cross
        cy += (y1 + y2) * cross
    return cx / (3 * a), cy / (3 * a)


def main() -> None:
    geo = json.loads(SOURCE.read_text(encoding="utf-8"))
    shapes = {}
    for feature in geo["features"]:
        key = ISO_TO_REGION[feature["properties"]["shapeISO"]]
        g = feature["geometry"]
        polygons = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        outer = [[(float(x), float(y)) for x, y in poly[0]] for poly in polygons]          # holes are not drawn
        rings = [r for r in outer if area(r) >= MIN_RING_AREA_DEG2] or [max(outer, key=area)]
        shapes[key] = [simplify_ring(r, TOLERANCE_DEG) for r in rings]
    assert set(shapes) == set(ISO_TO_REGION.values())

    lons = [x for rings in shapes.values() for r in rings for x, _ in r]
    lats = [y for rings in shapes.values() for r in rings for _, y in r]
    k = math.cos(math.radians((min(lats) + max(lats)) / 2))          # equirectangular at the mid latitude
    scale = WIDTH / ((max(lons) - min(lons)) * k)
    height = round((max(lats) - min(lats)) * scale)

    def project(pt: tuple) -> tuple:
        return round((pt[0] - min(lons)) * k * scale, 1), round((max(lats) - pt[1]) * scale, 1)

    regions = {}
    for key in sorted(shapes):
        rings = [[project(p) for p in r] for r in shapes[key]]
        d = " ".join("M" + " L".join(f"{x} {y}" for x, y in r) + " Z" for r in rings)
        cx, cy = centroid(max(rings, key=area))
        regions[key] = {"d": d, "cx": round(cx, 1), "cy": round(cy, 1)}
    payload = {"width": WIDTH, "height": height, "regions": regions,
               "source": "geoBoundaries gbOpen SAU ADM1 · © OpenStreetMap contributors (ODbL 1.0)"}
    with open(TARGET, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("window.WAQF_MAP = " + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + ";\n")
    points = sum(v["d"].count("L") + v["d"].count("M") for v in regions.values())
    print(f"dashboard/map.js written: 13 regions, {points} points, {TARGET.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
