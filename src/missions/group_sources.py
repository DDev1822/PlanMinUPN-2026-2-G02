"""Fuentes M01B propias de G02 para IMP-008; no importa resultados G05."""
from __future__ import annotations

GROUP = "G02"
DATASET = "DS02"

from collections import defaultdict
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from src.mod1.loader import load_raw_data
from src.mod1.validator import validate_data
from src.mod1.desurvey import desurvey
from src.mod1.positioning import position_intervals
from src.missions.estimation import Sample

ANALYTES = ("cu_pct", "mo_pct", "au_gt")


def read_csv(path: Path) -> list[dict[str, str]]:
    opener=gzip.open if path.suffix=='.gz' else open
    with opener(path,'rt',encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def number(value, nullable=False):
    if value is None or str(value).strip() == "":
        if nullable:
            return None
        raise ValueError("Valor numérico requerido")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("Valor no finito")
    return result


def _code(row, lithology):
    start, end = float(row["from_m"]), float(row["to_m"])
    codes = [r["lith_code"] for r in lithology[row["hole_id"]]
             if float(r["from_m"]) <= start + 1e-7 and float(r["to_m"]) >= end - 1e-7]
    return codes[0] if len(codes) == 1 else None


def _origins(row, assays):
    start, end = float(row["from_m"]), float(row["to_m"])
    identifiers = [r["sample_id"] for r in assays[row["hole_id"]]
                   if float(r["from_m"]) < end - 1e-8 and float(r["to_m"]) > start + 1e-8]
    if not identifiers or len(identifiers) != len(set(identifiers)):
        raise ValueError("Orígenes de compósito ausentes/duplicados")
    pieces = []
    for sid in identifiers:
        matches = [r for r in assays[row["hole_id"]] if r["sample_id"] == sid]
        if len(matches) != 1:
            raise ValueError("Origen de compósito inválido: " + sid)
        source = matches[0]
        low = max(start, float(source["from_m"]))
        high = min(end, float(source["to_m"]))
        if high <= low:
            raise ValueError("Origen sin intersección: " + sid)
        pieces.append((low, high, source))
    pieces.sort(key=lambda item: item[0])
    cursor = start
    for low, high, _ in pieces:
        if abs(low - cursor) > 1e-6:
            raise ValueError("Hueco o solape de procedencia en compósito")
        cursor = high
    if abs(cursor - end) > 1e-6:
        raise ValueError("Procedencia no cubre compósito")
    return identifiers, pieces


def _blocks_g02(root):
    rows = read_csv(root / "data/processed/m01b/block_model.csv.gz")
    if len(rows) != 485625 or len({r["block_id"] for r in rows}) != len(rows):
        raise ValueError("M01B G02 incompleto o IDs duplicados")
    result = []
    for r in rows:
        sizes = [number(r[k]) for k in ("dx", "dy", "dz")]
        row = {"i": int(r["i"]), "j": int(r["j"]), "k": int(r["k"]),
               "block_id": "G02-" + r["block_id"], "source_block_id": r["block_id"],
               "lith_code": r["lith_code"], "lith_status": r["lith_status"],
               "lith_assignment_basis": "C2_MIDPOINT_CELL_DIAGONAL" if r["lith_status"] == "ASSIGNED" else r["lith_reason"],
               "topo_status": r["topo_status"], "topo_z_m": number(r["topo_z_m"], True),
               "nominal_topo_status": r["nominal_topo_status"], "topo_reason": r["topo_reason"],
               "topo_footprint_area_m2": number(r["topo_footprint_area"]),
               "lith_support_count": int(r["lith_status"] == "ASSIGNED"),
               "lith_nearest_distance_m": number(r["lith_nearest_distance_m"], True)}
        for axis in "xyz":
            row[axis + "_min"] = number(r[axis + "_min"])
            row[axis + "_max"] = number(r[axis + "_max"])
            row[axis + "_center"] = number(r[axis + "_center"])
        if not math.isclose(math.prod(sizes), number(r["volume_m3"]), abs_tol=1e-8):
            raise ValueError("M01B G02 volumen nominal discordante")
        result.append(row)
    return result


def prepare(root: Path, parameters: dict):
    raw = load_raw_data(root / "data/raw")
    validation = validate_data(raw)
    errors = [f for f in validation["findings"] if f["severity"] == "ERROR"]
    if errors:
        raise ValueError(f"M01 contiene {len(errors)} errores: {errors[:2]}")
    release = raw["release_manifest"]
    if (release["dataset_id"], release["release_id"], release.get("synthetic_data")) != (DATASET, "EXP03", True):
        raise ValueError("Release de grupo diferente al autorizado")
    for rel, expected in release["file_sha256"].items():
        actual = hashlib.sha256((root / "data/raw" / rel).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        if actual != expected:
            raise ValueError("SHA raw no coincide: " + rel)
    trajectory = desurvey(raw["collar"], raw["survey"])
    by_lith = defaultdict(list)
    by_assay = defaultdict(list)
    for row in raw["lithology"]:
        by_lith[row["hole_id"]].append(row)
    for row in raw["assay"]:
        by_assay[row["hole_id"]].append(row)
    path = root / ("data/processed/m01b/composites.csv")
    composites = read_csv(path)
    positioned = position_intervals(trajectory, {"assay": composites, "lithology": [], "alteration": [], "density": []})["assay"]
    grade_samples = []
    composite_qa = []
    for row, pos in zip(composites, positioned):
        start, end = number(row["from_m"]), number(row["to_m"])
        length = end - start
        if length <= 0 or not math.isclose(length, number(row["length_m"]), abs_tol=1e-6):
            raise ValueError("Longitud de compósito inválida")
        code = _code(row, by_lith)
        if not code or code != row["lith_code"]:
            raise ValueError("Compósito cruza contacto o no reproduce código")
        xyz = tuple(number(row["x_mid" if a == "x" else a + "_mid"]) for a in "xyz")
        if max(abs(a - number(pos[k + "_mid"])) for a, k in zip(xyz, "xyz")) > 1e-5:
            raise ValueError("XYZ de compósito no reproduce desurvey")
        origins, pieces = _origins(row, by_assay)
        values = {}
        for analyte in ANALYTES:
            vals = [number(source[analyte], True) for _, _, source in pieces]
            values[analyte] = None if any(v is None for v in vals) else math.fsum((high - low) * value for (low, high, _), value in zip(pieces, vals)) / length
        if not math.isclose(number(row["cu_pct"]), values["cu_pct"], rel_tol=1e-7, abs_tol=1e-8):
            raise ValueError("Cu compuesto no concilia con ensayes")
        sample_id = f"{GROUP}:{row['hole_id']}:{start:.9f}:{end:.9f}"
        full = math.isclose(length, parameters["grade"]["reference_length_m"], abs_tol=1e-6)
        eligible = full and code not in parameters["excluded_lithologies"]
        if eligible:
            grade_samples.append(Sample(sample_id, row["hole_id"], code, xyz, values, frozenset(origins)))
        composite_qa.append(dict(row, **values, composite_id=sample_id, source_sample_ids=";".join(origins), eligible_idw2=eligible))
    positioned_density = position_intervals(trajectory, {"assay": [], "lithology": [], "alteration": [], "density": raw["density"]})["density"]
    density_samples = []
    density_qa = []
    for row in positioned_density:
        code = _code(row, by_lith)
        rho = number(row.get("density_t_m3"), True)
        eligible = bool(code and code not in parameters["excluded_lithologies"] and rho and rho > 0)
        density_qa.append({k: v for k, v in row.items() if k != "trajectory_segments"} | {"lith_code": code, "eligible_idw2": eligible})
        if eligible:
            density_samples.append(Sample(row["density_sample_id"], row["hole_id"], code,
                                          tuple(number(row[k + "_mid"]) for k in "xyz"),
                                          {"density_t_m3": rho}, frozenset([row["density_sample_id"]])))
    blocks = _blocks_g02(root)
    if len({b["block_id"] for b in blocks}) != len(blocks):
        raise ValueError("IDs de bloque duplicados")
    qa = {"group": GROUP, "dataset": DATASET, "raw_counts": {k: len(raw[k]) for k in ("collar", "survey", "assay", "density", "lithology")},
          "composites": len(composites), "eligible_composites": len(grade_samples),
          "density_samples": len(positioned_density), "eligible_density_samples": len(density_samples),
          "m01b_blocks": len(blocks), "m01_findings": validation["findings"],
          "composite_xyz_reproduced": True, "cu_reconciled": True,
          "analytes_augmented_from_raw": ["mo_pct", "au_gt"], "formal_crs": "UNKNOWN"}
    return blocks, grade_samples, density_samples, composite_qa, density_qa, qa
