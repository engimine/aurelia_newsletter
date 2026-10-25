---
name: planos-estructuras-cte
description: Calcula estructuras sencillas de edificación según el Código Técnico de la Edificación (CTE DB-SE, SE-AE, SE-A, SE-M, SE-C, Código Estructural, NCSE-02, DB-SI 6) y genera el juego de planos de estructura en PDF (A3, cajetín ARISTOSIA PROJECTS) más la memoria de cálculo. Usar cuando se pida calcular o dimensionar una entreplanta, altillo, forjado ligero, plataforma o pórtico de vigas, viguetas, pilares y zapatas, o hacer "planos de estructura con cálculos según CTE".
---

# Planos de estructura con cálculo CTE

Herramienta en Python (matplotlib) que, a partir de un JSON de proyecto:

1. **Calcula** (`scripts/calculo.py`): acciones DB-SE-AE, combinaciones DB-SE (1,35G + 1,5Q; característica; casi permanente),
   viguetas (madera DB-SE-M o acero DB-SE-A), vigas principales, zunchos, pilares (pandeo + interacción N-M), placa de
   anclaje, zapata aislada (DB-SE-C + bielas y tirantes del Código Estructural), uniones, estabilidad lateral,
   sismo (aplicabilidad NCSE-02) y fuego (exigencia DB-SI 6). Dimensiona automáticamente si no se fija la sección.
2. **Dibuja** (`scripts/planos.py`) 6 hojas A3 con el cajetín de ARISTOSIA (formato del plano 00B):
   E-01 cuadro de características y notas · E-02 cimentación · E-03 planta de forjado · E-04 secciones A-A/B-B ·
   E-05 detalles (zapata y placa, placa en planta, unión viga-pilar, unión vigueta-viga) · E-06 resumen de cálculo.
3. **Redacta** la memoria de cálculo en Markdown con cada fórmula, valores y referencia normativa.

## Uso

```bash
python3 .claude/skills/planos-estructuras-cte/scripts/generar.py proyecto.json carpeta_salida --png
```

Salida: `<codigo>_planos_estructura.pdf`, `<codigo>_memoria_calculo.md`, `<codigo>_resultados.json` y PNG de cada hoja.
Dependencias: `pip install matplotlib numpy`.

## Esquema del JSON (ver `ejemplos/entreplanta_ejemplo.json`)

| Clave | Contenido |
|---|---|
| `proyecto` | titulo, subtitulo, promotor, emplazamiento, codigo, fecha, estudio, logo, autores[{nombre,titulo}], formato (A3/A1) |
| `uso` | Categoría DB-SE-AE tabla 3.1: A1, A2, B, C1…C5, D1, D2, E, F, G1 |
| `geometria` | luces_x[], luces_y[] (m entre ejes), altura_pilar (m, cara sup. zapata → cara inf. viga), direccion_viguetas x/y |
| `cargas` | permanentes[{nombre,valor,posterior}] (opcional; si falta usa valores tipo Anejo C), tabiqueria, barandilla, peso_barandilla, sobrecarga_uso (forzar) |
| `tabiqueria_tipo` | fragil (L/500), ordinaria (L/400), resto (L/300) — integridad DB-SE 4.3.3.1 |
| `clase_servicio` | 1, 2, 3 (DB-SE-M) |
| `materiales` | vigas (S275/S355 o C24/GL24h…), pilares (S275…), hormigon (HA-25…), armadura (B500S) |
| `forjado` | material (C24, GL24h, S275…), separacion (m), seccion [b,h] o perfil (opcional), apoyo "enrasado"/"apoyado", tablero |
| `vigas` | serie IPE/HEB o perfil fijo "IPE 220" / seccion [b,h] si madera |
| `pilares` | serie SHS/HEB, perfil fijo, base "empotrada"/"articulada", minimo (por defecto SHS 80x4) |
| `estabilidad` | tipo "muro" (separacion_anclajes, longitud_muro) / "pilares_empotrados" / "cruces" |
| `cimentacion` | tension_admisible (kPa), canto, profundidad, recubrimiento, lado (fijo) o lado_minimo |
| `sismo` | ab (g), importancia normal/especial |
| `resistencia_fuego` | "R 30", "R 60"… |

## Reglas

- Las tablas normativas están en `scripts/normativa.py` con su referencia. No inventar valores: si falta un dato, añadirlo
  allí citando documento y tabla.
- Comprobar siempre el resultado: `no cumplen: 0`. Si algo no cumple, cambiar sección/material o geometría y regenerar.
- Revisar visualmente los PNG antes de entregar (solapes de texto, cotas).
- El alcance del motor es el esquema viguetas → vigas → pilares → zapatas aisladas. Para otras tipologías (forjados de
  hormigón, cerchas, muros, pórticos rígidos, cubiertas con nieve/viento) ampliar `calculo.py` y `planos.py` siguiendo el
  mismo patrón (`Memoria.check(...)` + hoja nueva) en lugar de calcular a mano fuera del sistema.
- Todo documento lleva la advertencia de que es preliminar y debe revisarlo y firmarlo técnico competente.
