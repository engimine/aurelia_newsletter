#!/usr/bin/env python3
"""Genera planos (PDF) + memoria de cálculo (Markdown) + resultados (JSON) a partir de un
archivo de proyecto JSON.

Uso:  python3 generar.py proyecto.json [carpeta_salida] [--png] [--sin-optimizar]

Por defecto OPTIMIZA: prueba dirección y separación de viguetas, serie de vigas y canto de zapata
y se queda con la solución que cumple con menor coste (respetando lo que se fije en el JSON).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import calculo  # noqa: E402
import planos   # noqa: E402
import optimizacion  # noqa: E402


def _limpio(o):
    if isinstance(o, dict):
        return {str(k): _limpio(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_limpio(v) for v in o]
    if isinstance(o, float):
        return round(o, 4)
    return o


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        sys.exit(1)
    cfg = json.load(open(args[0], encoding="utf-8"))
    out = args[1] if len(args) > 1 else os.path.join(os.path.dirname(os.path.abspath(args[0])), "salida")
    os.makedirs(out, exist_ok=True)
    cod = cfg["proyecto"].get("codigo", "EST")
    tabla = None
    if "--sin-optimizar" not in sys.argv:
        cfg, tabla = optimizacion.optimizar(cfg)
    r, M = calculo.calcular(cfg)
    med, coste = optimizacion.mediciones(cfg, r)
    r["mediciones"], r["coste"] = med, coste
    M.h("11. Optimización y mediciones")
    if tabla:
        M.p(f"Se han analizado las combinaciones de dirección y separación de viguetas, serie de vigas y canto de "
            f"zapata; {len(tabla)} cumplen todas las comprobaciones. Se adopta la de menor coste estimado.")
        M.p("| # | Dir. | Sep. (m) | Vigueta | Viga | Pilar | Zapata | Aprov. máx. | Coste (€) |\n|---|---|---|---|---|---|---|---|---|")
        for i, t in enumerate(tabla[:8], 1):
            M.p(f"| {i} | {t['direccion'].upper()} | {t['separacion']:.2f} | {t['vigueta']} | {t['viga']} | {t['pilar']} | "
                f"{t['zapata']} | {t['ratio_max']:.2f} | {t['coste']:.0f} |")
        M.p(f"\nAhorro frente a la peor solución que también cumple: {tabla[-1]['coste'] - tabla[0]['coste']:.0f} € "
            f"({(1 - tabla[0]['coste'] / tabla[-1]['coste']) * 100:.0f} %).")
        r["optimizacion"] = [{k: v for k, v in t.items() if k not in ("cfg", "med")} for t in tabla[:8]]
        r["optimizacion_n"] = len(tabla)
        r["optimizacion_ahorro"] = tabla[-1]["coste"] - tabla[0]["coste"]
    M.p(f"Mediciones: acero estructural {med['acero_kg']:.0f} kg; madera {med.get('madera_m3', 0):.2f} m³; "
        f"hormigón {med['hormigon_m3']:.2f} m³; armadura {med['armado_kg']:.0f} kg; excavación {med['excavacion_m3']:.2f} m³. "
        f"Coste estimado de la estructura (PEM orientativo, precios editables): **{coste:.0f} €**.")
    res = {k: v for k, v in r.items() if k not in ("pilares_N",)}
    res["pilares_N"] = {f"{i},{j}": v for (i, j), v in r["pilares_N"].items()}
    if "geotecnia" in res:
        res["geotecnia"] = {k: v for k, v in res["geotecnia"].items()}
    res["zapata"] = {k: v for k, v in r["zapata"].items() if k != "geo"}
    for k in ("viga", "zuncho", "vigueta", "pilar"):
        res[k] = {kk: vv for kk, vv in r[k].items() if kk != "perfil"}
    with open(os.path.join(out, f"{cod}_resultados.json"), "w", encoding="utf-8") as f:
        json.dump(_limpio(res), f, ensure_ascii=False, indent=1)
    png = os.path.join(out, "png") if "--png" in sys.argv else None
    if png:
        os.makedirs(png, exist_ok=True)
    pdf = os.path.join(out, f"{cod}_planos_estructura.pdf")
    planos.generar_pdf(cfg, r, M, pdf, png)
    with open(os.path.join(out, f"{cod}_memoria_calculo.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(M.lineas))
    with open(os.path.join(out, f"{cod}_proyecto_optimizado.json"), "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=1)
    n_no = sum(1 for c in r["checks"] if not c["cumple"])
    print(f"Vigueta {r['vigueta']['seccion']} | VP {r['viga']['seccion']} | ZU {r['zuncho']['seccion']} | "
          f"Pilar {r['pilar']['seccion']} | Zapata {r['zapata']['B']:.2f}x{r['zapata']['B']:.2f}x{r['zapata']['h']:.2f}")
    print(f"Comprobaciones: {len(r['checks'])}, no cumplen: {n_no} | coste estimado {coste:.0f} €"
          + (f" | {len(tabla)} alternativas válidas, ahorro {r['optimizacion_ahorro']:.0f} €" if tabla else ""))
    print(f"PDF: {pdf}")


if __name__ == "__main__":
    main()
