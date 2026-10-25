"""Optimización: busca la solución que CUMPLE todas las comprobaciones con el menor coste estimado.

Variables: dirección de viguetas, separación de viguetas, serie de vigas (IPE/HEB), canto de zapata.
Dentro de cada combinación, calculo.calcular ya elige la sección más ligera que cumple.
Precios unitarios orientativos (ejecución material, € sin IVA), editables en cfg["precios"].
"""
import copy
import itertools
import math

import calculo
import normativa as N

PRECIOS = {
    "acero_estructural": 2.60,   # €/kg suministrado, fabricado, montado e imprimado
    "madera_maciza": 650.0,      # €/m³ C18-C30 colocada
    "madera_laminada": 950.0,    # €/m³ GL colocada
    "hormigon": 115.0,           # €/m³ HA en cimentación, vertido
    "hormigon_limpieza": 85.0,   # €/m³
    "acero_armado": 1.40,        # €/kg B500S colocado
    "excavacion": 30.0,          # €/m³ excavación de pozos y retirada
    "estribo": 6.0,              # €/ud colgador de vigueta
    "tablero": 22.0,             # €/m² (no depende de la solución, informativo)
}


def mediciones(cfg, r):
    pr = dict(PRECIOS, **cfg.get("precios", {}))
    xs, ys = cfg["geometria"]["luces_x"], cfg["geometria"]["luces_y"]
    Lj, Lb = r["Lj"], r["Lb"]
    s = cfg["forjado"]["separacion"]
    n_lin_vp = len(Lj) + 1
    n_pil = (len(xs) + 1) * (len(ys) + 1)
    kg = lambda pp: pp / 9.81e-3     # kN/m → kg/m
    med = {}
    # viguetas
    n_vig = sum(max(0, math.ceil(b / s) - 1) for b in Lb)
    Ltot_v = n_vig * sum(Lj)
    v = r["vigueta"]
    if "perfil" in v:
        med["acero_vigueta_kg"] = Ltot_v * kg(v["perfil"]["peso"])
    else:
        med["madera_m3"] = Ltot_v * v["b"] * v["h"] * 1e-6
    med["estribos_ud"] = 2 * n_vig * len(Lj)
    # vigas principales y zunchos
    acero = 0.0
    for clave, L in (("viga", sum(Lb) * n_lin_vp), ("zuncho", sum(Lj) * (len(Lb) + 1))):
        e = r[clave]
        if "perfil" in e:
            acero += L * kg(e["perfil"]["peso"])
        else:
            med["madera_m3"] = med.get("madera_m3", 0) + L * e["b"] * e["h"] * 1e-6
    p = r["pilar"]["perfil"]
    acero += n_pil * (r["H"] * kg(p["peso"]))
    pl = r["placa"]
    acero += n_pil * ((pl["a"] / 1000) ** 2 * pl["t"] / 1000 * 7850 + ((p["b"] + 60) / 1000) ** 2 * 0.010 * 7850)
    med["acero_kg"] = acero * 1.05 + med.pop("acero_vigueta_kg", 0)   # +5 % uniones y despuntes
    zp = r["zapata"]
    med["hormigon_m3"] = n_pil * zp["B"] ** 2 * zp["h"]
    med["limpieza_m3"] = n_pil * (zp["B"] + 0.1) ** 2 * 0.10
    med["excavacion_m3"] = n_pil * (zp["B"] + 0.2) ** 2 * (zp["prof"] + 0.10)
    lbar = zp["B"] - 2 * zp["rec"] + 2 * 0.15
    med["armado_kg"] = n_pil * 2 * zp["n"] * lbar * N.BARRAS[zp["phi"]] * 7.85e-3
    tipo_mad = N.MADERAS.get(cfg["forjado"]["material"], {}).get("tipo", "maciza")
    coste = (med["acero_kg"] * pr["acero_estructural"] + med.get("madera_m3", 0) * pr["madera_" + tipo_mad] +
             med["estribos_ud"] * pr["estribo"] + med["hormigon_m3"] * pr["hormigon"] +
             med["limpieza_m3"] * pr["hormigon_limpieza"] + med["excavacion_m3"] * pr["excavacion"] +
             med["armado_kg"] * pr["acero_armado"])
    return med, coste


def optimizar(cfg, verbose=False):
    """Devuelve (cfg_optimo, tabla_alternativas). Respeta lo que el usuario haya fijado en cfg."""
    opt = cfg.get("optimizacion", {})
    g = cfg["geometria"]
    dirs = [g["direccion_viguetas"]] if g.get("direccion_viguetas") and opt.get("fijar_direccion") else ["x", "y"]
    seps = opt.get("separaciones", [0.30, 0.40, 0.50, 0.60]) if not opt.get("fijar_separacion") else \
        [cfg["forjado"]["separacion"]]
    series = opt.get("series_vigas", ["IPE", "HEB"]) if not cfg.get("vigas", {}).get("perfil") and \
        cfg["materiales"]["vigas"] in N.ACEROS else [cfg.get("vigas", {}).get("serie", "IPE")]
    cantos = opt.get("cantos_zapata", [0.30, 0.35, 0.40, 0.50]) if not cfg["cimentacion"].get("canto_fijo") else \
        [cfg["cimentacion"]["canto"]]
    tabla = []
    for d, s, serie, h in itertools.product(dirs, seps, series, cantos):
        c = copy.deepcopy(cfg)
        c["geometria"]["direccion_viguetas"] = d
        c["forjado"]["separacion"] = s
        c.setdefault("vigas", {})["serie"] = serie
        c["cimentacion"]["canto"] = h
        if "profundidad" in cfg["cimentacion"]:
            c["cimentacion"]["profundidad"] = max(cfg["cimentacion"]["profundidad"], h + 0.20)
        try:
            r, _ = calculo.calcular(c)
        except (ValueError, StopIteration, TypeError) as ex:
            if verbose:
                print("descartada", d, s, serie, h, ex)
            continue
        if not r["ok"]:
            continue
        med, coste = mediciones(c, r)
        tabla.append(dict(direccion=d, separacion=s, serie=serie, canto=h, coste=coste, med=med,
                          vigueta=r["vigueta"]["seccion"], viga=r["viga"]["seccion"], pilar=r["pilar"]["seccion"],
                          zapata=f"{r['zapata']['B']:.2f}x{r['zapata']['h']:.2f}",
                          ratio_max=max(x["ratio"] for x in r["checks"]), cfg=c))
    if not tabla:
        raise ValueError("Ninguna combinación cumple: revisar geometría, materiales o terreno.")
    tabla.sort(key=lambda t: t["coste"])
    return tabla[0]["cfg"], tabla
