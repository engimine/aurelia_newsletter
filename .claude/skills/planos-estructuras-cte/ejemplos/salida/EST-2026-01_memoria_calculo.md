
# MEMORIA DE CÁLCULO DE ESTRUCTURA — ENTREPLANTA EN SALÓN DE VIVIENDA

Estructura metálica con forjado de madera · C/ Ejemplo 1, 43550 Ulldecona (Tarragona)

## 0. Normativa y método

CTE DB-SE (Seguridad estructural), DB-SE-AE (Acciones), DB-SE-A (Acero), DB-SE-M (Madera), DB-SE-C (Cimientos), DB-SI 6 (Resistencia al fuego de la estructura); Código Estructural (RD 470/2021) para el hormigón armado; NCSE-02 (sismo). Método de los estados límite (DB-SE 3.2).
Esquema: viguetas biapoyadas en dirección X (vanos 3.30 m) entre vigas principales biapoyadas (vanos 4.40 m) sobre pilares de altura 2.45 m. Uniones viga-pilar articuladas.

## 1. Acciones (DB-SE-AE)

| Acción | Valor | Referencia |
|---|---|---|
| Tablero estructural OSB/contrachapado 22 mm | 0.15 kN/m² | DB-SE-AE Anejo C |
| Pavimento ligero | 0.50 kN/m² | DB-SE-AE Anejo C |
| Falso techo de placa de yeso | 0.15 kN/m² | DB-SE-AE Anejo C |
| Instalaciones | 0.10 kN/m² | DB-SE-AE Anejo C |
| **Total cargas permanentes (sin peso propio de la estructura)** | **0.90 kN/m²** | |
| Sobrecarga de uso, categoría A1 (Viviendas y zonas de habitaciones en hospitales y hoteles) | 2.00 kN/m² | DB-SE-AE tabla 3.1 |
| Carga concentrada (independiente) | 2.0 kN | DB-SE-AE tabla 3.1 |
| Fuerza horizontal en barandilla | 0.8 kN/m | DB-SE-AE tabla 3.3 |

Coeficientes de simultaneidad (DB-SE tabla 4.2): ψ0 = 0.7, ψ1 = 0.5, ψ2 = 0.3.
Coeficientes parciales (DB-SE tabla 4.1): γG = 1.35, γQ = 1.5.
Combinaciones: ELU persistente 1,35·G + 1,50·Q; ELS característica G + Q; casi permanente G + ψ2·Q.
Nieve y viento no actúan (estructura interior). Sismo: ver apartado NCSE-02.

## 2. Viguetas (DB-SE-M)

Vigueta tipo: separación 60 cm, luz de cálculo 3.30 m (entre ejes, del lado de la seguridad).
Sección 70×195 mm, C24 (maciza); L = 3.30 m; clase de servicio 1; kmod = 0.8 (carga de duración media); γM = 1.3; kh = 1.000.
Cargas: g,pp = 0.146 kN/m, g,post = 0.450 kN/m, q = 1.200 kN/m → qd = 1,35·g + 1,5·q = 2.605 kN/m; Md = 3.55 kN·m; Vd = 4.30 kN.
- **ELU flexión σm,d ≤ fm,d**: 7.99 MPa / 14.8 MPa = **0.54** ✔ CUMPLE  _(DB-SE-M 6.1.6)_
- **ELU cortante τd ≤ fv,d**: 0.472 MPa / 1.54 MPa = **0.31** ✔ CUMPLE  _(DB-SE-M 6.1.8)_
- **ELU carga concentrada 2 kN en centro de vano**: 8.05 MPa / 16.6 MPa = **0.48** ✔ CUMPLE  _(DB-SE-AE 3.1.1(2), DB-SE-M 6.1.6)_
Vuelco lateral: canto/ancho ≤ 4 y cara comprimida arriostrada por el tablero → kcrit = 1 (DB-SE-M 6.3.3).
Flechas instantáneas: δG,pp = 0.47 mm, δG,post = 1.46 mm, δQ = 3.89 mm; fluencia kdef = 0.6 (DB-SE-M 5.1).
- **ELS integridad (flecha activa ≤ L/400)**: 7.22 mm / 8.25 mm = **0.87** ✔ CUMPLE  _(DB-SE 4.3.3.1)_
- **ELS confort (δQ ≤ L/350)**: 3.89 mm / 9.43 mm = **0.41** ✔ CUMPLE  _(DB-SE 4.3.3.1)_
- **ELS apariencia (casi perm. ≤ L/300)**: 4.97 mm / 11 mm = **0.45** ✔ CUMPLE  _(DB-SE 4.3.3.1)_
Reacción de cálculo de vigueta: Rd = 4.30 kN → estribo/colgador metálico con ETA y capacidad ≥ 4.3 kN (o apoyo directo sobre ala con fijación).

## 3. Vigas principales (DB-SE-A)

Ancho tributario máximo = 1.65 m (vigas interiores = media de vanos adyacentes; de borde = medio vano). Se incluye peso de viguetas (0.09 kN/m²) y barandilla (0.30 kN/m) en vigas de borde.
Forjado enrasado: canto de viga principal ≥ canto de vigueta (195 mm).
Perfil IPE 200 (S275, fy = 275 MPa); L = 4.40 m; clase 1 en flexión (IPE/HEB laminados).
A = 28.3 cm², Iy = 1940 cm⁴, Wpl,y = 220.0 cm³, Av = 13.8 cm², peso propio = 0.218 kN/m.
Cargas: g,pp = 0.920 kN/m, g,post = 1.237 kN/m, q = 3.300 kN/m → qd = 7.863 kN/m; Md = 19.03 kN·m; Vd = 17.30 kN.
Pandeo lateral impedido: ala comprimida arriostrada de forma continua por viguetas y tablero (DB-SE-A 6.3.3.2).
- **ELU flexión Md ≤ χLT·Mpl,Rd**: 19 kN·m / 57.6 kN·m = **0.33** ✔ CUMPLE  _(DB-SE-A 6.2.6 / 6.3.3)_
- **ELU cortante Vd ≤ Vpl,Rd**: 17.3 kN / 209 kN = **0.08** ✔ CUMPLE  _(DB-SE-A 6.2.4)_
Flechas instantáneas: δG,pp = 1.10 mm, δG,post = 1.48 mm, δQ = 3.95 mm.
- **ELS integridad (flecha activa ≤ L/400)**: 5.44 mm / 11 mm = **0.49** ✔ CUMPLE  _(DB-SE 4.3.3.1)_
- **ELS confort (δQ ≤ L/350)**: 3.95 mm / 12.6 mm = **0.31** ✔ CUMPLE  _(DB-SE 4.3.3.1)_
- **ELS apariencia (casi perm. ≤ L/300)**: 3.77 mm / 14.7 mm = **0.26** ✔ CUMPLE  _(DB-SE 4.3.3.1)_

## 4. Zunchos de borde

Perfil IPE 200 (S275, fy = 275 MPa); L = 3.30 m; clase 1 en flexión (IPE/HEB laminados).
A = 28.3 cm², Iy = 1940 cm⁴, Wpl,y = 220.0 cm³, Av = 13.8 cm², peso propio = 0.218 kN/m.
Cargas: g,pp = 0.591 kN/m, g,post = 0.225 kN/m, q = 0.600 kN/m → qd = 2.002 kN/m; Md = 2.73 kN·m; Vd = 3.30 kN.
Pandeo lateral impedido: ala comprimida arriostrada de forma continua por viguetas y tablero (DB-SE-A 6.3.3.2).
- **ELU flexión Md ≤ χLT·Mpl,Rd**: 2.73 kN·m / 57.6 kN·m = **0.05** ✔ CUMPLE  _(DB-SE-A 6.2.6 / 6.3.3)_
- **ELU cortante Vd ≤ Vpl,Rd**: 3.3 kN / 209 kN = **0.02** ✔ CUMPLE  _(DB-SE-A 6.2.4)_
Flechas instantáneas: δG,pp = 0.22 mm, δG,post = 0.09 mm, δQ = 0.23 mm.
- **ELS integridad (flecha activa ≤ L/400)**: 0.313 mm / 8.25 mm = **0.04** ✔ CUMPLE  _(DB-SE 4.3.3.1)_
- **ELS confort (δQ ≤ L/350)**: 0.227 mm / 9.43 mm = **0.02** ✔ CUMPLE  _(DB-SE 4.3.3.1)_
- **ELS apariencia (casi perm. ≤ L/300)**: 0.378 mm / 11 mm = **0.03** ✔ CUMPLE  _(DB-SE 4.3.3.1)_

## 5. Pilares (DB-SE-A)

Pilar más cargado: alineación (0, 0). NG = 6.1 kN, NQ = 8.2 kN.
Estabilidad lateral: Hd = max(imperfección ΣNd/200 = 0.41 kN; barandilla 1,5·0.8 kN/m·L = 5.28 kN) = 5.28 kN, resistida mediante anclaje del forjado al muro existente.
Esbeltez de pared c/t = 17.0 → clase 1 (límites 33ε/38ε/42ε, ε = 0.92).
Perfil SHS 80x4 (S275); H = 2.45 m; base empotrada; β = 0.7 → Lk = 1.72 m; i = 30.7 mm; λ̄ = 0.64; curva c; χ = 0.760.
Nd = 1,35·(NG + pp) + 1,5·NQ = 20.9 kN; Nb,Rd = χ·A·fy/γM1 = 233.8 kN; Md = 2.42 kN·m (excentricidad de apoyo de vigas / acción horizontal); MRd = 8.66 kN·m.
- **ELU pandeo por compresión Nd ≤ Nb,Rd**: 20.9 kN / 234 kN = **0.09** ✔ CUMPLE  _(DB-SE-A 6.3.2)_
- **ELU interacción N + M (cm = 0,9)**: 0.35 - / 1 - = **0.35** ✔ CUMPLE  _(DB-SE-A 6.3.4.2 (simplificada))_
Anclaje a muro: 8 anclajes c/60 cm en 4.40 m; Vd por anclaje = 0.66 kN (comprobar con ETA del anclaje en la fábrica existente).

## 6. Placa de anclaje (DB-SE-A 8.8)

Placa 200×200×10 mm (S275); fjd = βj·kj·fcd = 16.7 MPa; σ = Nd/A = 0.52 MPa; vuelo c = 60 mm → t,req = c·√(3σγM0/fy) = 4.6 mm.
- **ELU presión bajo placa σ ≤ fjd**: 0.523 MPa / 16.7 MPa = **0.03** ✔ CUMPLE  _(DB-SE-A 8.8.1)_
- **ELU flexión de placa t,req ≤ t = 10 mm**: 4.64 mm / 10 mm = **0.46** ✔ CUMPLE  _(DB-SE-A 8.8.1)_
- **ELU soldadura pilar-placa en ángulo a = 4 mm perimetral**: 20.9 kN / 285 kN = **0.07** ✔ CUMPLE  _(DB-SE-A 8.6.2)_
Anclaje: 4 M16 barra roscada 8.8 con anclaje químico (ETA), L,emb ≥ 125 mm. Bajo cargas gravitatorias no hay tracción; el anclaje se dimensiona con el software del fabricante (ETA) para el cortante horizontal Hd indicado en la estabilidad lateral.

## 7. Cimentación (DB-SE-C, Código Estructural)


### 7.0 Información geotécnica

Fuente: **sin estudio geotécnico**; terreno estimado a partir de la geología del emplazamiento (Mapa Geológico MAGNA 1:50.000, IGME (visor info.igme.es)). Valores de PREDIMENSIONADO: el estudio geotécnico es preceptivo (DB-SE-C 3.1) y debe confirmarlos antes de la ejecución.
> ⚠ Depósitos heterogéneos: comprobar la homogeneidad del apoyo en todas las zapatas.
Tipo de construcción **C-0** (DB-SE-C tabla 3.1: 1 planta(s), 15 m²). Grupo de terreno **T-2** (estimado según la litología, DB-SE-C tabla 3.2).
Exigencias orientativas: distancia máx. entre puntos 30 m, profundidad 18 m (tabla 3.3); ≥ 3 puntos de reconocimiento, ≥ 2 sondeo(s) mecánico(s) con sustitución por penetrómetros hasta el 70 % (tabla 3.4).
> ⚠ No se aporta el detalle del reconocimiento (puntos, sondeos, profundidad).
Agresividad: SO₄ suelo = n/d mg/kg, agua = n/d mg/l → clase de exposición **IIa**: a/c ≤ 0.6, cemento ≥ 275 kg/m³, resistencia mínima HA-25.

### 7.1 Terreno de cimentación

Litología: **Glacis, coluviales y costras calcáreas (Cuaternario)**. Parámetros característicos estimados (rango inferior): γ = 19 kN/m³, φ' = 30°, c' = 5 kPa, N_SPT ≈ 15.
Hundimiento Brinch-Hansen (largo plazo (drenado)): qh = 774 kPa → qh/γR = 258 kPa. Asiento (Burland y Burbidge (DB-SE-C F.2)) ≤ 25 mm → 937 kPa. Tope orientativo tabla D.25: 200 kPa.
**σadm estimada = 200 kPa** (rige tabla D.25).

### 7.2 Zapata

Zapata cuadrada 0.60×0.60×0.30 m, cota de apoyo −0.60 m; HA: fck = 25 MPa; armadura fyk = 500 MPa; σadm = 200 kPa.
Nk = 14.6 kN; peso zapata + tierras = 4.9 kN; Mk = 0.00 kN·m → e = 0.0 cm.
- **Tensión media σmed ≤ σadm**: 54 kPa / 200 kPa = **0.27** ✔ CUMPLE  _(DB-SE-C 4.3)_
- **Tensión de borde σmax ≤ 1,25·σadm**: 54 kPa / 250 kPa = **0.22** ✔ CUMPLE  _(DB-SE-C 4.3)_
- **ELS asiento total s ≤ s,adm**: 1.16 mm / 25 mm = **0.05** ✔ CUMPLE  _(DB-SE-C 4.2.2.3 / anejo F.2)_
- **ELS distorsión angular β ≤ 1/500**: 0.000176 - / 0.002 - = **0.09** ✔ CUMPLE  _(DB-SE-C tabla 2.2)_
Vuelo v = 0.20 m ≤ 2h = 0.60 m → zapata RÍGIDA; canto útil d = 0.242 m; Nd = 20.9 kN.
Método de bielas y tirantes: Td = Nd·(a − a0)/(6,8·d) = 5.1 kN; As = Td/fyd = 13 mm² (fyd ≤ 400 MPa).
- **Armadura inferior por dirección: 3Ø12 c/25 cm**: 162 mm² / 339 mm² = **0.48** ✔ CUMPLE  _(Código Estructural (bielas y tirantes, cuantía mínima))_
As,min geométrica = 0.9 ‰ · B · h = 162 mm²; Ø ≥ 12 mm y separación ≤ 30 cm.
- **Compresión localizada bajo placa**: 20.9 kN / 2e+03 kN = **0.01** ✔ CUMPLE  _(Código Estructural art. 61)_

## 8. Uniones

Reacción de cálculo de viga principal Rd = 17.3 kN.
- **2 tornillos M16 8.8 a cortante (1 plano)**: 17.3 kN / 121 kN = **0.14** ✔ CUMPLE  _(DB-SE-A 8.5.2.2)_
- **Aplastamiento en chapa de 8 mm**: 17.3 kN / 210 kN = **0.08** ✔ CUMPLE  _(DB-SE-A 8.5.2.2)_

## 9. Acción sísmica (NCSE-02) y resistencia al fuego (DB-SI 6)

ab = 0.04g < 0,08g, construcción de importancia normal con pórticos bien arriostrados → exenta de la NCSE-02 (art. 1.2.3).
Resistencia al fuego exigida: R 30 (DB-SI 6, tabla 3.1). Acero: protección con pintura intumescente o placa según certificado; madera: comprobación por sección reducida (DB-SI anejo E).

## 10. Resumen de comprobaciones

| Elemento | Comprobación | Demanda | Capacidad | Aprov. | Estado |
|---|---|---|---|---|---|
| Vigueta | ELU flexión σm,d ≤ fm,d | 7.99 MPa | 14.8 MPa | 0.54 | CUMPLE |
| Vigueta | ELU cortante τd ≤ fv,d | 0.472 MPa | 1.54 MPa | 0.31 | CUMPLE |
| Vigueta | ELU carga concentrada 2 kN en centro de vano | 8.05 MPa | 16.6 MPa | 0.48 | CUMPLE |
| Vigueta | ELS integridad (flecha activa ≤ L/400) | 7.22 mm | 8.25 mm | 0.87 | CUMPLE |
| Vigueta | ELS confort (δQ ≤ L/350) | 3.89 mm | 9.43 mm | 0.41 | CUMPLE |
| Vigueta | ELS apariencia (casi perm. ≤ L/300) | 4.97 mm | 11 mm | 0.45 | CUMPLE |
| Viga principal | ELU flexión Md ≤ χLT·Mpl,Rd | 19 kN·m | 57.6 kN·m | 0.33 | CUMPLE |
| Viga principal | ELU cortante Vd ≤ Vpl,Rd | 17.3 kN | 209 kN | 0.08 | CUMPLE |
| Viga principal | ELS integridad (flecha activa ≤ L/400) | 5.44 mm | 11 mm | 0.49 | CUMPLE |
| Viga principal | ELS confort (δQ ≤ L/350) | 3.95 mm | 12.6 mm | 0.31 | CUMPLE |
| Viga principal | ELS apariencia (casi perm. ≤ L/300) | 3.77 mm | 14.7 mm | 0.26 | CUMPLE |
| Zuncho | ELU flexión Md ≤ χLT·Mpl,Rd | 2.73 kN·m | 57.6 kN·m | 0.05 | CUMPLE |
| Zuncho | ELU cortante Vd ≤ Vpl,Rd | 3.3 kN | 209 kN | 0.02 | CUMPLE |
| Zuncho | ELS integridad (flecha activa ≤ L/400) | 0.313 mm | 8.25 mm | 0.04 | CUMPLE |
| Zuncho | ELS confort (δQ ≤ L/350) | 0.227 mm | 9.43 mm | 0.02 | CUMPLE |
| Zuncho | ELS apariencia (casi perm. ≤ L/300) | 0.378 mm | 11 mm | 0.03 | CUMPLE |
| Pilar | ELU pandeo por compresión Nd ≤ Nb,Rd | 20.9 kN | 234 kN | 0.09 | CUMPLE |
| Pilar | ELU interacción N + M (cm = 0,9) | 0.35 - | 1 - | 0.35 | CUMPLE |
| Placa base | ELU presión bajo placa σ ≤ fjd | 0.523 MPa | 16.7 MPa | 0.03 | CUMPLE |
| Placa base | ELU flexión de placa t,req ≤ t = 10 mm | 4.64 mm | 10 mm | 0.46 | CUMPLE |
| Placa base | ELU soldadura pilar-placa en ángulo a = 4 mm perimetral | 20.9 kN | 285 kN | 0.07 | CUMPLE |
| Zapata | Tensión media σmed ≤ σadm | 54 kPa | 200 kPa | 0.27 | CUMPLE |
| Zapata | Tensión de borde σmax ≤ 1,25·σadm | 54 kPa | 250 kPa | 0.22 | CUMPLE |
| Zapata | ELS asiento total s ≤ s,adm | 1.16 mm | 25 mm | 0.05 | CUMPLE |
| Zapata | ELS distorsión angular β ≤ 1/500 | 0.000176 - | 0.002 - | 0.09 | CUMPLE |
| Zapata | Armadura inferior por dirección: 3Ø12 c/25 cm | 162 mm² | 339 mm² | 0.48 | CUMPLE |
| Zapata | Compresión localizada bajo placa | 20.9 kN | 2e+03 kN | 0.01 | CUMPLE |
| Unión viga-pilar | 2 tornillos M16 8.8 a cortante (1 plano) | 17.3 kN | 121 kN | 0.14 | CUMPLE |
| Unión viga-pilar | Aplastamiento en chapa de 8 mm | 17.3 kN | 210 kN | 0.08 | CUMPLE |

**Resultado global: TODAS LAS COMPROBACIONES CUMPLEN.**

> Documento técnico preliminar generado con ayuda de IA. Debe ser revisado, completado y firmado por técnico competente antes de su uso en proyecto, licencia u obra.

## 11. Optimización y mediciones

Se han analizado las combinaciones de dirección y separación de viguetas, serie de vigas y canto de zapata; 64 cumplen todas las comprobaciones. Se adopta la de menor coste estimado.
| # | Dir. | Sep. (m) | Vigueta | Viga | Pilar | Zapata | Aprov. máx. | Coste (€) |
|---|---|---|---|---|---|---|---|---|
| 1 | X | 0.60 | 70x195 C24 | IPE 200 | SHS 80x4 | 0.60x0.30 | 0.87 | 1665 |
| 2 | X | 0.60 | 70x195 C24 | IPE 200 | SHS 80x4 | 0.60x0.35 | 0.87 | 1674 |
| 3 | X | 0.60 | 70x195 C24 | IPE 200 | SHS 80x4 | 0.60x0.40 | 0.87 | 1682 |
| 4 | X | 0.40 | 45x195 C24 | IPE 200 | SHS 80x4 | 0.60x0.30 | 0.91 | 1685 |
| 5 | X | 0.40 | 45x195 C24 | IPE 200 | SHS 80x4 | 0.60x0.35 | 0.91 | 1693 |
| 6 | X | 0.40 | 45x195 C24 | IPE 200 | SHS 80x4 | 0.60x0.40 | 0.91 | 1701 |
| 7 | X | 0.60 | 70x195 C24 | IPE 200 | SHS 80x4 | 0.60x0.50 | 0.87 | 1706 |
| 8 | X | 0.50 | 70x195 C24 | IPE 200 | SHS 80x4 | 0.60x0.30 | 0.73 | 1707 |

Ahorro frente a la peor solución que también cumple: 3119 € (65 %).
Mediciones: acero estructural 474 kg; madera 0.32 m³; hormigón 0.43 m³; armadura 17 kg; excavación 1.79 m³. Coste estimado de la estructura (PEM orientativo, precios editables): **1665 €**.