# PlanMinUPN 2026-2 · G02 Pampa Norte

Distribución independiente de G02, proyecto sintético **DS02/EXP03**. El árbol inicial procede del HEAD estudiantil `85d384f9aedc34d10d47f4fa6aca0625551e7015`; los resultados IMP-008 de este repositorio se calcularon con sus datos propios. No se importó el historial anterior ni se usaron tonelajes de otro grupo.

## Inicio

1. Clona el repositorio y abre la raíz en PyCharm con Python 3.12.
2. Instala dependencias con `python -m pip install -r requirements.txt`.
3. Ejecuta `python -m pytest -q` y `python -m src.missions.g02 verificar`.
4. Abre `index.html` para E1, M01B, S11 y S12. Selecciona el agente `.github/agents/kai-planeamiento.agent.md` en Copilot.

`data/raw/` contiene el release DS02/EXP03 y la topografía adicional Topopl, cuya procedencia se declara aparte. `data/processed/m01b/` contiene la malla histórica P2 de 485 625 celdas con clasificación P3 y asignación litológica preliminar P4. `outputs/g02_s11/` y `outputs/g02_s12/` contienen modelos académicos verificados por manifiesto, reportes, CSV y visores. La tabla completa está en CSV comprimido; los visores 3D muestran una selección para mantenerlos utilizables.

## Regla espacial y alcance

DD aprobó para este ejercicio un TIN local de Topopl, margen empírico ±18,119216 unidades Z y arista máxima de 29,154759 unidades XY. Las celdas `TOPO_UNCERTAIN` mantienen volumen y tonelaje nulos. CRS y datum permanecen desconocidos. P4 usa cercanía al compósito C2 y deja sin asignar lo ambiguo o lejano; no demuestra sólidos ni continuidad geológica. S11 usa IDW² como proxy académico; S12 compara inventario candidato y escenarios A/B sin secuencia física ni clasificación profesional de reservas. Véase `docs/STATUS.md`.

Kai ofrece 30 actividades, 21 observaciones E1 y 26 de aplicación, con registro individual local, Excel, informe y ZIP. La guía está en `docs/learning/GUIA_KAI_COMPARTIDA.md`; el controlador activo es `kai/recorrido_g02.py`. `.kai_local/` no se publica. La valoración semántica del alumno corresponde al tutor; la aceptación conversacional real y cualquier aprobación institucional siguen pendientes.
