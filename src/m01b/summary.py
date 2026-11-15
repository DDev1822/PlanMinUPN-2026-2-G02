"""Resumen trazable del recorrido G02 y catálogo E1 ligado a sus datos."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE_COMMIT="02aa78cbf769ae18bcc557dd24bf7c16b5dc1125"


def run(root=ROOT):
    raw=root/"data/raw"
    model=root/"data/processed/m01b"
    qa=json.loads((model/"qa.json").read_text(encoding="utf-8"))
    with (model/"composites.csv").open(encoding="utf-8",newline="") as stream:
        comps=list(csv.DictReader(stream))
    full=sum(abs(float(r["length_m"])-2)<1e-6 for r in comps)
    residual=len(comps)-full
    summary={
      "project":{"group":"G02","name":"Pampa Norte","project_id":"pampa_norte",
                 "dataset":"DS02","release":"EXP03","synthetic_data":True},
      "source":{"repo":"https://github.com/DDev1822/PlanMinUPN-2026-2-G02",
                "branch":"main","commit":BASE_COMMIT,"role":"original_clean_baseline"},
      "exploration":{"holes":54,"survey":385,"assays":8002,"lithology_intervals":153,
                     "density_observations":630,"topography_points":218112},
      "compositing":{"target_length_m":2,"total":len(comps),"full":full,"residual":residual,
                      "example":{"hole_id":"PN-C01-001","contact_m":10}},
      "model":{"block_size_m":list(qa["p2_cell_size_m"]),"block_count":qa["blocks"],
               "topography":qa["topo_status_counts"],
               "lithology":{"ASSIGNED":qa["lith_status_counts"].get("ASSIGNED",0),
                            "UNKNOWN/UNASSIGNED":qa["blocks"]-qa["lith_status_counts"].get("ASSIGNED",0)},
               "professional_reserves_declared":False,"quantitative_estimates_available":True,
               "topography_uncertainty_policy":"DD_P3_G02_20261115"}}
    assert full+residual==8027
    dest=root/"datos";dest.mkdir(exist_ok=True)
    data=(json.dumps(summary,ensure_ascii=False,indent=2)+"\n").encode("utf-8")
    (dest/"resumen_verificado.json").write_bytes(data)
    (dest/"resumen.js").write_text("window.PLANMIN_SUMMARY="+json.dumps(summary,ensure_ascii=False,separators=(',',':'))+";\n",encoding="utf-8")
    catalog_path=root/"kai/ficha_individual_g02.json"
    catalog=json.loads(catalog_path.read_text(encoding="utf-8"))
    catalog["source_commit"]=BASE_COMMIT
    catalog["resumen_sha256"]=hashlib.sha256(data).hexdigest()
    for f in catalog["campos"]:
        if f["id"]=="BLOQUES.PARTIAL":
            f.update(id="BLOQUES.TOPO_UNCERTAIN",etiqueta="Celdas topográficas inciertas",
                     pregunta="¿Cuántas celdas quedan TOPO_UNCERTAIN por P3?",
                     pista="Consulta la tarjeta de incertidumbre topográfica: esas celdas no tienen tonelaje.")
            f["fuente"][-1]="TOPO_UNCERTAIN"
    catalog_path.write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return summary


if __name__=="__main__":print(json.dumps(run(),ensure_ascii=False,indent=2))
