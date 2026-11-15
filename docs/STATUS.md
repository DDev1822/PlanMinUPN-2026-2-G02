# Estado técnico · G02

- Fuente: Pampa Norte, DS02/EXP03, y `Topopl.csv` adicional con SHA-256 `6b150af3656c1bd7832b78e965af82ab10f48ac82126f700b740be9ff573b7f1`.
- P2: geometría histórica aprobada, 37 × 35 × 375 = 485 625 bloques. No se modificó su origen ni tamaño.
- P3: criterio local TIN aprobado por DD el 15 de noviembre de 2026. Margen de holdout ±18,119216 unidades Z y límite de arista de 29,154759 unidades XY. `ROCK` 293 263, `AIR` 123 998, `TOPO_UNCERTAIN` 68 364. Las 1 295 columnas tienen cobertura geométrica; 1 223 cumplen soporte de arista. CRS y datum desconocidos.
- P4: asignación literal preliminar a 54 993 centros ROCK; 1 564 ambiguos y 236 706 sin soporte. Radio igual a la diagonal de una celda P2 (29,192620 m) y banda de ambigüedad igual a su altura (1,486290 m). No se infieren sólidos geológicos ni litología en AIR o celdas inciertas.
- P5: exportación reproducible de `data/processed/m01b/block_model.csv.gz`, compósitos, QA y visor 3D. La tabla preserva todos los estados sin imputar tonelaje a celdas inciertas.
- S11/S12: corridas académicas propias con manifiestos y controles computacionales; comprueba `python -m src.missions.g02 verificar` para conocer los IDs activos. S11 usa IDW² y S12 inventario candidato con escenarios A/B. Los CSV completos son la fuente numérica; los visores muestrean bloques.
- Kai: 8 + 16 + 6 actividades, 21 observaciones E1, 26 S11/S12, SQLite local por alias, Excel e informe/ZIP individual. La prueba técnica del controlador no reemplaza la conversación humana ni la valoración del tutor.

**Límites:** no se acreditan georreferenciación absoluta, continuidad geológica, estimación profesional de recursos, pit, accesos, precedencias, secuencia de extracción ni reservas. La aceptación conversacional humana y la revisión visual docente están pendientes.
