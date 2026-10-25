"""Análisis geotécnico para cimentación directa según CTE DB-SE-C.

- Clasificación: tipo de construcción (tabla 3.1) y grupo de terreno (tabla 3.2).
- Suficiencia del reconocimiento (tablas 3.3 y 3.4, apartado 3.2).
- Carga de hundimiento de Brinch-Hansen (anejo F.1) con γR = 3,0 (tabla 2.1).
- Asientos: Burland y Burbidge en granulares (anejo F.2), elástico en cohesivos y roca.
- Agresividad química del terreno/agua (Código Estructural, clases de exposición Qa/Qb/Qc).
- Sin estudio: presión admisible orientativa (tabla D.25) — sólo para predimensionado.
Unidades: kN, m, kPa.
"""
import math

GAMMA_R_HUNDIMIENTO = 3.0   # DB-SE-C tabla 2.1, situación persistente
GAMMA_W = 9.81

# DB-SE-C tabla 3.3: distancia máxima entre puntos (m) y profundidad orientativa (m) por (tipo, grupo)
TABLA_3_3 = {
    ("C-0", "T-1"): (35, 6), ("C-0", "T-2"): (30, 18), ("C-1", "T-1"): (35, 6), ("C-1", "T-2"): (30, 18),
    ("C-2", "T-1"): (30, 12), ("C-2", "T-2"): (25, 25), ("C-3", "T-1"): (25, 14), ("C-3", "T-2"): (20, 30),
    ("C-4", "T-1"): (20, 16), ("C-4", "T-2"): (17, 35),
}
# DB-SE-C tabla 3.4: nº mínimo de sondeos y % de sustitución por pruebas continuas de penetración
TABLA_3_4 = {
    ("C-0", "T-1"): (1, 70), ("C-0", "T-2"): (2, 70), ("C-1", "T-1"): (1, 70), ("C-1", "T-2"): (3, 50),
    ("C-2", "T-1"): (2, 50), ("C-2", "T-2"): (3, 40), ("C-3", "T-1"): (3, 40), ("C-3", "T-2"): (3, 30),
    ("C-4", "T-1"): (3, 40), ("C-4", "T-2"): (3, 30),
}
PUNTOS_MINIMOS = 3  # DB-SE-C 3.2: número mínimo de puntos de reconocimiento

# DB-SE-C tabla D.25: presiones admisibles a efectos orientativos (kPa) — se adopta el límite inferior
PRESION_ORIENTATIVA = {
    "roca_ignea_sana": (10000, "Rocas ígneas y metamórficas sanas"),
    "roca_foliada_sana": (3000, "Rocas metamórficas foliadas sanas"),
    "roca_sedimentaria_sana": (1000, "Rocas sedimentarias sanas (areniscas, calizas no karstificadas, conglomerados cementados)"),
    "roca_arcillosa_sana": (500, "Rocas arcillosas sanas"),
    "grava_densa": (600, "Gravas y mezclas arena-grava densas"),
    "grava_media": (200, "Gravas y mezclas arena-grava medianamente densas a sueltas"),
    "arena_densa": (300, "Arenas y mezclas arena-grava densas"),
    "arena_media": (100, "Arenas medianamente densas a sueltas"),
    "arcilla_dura": (300, "Arcillas duras"),
    "arcilla_muy_firme": (200, "Arcillas muy firmes"),
    "arcilla_firme": (100, "Arcillas firmes"),
    "arcilla_blanda": (75, "Arcillas blandas"),
}

# Código Estructural: ataque por sulfatos (suelo mg/kg; agua mg/l) → clase específica de exposición
def clase_quimica(so4_suelo=None, so4_agua=None):
    nivel = 0
    if so4_suelo is not None:
        nivel = max(nivel, 3 if so4_suelo > 12000 else 2 if so4_suelo > 3000 else 1 if so4_suelo >= 2000 else 0)
    if so4_agua is not None:
        nivel = max(nivel, 3 if so4_agua > 3000 else 2 if so4_agua > 600 else 1 if so4_agua >= 200 else 0)
    return [None, "Qa", "Qb", "Qc"][nivel]

# Requisitos de durabilidad (a/c máx., cemento mín. kg/m³, resistencia mín.) — Código Estructural
DURABILIDAD = {"IIa": (0.60, 275, "HA-25"), "Qa": (0.50, 325, "HA-30"), "Qb": (0.50, 350, "HA-30"),
               "Qc": (0.45, 350, "HA-35")}


def tipo_construccion(plantas, superficie_m2):
    """DB-SE-C tabla 3.1."""
    if plantas > 20:
        return "C-4"
    if plantas > 10:
        return "C-3"
    if plantas >= 4:
        return "C-2"
    return "C-0" if superficie_m2 < 300 else "C-1"


def grupo_terreno(g):
    """DB-SE-C tabla 3.2. T-3 si hay alguna condición desfavorable declarada."""
    if g.get("grupo_terreno"):
        return g["grupo_terreno"], "indicado en el estudio"
    if g.get("grupo_terreno_geologia"):
        return g["grupo_terreno_geologia"], "estimado según la litología"
    malos = [k for k in ("expansivo", "colapsable", "blando_suelto", "karstico", "relleno_mayor_3m", "inundable",
                         "inestable", "pendiente_mayor_15") if g.get(k)]
    if malos:
        return "T-3", "condiciones desfavorables: " + ", ".join(malos)
    if g.get("relleno_antropico") or g.get("variabilidad"):
        return "T-2", "terreno intermedio (variabilidad o rellenos < 3 m)"
    return "T-1", "terreno favorable (poca variabilidad)"


def _estrato(estratos, z):
    for e in estratos:
        if e["desde"] <= z < e["hasta"]:
            return e
    return estratos[-1]


def _tension_efectiva(estratos, z, nf):
    s = 0.0
    zz = 0.0
    while zz < z - 1e-9:
        e = _estrato(estratos, zz)
        dz = min(e["hasta"], z) - zz
        g = e.get("gamma", 19.0)
        if nf is not None and zz >= nf:
            g = e.get("gamma_sat", g + 1.0) - GAMMA_W
        elif nf is not None and zz + dz > nf:
            dz = nf - zz
        s += g * dz
        zz += dz
    return s


def hundimiento(estratos, B, L, D, nf, e_B=0.0, e_L=0.0, carga_inclinada=0.0):
    """Brinch-Hansen (DB-SE-C anejo F.1). Devuelve (qh kPa, detalle dict). B, L, D en m."""
    Bs, Ls = B - 2 * e_B, L - 2 * e_L          # dimensiones equivalentes (Meyerhof)
    e = _estrato(estratos, D + 0.01)
    gamma = e.get("gamma", 19.0)
    if nf is not None and nf <= D + Bs:
        gamma = e.get("gamma_sat", gamma + 1.0) - GAMMA_W   # nivel freático en la zona de influencia
    q0 = _tension_efectiva(estratos, D, nf)
    BL = Bs / Ls
    k = math.atan(min(D / Bs, 2.0)) if D / Bs > 1 else D / Bs
    corto = e.get("tipo") == "cohesivo" and e.get("cu")
    if corto:  # corto plazo, sin drenaje (φ = 0)
        cu = e["cu"]
        sc, dc = 1 + 0.2 * BL, 1 + 0.34 * k
        qh = 5.14 * cu * sc * dc + q0
        det = dict(condicion="corto plazo (φ=0)", cu=cu, Nc=5.14, sc=sc, dc=dc, q0=q0, Bs=Bs, Ls=Ls, qh=qh)
    else:
        phi = math.radians(e.get("phi", 30.0))
        c = e.get("c", 0.0)
        Nq = math.exp(math.pi * math.tan(phi)) * math.tan(math.pi / 4 + phi / 2) ** 2
        Nc = (Nq - 1) / math.tan(phi) if phi > 0 else 5.14
        Ng = 1.5 * (Nq - 1) * math.tan(phi)
        sc = 1 + 0.2 * BL
        sq = 1 + 1.5 * math.tan(phi) * BL
        sg = 1 - 0.3 * BL
        dq = 1 + 2 * math.tan(phi) * (1 - math.sin(phi)) ** 2 * k
        dc = 1 + 2 * (Nq / Nc) * (1 - math.sin(phi)) ** 2 * k if phi > 0 else 1 + 0.34 * k
        iq = ic = ig = 1.0
        if carga_inclinada:  # tan δ = H/V
            t = carga_inclinada
            iq, ic, ig = (1 - 0.7 * t) ** 3, (1 - 0.7 * t) ** 3, (1 - t) ** 3
        qh = c * Nc * sc * dc * ic + q0 * Nq * sq * dq * iq + 0.5 * Bs * gamma * Ng * sg * ig
        det = dict(condicion="largo plazo (drenado)", phi=math.degrees(phi), c=c, Nq=Nq, Nc=Nc, Ng=Ng,
                   sc=sc, sq=sq, sg=sg, dc=dc, dq=dq, q0=q0, gamma=gamma, Bs=Bs, Ls=Ls, qh=qh)
    return qh, det


def asiento(estratos, B, L, D, q_neta, nf):
    """Asiento en mm bajo presión neta q_neta (kPa)."""
    e = _estrato(estratos, D + 0.01)
    if e.get("tipo") == "granular" and e.get("nspt"):
        N = e["nspt"]
        if nf is not None and nf <= D + B and N > 15:
            N = 15 + 0.5 * (N - 15)          # corrección de Terzaghi para arenas finas bajo NF
        Ic = 1.71 / N ** 1.4
        fs = (1.25 * (L / B) / (L / B + 0.25)) ** 2
        zi = B ** 0.763                      # profundidad de influencia (N creciente con la profundidad)
        s = fs * q_neta * B ** 0.7 * Ic
        return s, dict(metodo="Burland y Burbidge (DB-SE-C F.2)", N=N, Ic=Ic, fs=fs, zi=zi)
    E = e.get("E")
    if not E:
        if e.get("cu"):
            E = 300 * e["cu"]                # orientativo: E ≈ 300·cu (arcillas normalmente consolidadas)
        elif e.get("nspt"):
            E = 1000 * e["nspt"] * 0.7       # orientativo: E (kPa) ≈ 700·N
        else:
            E = 20000
    nu = e.get("nu", 0.3)
    Is = 0.82 if abs(L - B) < 1e-6 else 0.82 + 0.15 * math.log(L / B)   # zapata rígida (Steinbrenner aprox.)
    s = q_neta * B * (1 - nu ** 2) * Is / E * 1000
    return s, dict(metodo="elástico (zapata rígida)", E=E, nu=nu, Is=Is)


def analizar_reconocimiento(M, cfg, B, D):
    """Clasificación y suficiencia del estudio. Devuelve dict con tipo, grupo y avisos."""
    g = cfg.get("geotecnia", {})
    plantas = cfg.get("plantas", 1)
    sup = cfg.get("superficie_construida", sum(cfg["geometria"]["luces_x"]) * sum(cfg["geometria"]["luces_y"]))
    tc = g.get("tipo_construccion") or tipo_construccion(plantas, sup)
    gt, motivo = grupo_terreno(g)
    M.p(f"Tipo de construcción **{tc}** (DB-SE-C tabla 3.1: {plantas} planta(s), {sup:.0f} m²). "
        f"Grupo de terreno **{gt}** ({motivo}, DB-SE-C tabla 3.2).")
    avisos = []
    if gt == "T-3":
        avisos.append("Terreno T-3 (desfavorable): el reconocimiento y la solución de cimentación deben "
                      "estudiarse de forma específica (DB-SE-C 3.2). Valorar cimentación profunda o mejora del terreno.")
    rec = g.get("reconocimiento")
    clave = (tc, gt if gt != "T-3" else "T-2")
    dmax, P = TABLA_3_3[clave]
    nsond, sust = TABLA_3_4[clave]
    M.p(f"Exigencias orientativas: distancia máx. entre puntos {dmax} m, profundidad {P} m (tabla 3.3); "
        f"≥ {PUNTOS_MINIMOS} puntos de reconocimiento, ≥ {nsond} sondeo(s) mecánico(s) con sustitución por "
        f"penetrómetros hasta el {sust} % (tabla 3.4).")
    z_inf = D + 2.0 * B  # bulbo de presiones de una zapata aislada
    if rec:
        n, s, prof = rec.get("puntos", 0), rec.get("sondeos", 0), rec.get("profundidad", 0)
        M.p(f"Reconocimiento realizado: {n} puntos ({s} sondeos), profundidad máx. {prof} m. "
            f"Zona de influencia de la zapata hasta {z_inf:.1f} m.")
        if n < PUNTOS_MINIMOS:
            avisos.append(f"Sólo {n} puntos de reconocimiento (< {PUNTOS_MINIMOS}, DB-SE-C 3.2).")
        if s < nsond:
            avisos.append(f"{s} sondeos mecánicos < {nsond} exigidos (DB-SE-C tabla 3.4).")
        if prof < z_inf:
            avisos.append(f"Profundidad reconocida {prof} m < zona de influencia {z_inf:.1f} m.")
        if not avisos:
            M.p("El reconocimiento es suficiente para la cimentación proyectada.")
    else:
        avisos.append("No se aporta el detalle del reconocimiento (puntos, sondeos, profundidad).")
    if g.get("expansivo"):
        avisos.append("Arcillas expansivas: apoyar por debajo de la zona activa, aislar de cambios de humedad "
                      "(aceras perimetrales, drenaje) y comprobar presión de hinchamiento frente a la carga.")
    for a in avisos:
        M.p(f"> ⚠ {a}")
    return dict(tipo=tc, grupo=gt, motivo=motivo, avisos=avisos, dmax=dmax, P=P, nsond=nsond)


def presion_admisible(M, cfg, B, D, Nk, Mk, H_k=0.0, escribir=True):
    """σadm de proyecto (kPa) para una zapata cuadrada B en m a profundidad D, con Nk total (incl. peso propio).
    Devuelve (qadm, detalle). Si escribir=False no vuelca nada a la memoria (para iterar)."""
    g = cfg.get("geotecnia")
    if not g or g.get("fuente") == "orientativo":
        clave = (g or {}).get("terreno_orientativo")
        if clave:
            q, desc = PRESION_ORIENTATIVA[clave]
            ref = f"DB-SE-C tabla D.25 (orientativo): {desc}"
        else:
            q = cfg["cimentacion"]["tension_admisible"]
            ref = "valor adoptado sin estudio geotécnico"
        if escribir:
            M.p(f"σadm = {q:.0f} kPa — {ref}. **PREDIMENSIONADO: a confirmar por estudio geotécnico (DB-SE-C 3).**")
        return q, dict(fuente="orientativo", qadm=q, ref=ref)
    est = g["estratos"]
    nf = g.get("nivel_freatico")
    e = Mk / Nk if Nk else 0.0
    tan_d = H_k / Nk if Nk else 0.0
    qh, dh = hundimiento(est, B, B, D, nf, e_B=e, carga_inclinada=tan_d)
    q_hund = qh / GAMMA_R_HUNDIMIENTO
    q0 = _tension_efectiva(est, D, nf)
    s_adm = g.get("asiento_admisible", 25.0)
    # presión bruta que produce el asiento admisible (asiento lineal con la presión neta)
    s_unit, ds = asiento(est, B, B, D, 1.0, nf)
    q_asiento = s_adm / s_unit + q0
    cand = [(q_hund, "hundimiento / γR"), (q_asiento, f"asiento ≤ {s_adm:.0f} mm")]
    if g.get("qadm_estudio"):
        cand.append((g["qadm_estudio"], "recomendación del estudio geotécnico"))
    qadm, rige = min(cand)
    if escribir:
        M.p(f"Hundimiento (Brinch-Hansen, {dh['condicion']}): B* = {dh['Bs']:.2f} m, q0 = {dh['q0']:.1f} kPa, " +
            (f"φ' = {dh['phi']:.1f}°, c' = {dh['c']:.0f} kPa, Nq = {dh['Nq']:.2f}, Nc = {dh['Nc']:.2f}, Nγ = {dh['Ng']:.2f}, "
             f"sq = {dh['sq']:.2f}, sγ = {dh['sg']:.2f}, dq = {dh['dq']:.2f}" if "phi" in dh else
             f"cu = {dh['cu']:.0f} kPa, sc = {dh['sc']:.2f}, dc = {dh['dc']:.2f}") +
            f" → qh = {qh:.0f} kPa; qh/γR = {q_hund:.0f} kPa (γR = {GAMMA_R_HUNDIMIENTO}, DB-SE-C tabla 2.1).")
        M.p(f"Asiento ({ds['metodo']}): {s_unit:.4f} mm por cada kPa de presión neta → presión bruta para "
            f"{s_adm:.0f} mm = {q_asiento:.0f} kPa." + (f" Estudio geotécnico: qadm = {g['qadm_estudio']:.0f} kPa."
                                                         if g.get("qadm_estudio") else ""))
        M.p(f"**σadm de proyecto = {qadm:.0f} kPa** (rige {rige}).")
    return qadm, dict(fuente="estudio", qadm=qadm, rige=rige, qh=qh, q_hund=q_hund, q_asiento=q_asiento,
                      s_unit=s_unit, q0=q0, det_h=dh, det_s=ds, nf=nf)


def durabilidad(M, cfg):
    """Clase de exposición del hormigón de cimentación y hormigón mínimo."""
    g = cfg.get("geotecnia", {})
    q = clase_quimica(g.get("sulfatos_suelo"), g.get("sulfatos_agua"))
    clase = "IIa" + (f"+{q}" if q else "")
    req = DURABILIDAD[q or "IIa"]
    M.p(f"Agresividad: SO₄ suelo = {g.get('sulfatos_suelo', 'n/d')} mg/kg, agua = {g.get('sulfatos_agua', 'n/d')} mg/l "
        f"→ clase de exposición **{clase}**: a/c ≤ {req[0]}, cemento ≥ {req[1]} kg/m³, resistencia mínima {req[2]}"
        + (", cemento resistente a sulfatos (SR)." if q else "."))
    return dict(clase=clase, hormigon_min=req[2], quimica=q, ac=req[0], cemento=req[1])


# ============================================================================ sin estudio: geología
# Parámetros característicos ESTIMADOS por litología (rango inferior de valores habituales en la bibliografía
# geotécnica española: DB-SE-C anejo D, tablas D.23-D.25; Guía de cimentaciones en obras de carretera).
# Se usan sólo cuando no hay estudio geotécnico y quedan siempre del lado de la seguridad: la σadm resultante
# se limita además al valor orientativo de la tabla D.25 indicado en "d25".
GEOLOGIA = {
    "relleno_antropico": dict(desc="Rellenos antrópicos / vertidos", tipo="granular", gamma=17, phi=25, c=0,
                              nspt=4, d25=None, grupo="T-3", portante=False,
                              avisos=["Los rellenos NO son aptos como apoyo: atravesarlos y apoyar en el terreno natural."]),
    "arcilla_blanda": dict(desc="Arcillas y limos blandos (marismas, fondos de valle, Cuaternario)", tipo="cohesivo",
                           gamma=18, cu=25, phi=20, c=0, E=4000, d25="arcilla_blanda", grupo="T-3",
                           avisos=["Suelo blando: asientos importantes; valorar cimentación profunda o losa."]),
    "arcilla_firme": dict(desc="Arcillas y limos firmes (terrazas, llanuras aluviales, Cuaternario)", tipo="cohesivo",
                          gamma=19, cu=50, phi=24, c=5, E=12000, d25="arcilla_firme", grupo="T-2",
                          avisos=["Comprobar expansividad (límites de Atterberg, Lambe) antes de cimentar."]),
    "marga": dict(desc="Margas y arcillas margosas consolidadas (Terciario)", tipo="cohesivo", gamma=20, cu=100,
                  phi=25, c=10, E=25000, d25="arcilla_muy_firme", grupo="T-2",
                  avisos=["Margas: potencialmente expansivas y alterables; apoyar en marga sana, hormigonar la "
                          "excavación sin demora y proteger de la humedad."]),
    "margas_yesiferas": dict(desc="Margas yesíferas y yesos (Terciario evaporítico)", tipo="cohesivo", gamma=20,
                             cu=80, phi=25, c=10, E=20000, d25="arcilla_firme", grupo="T-3", sulfatos_suelo=12001,
                             avisos=["Yesos: riesgo de disolución y de ataque químico (clase Qc): cemento SR y "
                                     "reconocimiento específico obligatorio."]),
    "arena_suelta": dict(desc="Arenas sueltas a medianamente densas (aluviales, dunas, playas)", tipo="granular",
                         gamma=18, phi=28, c=0, nspt=8, d25="arena_media", grupo="T-2",
                         avisos=["Nivel freático probable a poca profundidad en aluviales: comprobar en obra."]),
    "arena_densa": dict(desc="Arenas densas", tipo="granular", gamma=19, phi=33, c=0, nspt=30, d25="arena_densa",
                        grupo="T-1", avisos=[]),
    "grava_aluvial": dict(desc="Gravas y arenas de terraza / aluvial (Cuaternario)", tipo="granular", gamma=20,
                          phi=32, c=0, nspt=20, d25="grava_media", grupo="T-1",
                          avisos=["Retirar la capa vegetal y limos superficiales; apoyar en la terraza de gravas."]),
    "glacis_coluvial": dict(desc="Glacis, coluviales y costras calcáreas (Cuaternario)", tipo="granular", gamma=19,
                            phi=30, c=5, nspt=15, d25="grava_media", grupo="T-2",
                            avisos=["Depósitos heterogéneos: comprobar la homogeneidad del apoyo en todas las zapatas."]),
    "conglomerado": dict(desc="Conglomerados y areniscas poco cementados (Terciario)", tipo="granular", gamma=21,
                         phi=35, c=10, nspt=40, d25="grava_densa", grupo="T-1", avisos=[]),
    "caliza": dict(desc="Calizas y dolomías (Mesozoico/Terciario)", tipo="roca", gamma=24, E=1e6,
                   d25="roca_sedimentaria_sana", grupo="T-1", reduccion=0.5,
                   avisos=["Calizas: inspeccionar el fondo de excavación por posible karstificación (cavidades, "
                           "arcillas de descalcificación). Si aparecen, el terreno pasa a T-3."]),
    "arenisca": dict(desc="Areniscas y conglomerados cementados", tipo="roca", gamma=23, E=5e5,
                     d25="roca_sedimentaria_sana", grupo="T-1", reduccion=0.5, avisos=[]),
    "pizarra": dict(desc="Pizarras, esquistos y filitas", tipo="roca", gamma=25, E=5e5, d25="roca_foliada_sana",
                    grupo="T-1", reduccion=0.3,
                    avisos=["Roca foliada: retirar la zona alterada superficial y apoyar en roca sana."]),
    "granito": dict(desc="Granitos y rocas ígneas", tipo="roca", gamma=26, E=1e6, d25="roca_ignea_sana", grupo="T-1",
                    reduccion=0.05,
                    avisos=["Granito: suele existir un perfil de alteración (jabre/lehm). Si se apoya en jabre, "
                            "usar la litología 'arena_densa'."]),
}


def perfil_desde_geologia(g):
    """Construye estratos estimados a partir de la litología y el espesor de cobertera/relleno."""
    lit = GEOLOGIA[g["litologia"]]
    er = g.get("espesor_relleno", 0.0)
    estratos = []
    if er > 0:
        r = GEOLOGIA["relleno_antropico"]
        estratos.append(dict(nombre="Relleno / tierra vegetal", desde=0.0, hasta=er, tipo="granular",
                             gamma=r["gamma"], phi=r["phi"], c=0, nspt=r["nspt"]))
    e = {k: v for k, v in lit.items() if k in ("tipo", "gamma", "phi", "c", "cu", "nspt", "E")}
    e.update(nombre=lit["desc"], desde=er, hasta=30.0)
    estratos.append(e)
    return estratos, lit


def presion_admisible_geologia(M, cfg, B, D, Nk, Mk, H_k=0.0, escribir=True):
    g = cfg["geotecnia"]
    estratos, lit = perfil_desde_geologia(g)
    nf = g.get("nivel_freatico")
    if lit["tipo"] == "roca":
        q25 = PRESION_ORIENTATIVA[lit["d25"]][0]
        q = q25 * lit.get("reduccion", 0.5)
        q = min(q, g.get("qadm_maxima", 600.0))     # tope prudente sin reconocimiento de la roca
        if escribir:
            M.p(f"Litología: **{lit['desc']}** (roca). Tabla D.25: {q25:.0f} kPa para roca sana; se aplica un "
                f"factor {lit.get('reduccion', 0.5)} por grado de alteración y fracturación desconocidos y un tope de "
                f"{g.get('qadm_maxima', 600.0):.0f} kPa sin reconocimiento → **σadm estimada = {q:.0f} kPa**.")
        return q, dict(fuente="geologia", qadm=q, rige="tabla D.25 reducida (roca)", litologia=lit["desc"])
    if not lit.get("d25"):
        raise ValueError("La litología indicada no es apta como apoyo directo.")
    sub = dict(cfg)
    sub["geotecnia"] = dict(g, estratos=estratos, fuente="estudio", qadm_estudio=None)
    q_calc, det = presion_admisible(M, sub, B, D, Nk, Mk, H_k, escribir=False)
    q25 = PRESION_ORIENTATIVA[lit["d25"]][0]
    q = min(q_calc, q25)
    if escribir:
        e = estratos[-1]
        par = (f"γ = {e['gamma']} kN/m³, " + (f"cu = {e['cu']} kPa, " if e.get("cu") else "") +
               f"φ' = {e.get('phi', 0)}°, c' = {e.get('c', 0)} kPa" + (f", N_SPT ≈ {e['nspt']}" if e.get("nspt") else "") +
               (f", E ≈ {e['E']/1000:.0f} MPa" if e.get("E") else ""))
        M.p(f"Litología: **{lit['desc']}**. Parámetros característicos estimados (rango inferior): {par}.")
        dh = det["det_h"]
        M.p(f"Hundimiento Brinch-Hansen ({dh['condicion']}): qh = {det['qh']:.0f} kPa → qh/γR = {det['q_hund']:.0f} kPa. "
            f"Asiento ({det['det_s']['metodo']}) ≤ {g.get('asiento_admisible', 25):.0f} mm → {det['q_asiento']:.0f} kPa. "
            f"Tope orientativo tabla D.25: {q25:.0f} kPa.")
        M.p(f"**σadm estimada = {q:.0f} kPa** (rige {'tabla D.25' if q25 <= q_calc else det['rige']}).")
    return q, dict(det, fuente="geologia", qadm=q, litologia=lit["desc"], q25=q25)
