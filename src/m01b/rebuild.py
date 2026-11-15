"""Reconstruye la malla P2 G02 y clasifica P3 con la regla aprobada por DD.

No estima volumen de roca ni tonelaje para una celda topográficamente incierta.
La asignación P4 es categórica preliminar; no representa sólidos geológicos.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import math
from collections import Counter
from contextlib import contextmanager
from pathlib import Path

import numpy as np
from scipy.interpolate import LinearNDInterpolator
from scipy.spatial import Delaunay, cKDTree

from src.mod1.compositing import build_m01b_composites
from src.mod1.loader import load_raw_data
from src.mod1.validator import validate_data
from src.missions.volume import clip, area_integral

ROOT = Path(__file__).resolve().parents[2]
ORIGIN = (242342.62969373562, 8196192.574427972, 2990.4449489083745)
SIZE = (20.615528128083973, 20.615528128083973, 1.4862896509547885)
SHAPE = (37, 35, 375)
TOPO_SHA256 = "6b150af3656c1bd7832b78e965af82ab10f48ac82126f700b740be9ff573b7f1"
TOPO_ERROR_BAND = 18.119215791090028  # maximum observed spatial-sector holdout error, Z units
SUPPORT_EDGE_LIMIT = math.hypot(SIZE[0], SIZE[1])
P4_RADIUS = math.sqrt(sum(side * side for side in SIZE))
P4_AMBIGUITY_BAND = SIZE[2]
FIELDS = ("block_id", "i", "j", "k", "x_min", "y_min", "z_min", "x_max", "y_max", "z_max",
          "x_center", "y_center", "z_center", "dx", "dy", "dz", "volume_m3", "topo_status",
          "nominal_topo_status", "topo_z_m", "tin_min_z", "tin_max_z", "topo_support_max_edge",
          "topo_footprint_area", "topo_reason", "lith_status", "lith_code", "lith_nearest_distance_m",
          "lith_reason")


@contextmanager
def deterministic_gzip_text(path):
    """Gzip sin nombre ni hora de creación para reproducir los SHA del modelo."""
    with path.open("wb") as raw_stream:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw_stream, mtime=0) as compressed:
            with io.TextIOWrapper(compressed, encoding="utf-8", newline="") as stream:
                yield stream


def surface_columns(points: np.ndarray) -> tuple[dict, dict]:
    """For each P2 XY footprint, clip all intersecting TIN planes exactly."""
    translation = points[:, :2].min(axis=0)
    local = points.copy()
    local[:, :2] -= translation
    tin = Delaunay(local[:, :2])
    triangles = local[tin.simplices]
    mins = triangles[:, :, :2].min(axis=1)
    maxs = triangles[:, :, :2].max(axis=1)
    edges = np.stack((np.linalg.norm(triangles[:, 0, :2]-triangles[:, 1, :2],axis=1),
                      np.linalg.norm(triangles[:, 1, :2]-triangles[:, 2, :2],axis=1),
                      np.linalg.norm(triangles[:, 2, :2]-triangles[:, 0, :2],axis=1)),axis=1).max(axis=1)
    center_xy = np.array([[(ORIGIN[0]+(i+.5)*SIZE[0])-translation[0],
                           (ORIGIN[1]+(j+.5)*SIZE[1])-translation[1]]
                          for i in range(SHAPE[0]) for j in range(SHAPE[1])])
    center_z = LinearNDInterpolator(tin, local[:, 2])(center_xy)
    columns = {}
    max_area_error = 0.0
    for i in range(SHAPE[0]):
        for j in range(SHAPE[1]):
            x0 = ORIGIN[0]+i*SIZE[0]-translation[0]
            x1 = x0+SIZE[0]
            y0 = ORIGIN[1]+j*SIZE[1]-translation[1]
            y1 = y0+SIZE[1]
            candidate = np.flatnonzero((maxs[:,0]>x0)&(mins[:,0]<x1)&(maxs[:,1]>y0)&(mins[:,1]<y1))
            areas, heights, used_edges = [], [], []
            for t in candidate:
                polygon = [tuple(p) for p in triangles[t]]
                for axis, bound, above in ((0,x0,True),(0,x1,False),(1,y0,True),(1,y1,False)):
                    polygon = clip(polygon,axis,bound,above)
                area,_ = area_integral(polygon)
                if area > 1e-12:
                    areas.append(area)
                    heights.extend(p[2] for p in polygon)
                    used_edges.append(float(edges[t]))
            covered_area = math.fsum(areas)
            error = abs(covered_area-SIZE[0]*SIZE[1])
            max_area_error = max(max_area_error,error)
            covered = bool(heights and error <= max(1e-6,SIZE[0]*SIZE[1]*1e-8)
                           and np.isfinite(center_z[i*SHAPE[1]+j]))
            edge = max(used_edges,default=float("inf"))
            columns[i,j] = dict(covered=covered, zmin=min(heights,default=None),
                                zmax=max(heights,default=None), center_z=float(center_z[i*SHAPE[1]+j])
                                if np.isfinite(center_z[i*SHAPE[1]+j]) else None,
                                max_edge=edge, area=covered_area,
                                supported=covered and edge<=SUPPORT_EDGE_LIMIT+1e-9)
    return columns, dict(tin_points=len(local),tin_triangles=len(triangles),
                         numerical_translation_xy=translation.tolist(),
                         max_footprint_area_error=max_area_error,
                         fully_covered_columns=sum(v["covered"] for v in columns.values()),
                         edge_supported_columns=sum(v["supported"] for v in columns.values()))


def classify_column(column: dict) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    floor = ORIGIN[2]+np.arange(SHAPE[2])*SIZE[2]
    roof = floor+SIZE[2]
    if not column["covered"]:
        return (np.full(SHAPE[2],"OUTSIDE",dtype=object),
                np.full(SHAPE[2],"UNKNOWN",dtype=object),
                np.full(SHAPE[2],"NO_TIN_COVERAGE",dtype=object))
    low, high = column["zmin"],column["zmax"]
    nominal = np.where(roof<=low,"ROCK",np.where(floor>=high,"AIR","PARTIAL"))
    if not column["supported"]:
        return (np.full(SHAPE[2],"TOPO_UNCERTAIN",dtype=object),nominal,
                np.full(SHAPE[2],"LOW_TOPO_SUPPORT",dtype=object))
    status = np.where(roof<=low-TOPO_ERROR_BAND,"ROCK",
                      np.where(floor>=high+TOPO_ERROR_BAND,"AIR","TOPO_UNCERTAIN"))
    reason = np.where(status=="TOPO_UNCERTAIN","SPATIAL_HOLDOUT_BAND","CONFIDENT_TIN_CLASS")
    return status,nominal,reason


def assign_preliminary_lithology(rock_xyz: np.ndarray, composites: list[dict]) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, dict]:
    """Nearest observed C2 midpoint by literal code, limited to one P2 cell diagonal."""
    codes = sorted({r["lith_code"] for r in composites if r["lith_code"]})
    distances = np.empty((len(rock_xyz),len(codes)),dtype=float)
    for c,code in enumerate(codes):
        sample = np.array([[float(r["x_mid"]),float(r["y_mid"]),float(r["z_mid"])]
                           for r in composites if r["lith_code"]==code])
        distances[:,c] = cKDTree(sample).query(rock_xyz,workers=-1)[0]
    best_idx = distances.argmin(axis=1)
    best = distances[np.arange(len(rock_xyz)),best_idx]
    ordered = np.sort(distances,axis=1)
    second = ordered[:,1] if len(codes)>1 else np.full(len(rock_xyz),np.inf)
    assigned = best<=P4_RADIUS
    ambiguous = assigned&(second-best<=P4_AMBIGUITY_BAND+1e-9)
    nearest_code=np.asarray(codes)[best_idx]
    air_nearest=assigned&(nearest_code=="AIR")
    status = np.where(~assigned,"UNASSIGNED",np.where(air_nearest,"UNASSIGNED",
                      np.where(ambiguous,"AMBIGUOUS","ASSIGNED")))
    code = np.where(status=="ASSIGNED",np.asarray(codes)[best_idx],"")
    reason=np.where(~assigned,"NO_SUPPORT_WITHIN_CELL_DIAGONAL",
                    np.where(air_nearest,"NEAREST_OBSERVATION_IS_AIR",
                             np.where(ambiguous,"AMBIGUOUS_LITERAL_CODES","SUPPORTED_CATEGORICAL_ASSIGNMENT")))
    qa = dict(method="NEAREST_C2_MIDPOINT_PER_LITERAL_CODE",radius_m=P4_RADIUS,
              ambiguity_band_m=P4_AMBIGUITY_BAND,unique_literal_codes=codes,
              rock_centers=len(rock_xyz),status_counts=dict(Counter(status)),
              reason_counts=dict(Counter(reason)))
    return status,code,best,reason,qa


def rebuild(root: Path = ROOT) -> dict:
    raw_dir = root/"data/raw"
    topo_path = raw_dir/"Topopl.csv"
    if hashlib.sha256(topo_path.read_bytes()).hexdigest()!=TOPO_SHA256:
        raise ValueError("Topopl no coincide con la fuente aprobada")
    raw = load_raw_data(raw_dir)
    errors = [f for f in validate_data(raw)["findings"] if f["severity"]=="ERROR"]
    if errors:
        raise ValueError(f"M01 inválido: {errors[:2]}")
    manifest=raw["release_manifest"]
    if (manifest["dataset_id"],manifest["release_id"],manifest.get("synthetic_data"))!=("DS02","EXP03",True):
        raise ValueError("Dataset/release G02 incorrecto")
    with topo_path.open(encoding="utf-8-sig",newline="") as stream:
        topo = np.asarray([(float(r["X"]),float(r["Y"]),float(r["Z"])) for r in csv.DictReader(stream)])
    if len(topo)!=218112 or not np.isfinite(topo).all():
        raise ValueError("Topopl inválido")
    out=root/"data/processed/m01b"
    out.mkdir(parents=True,exist_ok=True)
    build_m01b_composites(raw_dir,out/"composites.csv")
    with (out/"composites.csv").open(encoding="utf-8",newline="") as stream:
        composites=list(csv.DictReader(stream))
    columns,topo_qa=surface_columns(topo)
    n=math.prod(SHAPE)
    status=np.empty(n,dtype=object);nominal=np.empty(n,dtype=object);reason=np.empty(n,dtype=object)
    rock_indices=[];rock_xyz=[]
    def index(i,j,k):return (k*SHAPE[1]+j)*SHAPE[0]+i
    for i in range(SHAPE[0]):
        for j in range(SHAPE[1]):
            s,nom,r=classify_column(columns[i,j])
            for k in range(SHAPE[2]):
                p=index(i,j,k)
                status[p],nominal[p],reason[p]=s[k],nom[k],r[k]
                if s[k]=="ROCK":
                    rock_indices.append(p)
                    rock_xyz.append((ORIGIN[0]+(i+.5)*SIZE[0],ORIGIN[1]+(j+.5)*SIZE[1],
                                     ORIGIN[2]+(k+.5)*SIZE[2]))
    lith_status=np.full(n,"NOT_ELIGIBLE",dtype=object)
    lith_code=np.full(n,"",dtype=object)
    lith_reason=np.full(n,"NOT_CONFIDENT_ROCK",dtype=object)
    lith_distance=np.full(n,np.nan)
    ps,pc,pd,pr,p4_qa=assign_preliminary_lithology(np.asarray(rock_xyz),composites)
    lith_status[rock_indices]=ps;lith_code[rock_indices]=pc;lith_distance[rock_indices]=pd
    lith_reason[rock_indices]=pr
    path=out/"block_model.csv.gz"
    with deterministic_gzip_text(path) as stream:
        writer=csv.DictWriter(stream,fieldnames=FIELDS,lineterminator="\n")
        writer.writeheader()
        for k in range(SHAPE[2]):
            z0=ORIGIN[2]+k*SIZE[2]
            for j in range(SHAPE[1]):
                y0=ORIGIN[1]+j*SIZE[1]
                for i in range(SHAPE[0]):
                    x0=ORIGIN[0]+i*SIZE[0];p=index(i,j,k);col=columns[i,j]
                    writer.writerow(dict(block_id=f"B{i:03d}_{j:03d}_{k:03d}",i=i,j=j,k=k,
                        x_min=x0,y_min=y0,z_min=z0,x_max=x0+SIZE[0],y_max=y0+SIZE[1],z_max=z0+SIZE[2],
                        x_center=x0+SIZE[0]/2,y_center=y0+SIZE[1]/2,z_center=z0+SIZE[2]/2,
                        dx=SIZE[0],dy=SIZE[1],dz=SIZE[2],volume_m3=math.prod(SIZE),
                        topo_status=status[p],nominal_topo_status=nominal[p],
                        topo_z_m=col["center_z"] if col["center_z"] is not None else "",
                        tin_min_z=col["zmin"] if col["zmin"] is not None else "",
                        tin_max_z=col["zmax"] if col["zmax"] is not None else "",
                        topo_support_max_edge=col["max_edge"] if math.isfinite(col["max_edge"]) else "",
                        topo_footprint_area=col["area"],topo_reason=reason[p],
                        lith_status=lith_status[p],lith_code=lith_code[p],
                        lith_nearest_distance_m=lith_distance[p] if math.isfinite(lith_distance[p]) else "",
                        lith_reason=lith_reason[p]))
    qa=dict(group="G02",project="Pampa Norte",dataset="DS02/EXP03",p2_grid_shape=SHAPE,
            p2_origin_m=ORIGIN,p2_cell_size_m=SIZE,blocks=n,composites=len(composites),
            topography_sha256=TOPO_SHA256,topo_band_z_units=TOPO_ERROR_BAND,
            topo_edge_limit_xy_units=SUPPORT_EDGE_LIMIT,topography=topo_qa,
            topo_status_counts=dict(Counter(status)),nominal_topo_counts=dict(Counter(nominal)),
            lithology=p4_qa,lith_status_counts=dict(Counter(lith_status)),
            formal_crs="UNKNOWN",vertical_datum="UNKNOWN",
            p3_decision="DD approval in chat 2026-11-15; see teacher closure dossier",
            p4_scope="PRELIMINARY_LITERAL_CATEGORICAL_NOT_GEOLOGIC_SOLIDS")
    assert sum(qa["topo_status_counts"].values())==n
    assert all(lith_status[p]=="NOT_ELIGIBLE" for p in np.flatnonzero(status!="ROCK"))
    (out/"qa.json").write_text(json.dumps(qa,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    return qa


if __name__=="__main__":
    print(json.dumps(rebuild(),ensure_ascii=False,indent=2,allow_nan=False))
