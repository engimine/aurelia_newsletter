#!/usr/bin/env python3
"""Genera planos (PDF) + memoria de cálculo (Markdown) + resultados (JSON) a partir de un
archivo de proyecto JSON.

Uso:  python3 generar.py proyecto.json [carpeta_salida] [--png]
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import calculo  # noqa: E402
import planos   # noqa: E402


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
    r, M = calculo.calcular(cfg)
    with open(os.path.join(out, f"{cod}_memoria_calculo.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(M.lineas))
    res = {k: v for k, v in r.items() if k not in ("pilares_N",)}
    res["pilares_N"] = {f"{i},{j}": v for (i, j), v in r["pilares_N"].items()}
    for k in ("viga", "zuncho", "vigueta", "pilar"):
        res[k] = {kk: vv for kk, vv in r[k].items() if kk != "perfil"}
    with open(os.path.join(out, f"{cod}_resultados.json"), "w", encoding="utf-8") as f:
        json.dump(_limpio(res), f, ensure_ascii=False, indent=1)
    png = os.path.join(out, "png") if "--png" in sys.argv else None
    if png:
        os.makedirs(png, exist_ok=True)
    pdf = os.path.join(out, f"{cod}_planos_estructura.pdf")
    planos.generar_pdf(cfg, r, M, pdf, png)
    n_no = sum(1 for c in r["checks"] if not c["cumple"])
    print(f"Vigueta {r['vigueta']['seccion']} | VP {r['viga']['seccion']} | ZU {r['zuncho']['seccion']} | "
          f"Pilar {r['pilar']['seccion']} | Zapata {r['zapata']['B']:.2f}x{r['zapata']['B']:.2f}x{r['zapata']['h']:.2f}")
    print(f"Comprobaciones: {len(r['checks'])}, no cumplen: {n_no}")
    print(f"PDF: {pdf}")


if __name__ == "__main__":
    main()
