"""Volumen P3 conservador: nunca cuantificar superficie incierta."""
from __future__ import annotations

import math
from collections import Counter


def safe_volumes(blocks, _topography_path=None):
    rows=[]
    for b in blocks:
        full=math.prod(b[axis+"_max"]-b[axis+"_min"] for axis in "xyz")
        state=b["topo_status"]
        rock=full if state=="ROCK" else 0.0 if state=="AIR" else None
        rows.append(dict(cell_volume_m3=full,rock_volume_m3=rock,
                         rock_fraction=rock/full if rock is not None else None,
                         tin_z_center_m=b["topo_z_m"],
                         tin_center_topo_status=b["nominal_topo_status"],
                         footprint_area_covered_m2=b["topo_footprint_area_m2"],
                         volume_status="FULL_ROCK_CONFIDENT" if state=="ROCK" else
                         "AIR_EXCLUDED" if state=="AIR" else "TOPO_UNCERTAIN_NO_VOLUME" if state=="TOPO_UNCERTAIN" else
                         "NO_TIN_COVERAGE"))
    return rows,dict(method="P3_DD_APPROVED_CONSERVATIVE_FULL_OR_NULL",
                     statuses=dict(Counter(r["volume_status"] for r in rows)),
                     partial_fraction_model="NOT_APPLIED; uncertain has null rock volume",
                     topography_crs="UNKNOWN",vertical_datum="UNKNOWN")
