"""Vista local 3D de una muestra determinista de M01B G02."""
from __future__ import annotations

import csv
import gzip
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]


def run(root=ROOT):
    qa=json.loads((root/"data/processed/m01b/qa.json").read_text(encoding="utf-8"))
    points={"ROCK":[],"TOPO_UNCERTAIN":[]}
    path=root/"data/processed/m01b/block_model.csv.gz"
    with gzip.open(path,"rt",encoding="utf-8",newline="") as stream:
        for index,row in enumerate(csv.DictReader(stream)):
            state=row["topo_status"]
            if index%73!=0 or state not in points:
                continue
            points[state].append([float(row[a+"_center"]) for a in "xyz"]+[row["block_id"],row["lith_code"]])
    figure={key:{"x":[r[0] for r in records],"y":[r[1] for r in records],
                 "z":[r[2] for r in records],"id":[r[3] for r in records],
                 "code":[r[4] for r in records]} for key,records in points.items()}
    data=json.dumps({"figure":figure,"qa":qa},ensure_ascii=False,separators=(",",":"))
    page='''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>M01B G02 · Pampa Norte</title>
<script src="../../assets/plotly-4.1.1.min.js"></script><style>body{margin:0;background:#101719;color:#e1ebef;font:15px system-ui}.wrap{max-width:1200px;margin:auto;padding:1rem}a{color:#77d9ce}#plot{height:75vh;min-height:400px}button{cursor:pointer}header{display:flex;align-items:center;gap:1rem}header img{height:45px}.note{color:#b4cbd2}</style></head><body><div class="wrap"><header><img src="../../docs/assets/L3.png" alt="DrillStone"><h1>M01B · Pampa Norte G02</h1></header><p><a href="../../index.html#bloques">Volver</a> · <a href="../../data/processed/m01b/block_model.csv.gz" download>Malla completa CSV.gz</a> · <a href="../../data/processed/m01b/qa.json">Controles P2–P4</a></p><p id="counts"></p><p class="note">Muestra determinista de centros ROCK y TOPO_UNCERTAIN para inspección visual. AIR no se representa como bloque físico. La malla completa tiene 485.625 celdas; los resultados íntegros están en CSV.gz. La geometría P2 usa celdas de 20,615528 × 20,615528 × 1,486290 m. P3 aplica la banda aprobada por DD; las celdas inciertas no tienen tonelaje.</p><div id="plot"></div><p id="selected" aria-live="polite">Selecciona un punto.</p><p class="note">CRS y datum formal de Topopl desconocidos. Litología P4 preliminar por soporte local; no equivale a sólidos geológicos ni a validación de recursos.</p></div><script>const D=__DATA__;const colors={ROCK:'#67b99b',TOPO_UNCERTAIN:'#e6bc71'};const traces=Object.entries(D.figure).map(([key,p])=>({type:'scatter3d',mode:'markers',name:key,x:p.x,y:p.y,z:p.z,customdata:p.id.map((id,i)=>[id,p.code[i]]),marker:{size:2,color:colors[key],opacity:.75},hovertemplate:'%{customdata[0]}<br>'+key+'<br>Litología: %{customdata[1]}<extra></extra>'}));document.getElementById('counts').textContent=`ROCK ${D.qa.topo_status_counts.ROCK.toLocaleString('es-PE')} · AIR ${D.qa.topo_status_counts.AIR.toLocaleString('es-PE')} · TOPO_UNCERTAIN ${D.qa.topo_status_counts.TOPO_UNCERTAIN.toLocaleString('es-PE')} · muestra ${Object.values(D.figure).reduce((n,p)=>n+p.x.length,0).toLocaleString('es-PE')}`;Plotly.newPlot('plot',traces,{paper_bgcolor:'#101719',plot_bgcolor:'#101719',font:{color:'#e1ebef'},scene:{aspectmode:'data',xaxis:{title:'X local (m)'},yaxis:{title:'Y local (m)'},zaxis:{title:'Z local (m)'}},margin:{l:0,r:0,t:0,b:0}},{responsive:true,displaylogo:false}).then(()=>{document.getElementById('plot').on('plotly_click',e=>{const [id,code]=e.points[0].customdata;document.getElementById('selected').textContent=`${id} · ${e.points[0].data.name} · código ${code||'sin asignación'}`});window.G02_M01B_VIEW_READY=true});</script></body></html>'''.replace("__DATA__",data)
    out=root/"outputs/figures/m01b_g02_3d.html"
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(page,encoding="utf-8")
    return {"path":str(out),"sample_points":sum(len(p) for p in points.values()),"full_blocks":qa["blocks"]}


if __name__=="__main__":print(json.dumps(run(),ensure_ascii=False))
