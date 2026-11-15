# Modelo de bloques de recursos ACADÉMICO

Corrida `1bdc71adfd21abfcbfb3`. G02 DS02/EXP03; 485,625 celdas.

Cu estimado: 4985 bloques a 75 m; 4744 a 50 m. Densidad estimada: 54971. Tonelaje cuantificable: 92288914.846858 t en 54971 bloques. Con Cu y tonelaje: 4985 bloques, 8325973.187768 t.

## Trazabilidad

Ensayes originales → compósitos por longitud y contacto → IDW² por código preliminar. Mo y Au se reconstruyen desde ensayes; Cu se concilia con M01. Cada estimación conserva IDs, distancias, pesos y sondajes. Densidad usa desurvey M01 y mediciones íntegramente contenidas en un dominio. Residuales se preservan en QA. Volumen: celda completa únicamente para ROCK con margen P3; AIR cero; inciertas nulas. Se conserva el estado topográfico M01B por separado. Nulo no significa cero.

## Supuestos y límites

- Litología preliminar; continuidad entre sondajes no demostrada.
- Estimación en centro como proxy académico; soporte volumétrico no corregido.
- CRS/datum topográfico no documentados; marco local P3 aprobado por DD para DS02.
- Banda empírica máxima del holdout espacial y arista límite; celdas inciertas sin tonelaje.
- Incertidumbre de estimación no cuantificada por IDW².

## Verificación

`s11_validation.json` contiene controles ejecutados. La comparación manual .60 % / 2.64 t/m³ es un microcaso PT-01, no un bloque G02. La tabla completa respalda los totales; el 3D reduce contexto si excede 6000 cajas.
