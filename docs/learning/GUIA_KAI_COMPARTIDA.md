# Kai Planeamiento · recorrido G02

![DrillStone](../assets/L1.png)

**Proyecto:** Pampa Norte. **Release:** DS02/EXP03. Abre `index.html` para los datos E1, el modelo M01B y los resultados académicos S11/S12. Antes de usarlos, comprueba `python -m src.missions.g02 verificar`; cada corrida tiene su propio manifiesto. `Topopl.csv` es una dependencia topográfica adicional, no una pieza del manifiesto original DS02.

## Conversación y registro

Kai explica el concepto, plantea una decisión y su razón por turno, espera la respuesta y da una pista si hace falta. `DEMOSTRADO` requiere que el tutor valore una explicación propia; el controlador solo verifica estructura y secuencia. Una respuesta errónea se registra como `REQUIERE_REFUERZO` y se retoma. Un «sí» o la repetición de la pregunta no prueba comprensión.

El controlador activo es `kai/recorrido_g02.py`. Cada solicitud vive temporalmente en `.kai_solicitud_recorrido_g02.json`; se ejecuta con `python kai/recorrido_g02.py procesar-pendiente`. `estado` recupera el avance de un alias local. `perfil` pide consentimiento antes de guardar memoria social. Las 30 actividades se dividen en E1 (8), S11 (16) y S12 (6). El progreso queda en SQLite en `.kai_local/<alias>/`; el Excel es una vista del registro. El alias no es autenticación institucional.

La ficha E1 usa `estado_ficha_e1` y `responder_ficha_e1` para 21 observaciones extraídas del proyecto. La aplicación usa `estado_aplicacion` y `responder_aplicacion` para 13 observaciones S11 y 13 S12. Kai indica la pantalla y el bloque, pide el valor con unidad y conserva la respuesta literal. No rellena la ficha por el alumno ni inventa una observación. `entregar_individual` exige comprensión registrada, ficha y aplicación completas, además de productos grupales verificados; genera tres Excel, informe y ZIP en la carpeta local del alias. Esos archivos individuales no se suben a Git.

## Interpretación minera

E1 trata exploración, collar, survey, ensayes, compositación, topografía y malla. P2 conserva 485 625 celdas. P3 aplica TIN local de Topopl, margen empírico y estado incierto sin tonelaje. P4 asigna códigos litológicos literales solo con soporte cercano; la ausencia de asignación no equivale a estéril. Las unidades de longitud del release se interpretan localmente; CRS y datum topográficos formales no constan.

S11 enseña vecino cercano, IDW, variogramas, kriging, cokriging y simulación como métodos. El producto propio aplica IDW² con dominios literales preliminares, radio, muestras y sondajes mínimos, y presenta faltantes. Su volumen es una celda completa solo cuando P3 la clasifica con confianza como ROCK. Un mayor radio no demuestra mejor estimación. El visor usa una selección; el CSV completo y el manifiesto sustentan los totales.

S12 presenta mineral y desmonte **candidatos**, capacidades, flota y CAPEX/OPEX en A/B. La regla G02-ALLOC-01 reparte proporcionalmente inventario elegible para comparar capacidad; no ofrece una secuencia física, pit ni reservas profesionales. La ausencia de clasificación conserva su estado sin convertirla en desmonte. La evaluación semántica del estudiante, la aceptación conversacional real en Copilot/PyCharm y la revisión docente siguen pendientes.

![DrillStone · símbolo](../assets/L3.png)
