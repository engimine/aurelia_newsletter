"""Motor de cálculo CTE para estructuras porticadas sencillas de una planta (entreplantas,
forjados ligeros, altillos, plataformas): viguetas + vigas principales + zunchos + pilares
+ zapatas aisladas.

Esquema de cálculo (hipótesis documentadas en la memoria):
- Viguetas biapoyadas entre vigas principales (dirección "d").
- Vigas principales biapoyadas entre pilares (dirección "p"), uniones articuladas.
- Zunchos de borde en dirección "d" sobre las alineaciones de pilares.
- Pilares de acero (SHS/HEB) con base articulada o empotrada, zapata aislada centrada.
Unidades: kN, m, MPa. Las secciones se manejan en mm.
"""
import math
import normativa as N
import geotecnia as G


class Memoria:
    """Acumula comprobaciones (tabla) y desarrollo (texto Markdown)."""

    def __init__(self):
        self.lineas = []
        self.checks = []

    def h(self, txt, nivel=2):
        self.lineas.append(f"\n{'#' * nivel} {txt}\n")

    def p(self, txt=""):
        self.lineas.append(txt)

    def check(self, elemento, comprobacion, demanda, capacidad, unidad, ref, ratio=None):
        r = float(ratio if ratio is not None else (demanda / capacidad if capacidad else float("inf")))
        demanda, capacidad = float(demanda), float(capacidad)
        self.checks.append(dict(elemento=elemento, comprobacion=comprobacion, demanda=demanda,
                                capacidad=capacidad, unidad=unidad, ratio=r, ref=ref,
                                cumple=bool(r <= 1.0 + 1e-9)))
        self.p(f"- **{comprobacion}**: {demanda:.3g} {unidad} / {capacidad:.3g} {unidad} = "
               f"**{r:.2f}** {'✔ CUMPLE' if r <= 1 + 1e-9 else '✘ NO CUMPLE'}  _({ref})_")
        return r


def _ratio_max(checks, elemento):
    return max((c["ratio"] for c in checks if c["elemento"] == elemento), default=0.0)


# ====================================================================== cargas
def cargas_superficiales(cfg, M):
    uso = cfg["uso"]
    desc, qk, Qk = N.SOBRECARGA_USO[uso]
    perm = cfg["cargas"].get("permanentes") or [
        dict(nombre="Tablero estructural OSB/contrachapado 22 mm", valor=N.PESOS_TIPICOS["tablero_osb_22"], posterior=False),
        dict(nombre="Pavimento ligero", valor=N.PESOS_TIPICOS["pavimento_ligero"], posterior=True),
        dict(nombre="Falso techo de placa de yeso", valor=N.PESOS_TIPICOS["falso_techo_yeso"], posterior=True),
        dict(nombre="Instalaciones", valor=N.PESOS_TIPICOS["instalaciones"], posterior=True),
    ]
    tab = cfg["cargas"].get("tabiqueria", 0.0)
    if tab:
        perm = perm + [dict(nombre="Tabiquería (DB-SE-AE 2.1)", valor=tab, posterior=True)]
    g_total = sum(c["valor"] for c in perm)
    g_post = sum(c["valor"] for c in perm if c.get("posterior"))
    qk = cfg["cargas"].get("sobrecarga_uso", qk)
    M.h("1. Acciones (DB-SE-AE)")
    M.p("| Acción | Valor | Referencia |\n|---|---|---|")
    for c in perm:
        M.p(f"| {c['nombre']} | {c['valor']:.2f} kN/m² | DB-SE-AE Anejo C |")
    M.p(f"| **Total cargas permanentes (sin peso propio de la estructura)** | **{g_total:.2f} kN/m²** | |")
    M.p(f"| Sobrecarga de uso, categoría {uso} ({desc}) | {qk:.2f} kN/m² | DB-SE-AE tabla 3.1 |")
    M.p(f"| Carga concentrada (independiente) | {Qk:.1f} kN | DB-SE-AE tabla 3.1 |")
    hb = 0.0
    if cfg["cargas"].get("barandilla", True):
        hb = N.carga_barandilla(uso)
        M.p(f"| Fuerza horizontal en barandilla | {hb:.1f} kN/m | DB-SE-AE tabla 3.3 |")
    psi = N.psi_uso(uso)
    M.p(f"\nCoeficientes de simultaneidad (DB-SE tabla 4.2): ψ0 = {psi[0]}, ψ1 = {psi[1]}, ψ2 = {psi[2]}.")
    M.p(f"Coeficientes parciales (DB-SE tabla 4.1): γG = {N.GAMMA_G}, γQ = {N.GAMMA_Q}.")
    M.p("Combinaciones: ELU persistente 1,35·G + 1,50·Q; ELS característica G + Q; casi permanente G + ψ2·Q.")
    M.p("Nieve y viento no actúan (estructura interior). Sismo: ver apartado NCSE-02.")
    return dict(g=g_total, g_post=g_post, q=qk, Q=Qk, hb=hb, psi=psi, perm=perm, uso_desc=desc)


# ====================================================================== flechas
def flechas(M, elem, L, EI, wG_pp, wG_post, wQ, psi2, kdef, lim_int):
    """EI en kN·m². Devuelve ratios de integridad, confort y apariencia (DB-SE 4.3.3.1)."""
    d = lambda w: 5 * w * L ** 4 / (384 * EI) * 1000  # mm
    dGpp, dGpost, dQ = d(wG_pp), d(wG_post), d(wQ)
    activa = dGpost * (1 + kdef) + dGpp * kdef + dQ * (1 + psi2 * kdef)
    confort = dQ
    apariencia = (dGpp + dGpost) * (1 + kdef) + psi2 * dQ * (1 + kdef)
    if kdef:
        M.p(f"Flechas instantáneas: δG,pp = {dGpp:.2f} mm, δG,post = {dGpost:.2f} mm, δQ = {dQ:.2f} mm; "
            f"fluencia kdef = {kdef} (DB-SE-M 5.1).")
    else:
        M.p(f"Flechas instantáneas: δG,pp = {dGpp:.2f} mm, δG,post = {dGpost:.2f} mm, δQ = {dQ:.2f} mm.")
    M.check(elem, f"ELS integridad (flecha activa ≤ L/{lim_int})", activa, L * 1000 / lim_int, "mm", "DB-SE 4.3.3.1")
    M.check(elem, f"ELS confort (δQ ≤ L/{N.FLECHA_CONFORT})", confort, L * 1000 / N.FLECHA_CONFORT, "mm", "DB-SE 4.3.3.1")
    M.check(elem, f"ELS apariencia (casi perm. ≤ L/{N.FLECHA_APARIENCIA})", apariencia, L * 1000 / N.FLECHA_APARIENCIA, "mm", "DB-SE 4.3.3.1")
    return dict(activa=activa, confort=confort, apariencia=apariencia)


# ====================================================================== madera
def viga_madera(M, elem, mat, b, h, L, wG_pp_extra, wG_post, wQ, Pconc, cfg, apoyo_mm=None):
    m = N.MADERAS[mat]
    tipo = m["tipo"]
    cs = cfg.get("clase_servicio", 1)
    dur = N.DURACION_USO[cfg["uso"][0]]
    kmod = N.KMOD[cs][dur]
    gM = N.GAMMA_M_MADERA[tipo]
    kh = N.kh_madera(h, tipo)
    kdef = N.KDEF[cs]
    psi2 = N.psi_uso(cfg["uso"])[2]
    A, W, I = b * h, b * h ** 2 / 6, b * h ** 3 / 12
    pp = m["rho_m"] * 9.81e-3 * A * 1e-6          # kN/m (densidad media, DB-SE-AE Anejo C)
    wG_pp = pp + wG_pp_extra
    wd = N.GAMMA_G * (wG_pp + wG_post) + N.GAMMA_Q * wQ
    Md, Vd = wd * L ** 2 / 8, wd * L / 2
    fmd = kmod * kh * m["fm"] / gM
    fvd = kmod * m["fv"] / gM
    M.p(f"Sección {b}×{h} mm, {mat} ({tipo}); L = {L:.2f} m; clase de servicio {cs}; "
        f"kmod = {kmod} (carga de duración {dur}); γM = {gM}; kh = {kh:.3f}.")
    M.p(f"Cargas: g,pp = {wG_pp:.3f} kN/m, g,post = {wG_post:.3f} kN/m, q = {wQ:.3f} kN/m → "
        f"qd = 1,35·g + 1,5·q = {wd:.3f} kN/m; Md = {Md:.2f} kN·m; Vd = {Vd:.2f} kN.")
    M.check(elem, "ELU flexión σm,d ≤ fm,d", Md * 1e6 / W, fmd, "MPa", "DB-SE-M 6.1.6")
    M.check(elem, "ELU cortante τd ≤ fv,d", 1.5 * Vd * 1e3 / A, fvd, "MPa", "DB-SE-M 6.1.8")
    if Pconc:
        kmod_c = N.KMOD[cs]["corta"]
        Mp = N.GAMMA_G * (wG_pp + wG_post) * L ** 2 / 8 + N.GAMMA_Q * Pconc * L / 4
        M.check(elem, f"ELU carga concentrada {Pconc:.0f} kN en centro de vano", Mp * 1e6 / W,
                kmod_c * kh * m["fm"] / gM, "MPa", "DB-SE-AE 3.1.1(2), DB-SE-M 6.1.6")
    if apoyo_mm:
        Rd = Vd
        M.check(elem, f"ELU compresión perpendicular en apoyo (l = {apoyo_mm} mm)", Rd * 1e3 / (b * apoyo_mm),
                kmod * m["fc90"] / gM, "MPa", "DB-SE-M 6.1.5")
    M.p("Vuelco lateral: canto/ancho ≤ 4 y cara comprimida arriostrada por el tablero → kcrit = 1 (DB-SE-M 6.3.3).")
    EI = m["E"] * I * 1e-9  # kN·m²
    fl = flechas(M, elem, L, EI, wG_pp, wG_post, wQ, psi2, kdef, N.FLECHA_INTEGRIDAD[cfg.get("tabiqueria_tipo", "ordinaria")])
    return dict(seccion=f"{b}x{h} {mat}", b=b, h=h, mat=mat, pp=pp, R_G=(wG_pp + wG_post) * L / 2, R_Q=wQ * L / 2,
                Md=Md, Vd=Vd, flechas=fl)


# ====================================================================== acero (vigas)
def viga_acero(M, elem, nombre, acero, L, wG_extra, wG_post, wQ, Pconc, cfg, arriostrada=True):
    s = N.perfil(nombre)
    fy, fu = N.ACEROS[acero]
    psi2 = N.psi_uso(cfg["uso"])[2]
    wG_pp = s["peso"] + wG_extra
    wd = N.GAMMA_G * (wG_pp + wG_post) + N.GAMMA_Q * wQ
    Md, Vd = wd * L ** 2 / 8, wd * L / 2
    if Pconc:
        Md = max(Md, N.GAMMA_G * (wG_pp + wG_post) * L ** 2 / 8 + N.GAMMA_Q * Pconc * L / 4)
    Mpl = s["Wply"] * fy / N.GAMMA_M0 * 1e-6
    Vpl = s["Av"] * fy / (math.sqrt(3) * N.GAMMA_M0) * 1e-3
    M.p(f"Perfil {nombre} ({acero}, fy = {fy:.0f} MPa); L = {L:.2f} m; clase 1 en flexión (IPE/HEB laminados).")
    M.p(f"A = {s['A']/100:.1f} cm², Iy = {s['Iy']/1e4:.0f} cm⁴, Wpl,y = {s['Wply']/1e3:.1f} cm³, Av = {s['Av']/100:.1f} cm², "
        f"peso propio = {s['peso']:.3f} kN/m.")
    M.p(f"Cargas: g,pp = {wG_pp:.3f} kN/m, g,post = {wG_post:.3f} kN/m, q = {wQ:.3f} kN/m → qd = {wd:.3f} kN/m; "
        f"Md = {Md:.2f} kN·m; Vd = {Vd:.2f} kN.")
    chi_lt = 1.0
    if not arriostrada:
        E, G = N.E_ACERO, N.G_ACERO
        Lmm = L * 1000
        Mcr = 1.13 * math.pi ** 2 * E * s["Iz"] / Lmm ** 2 * math.sqrt(
            s["Iw"] / s["Iz"] + Lmm ** 2 * G * s["It"] / (math.pi ** 2 * E * s["Iz"])) * 1e-6
        lam = math.sqrt(s["Wply"] * fy * 1e-6 / Mcr)
        curva = "a" if s["h"] / s["b"] <= 2 else "b"
        chi_lt = N.chi_pandeo(lam, curva)
        M.p(f"Pandeo lateral sin arriostrar: Mcr = {Mcr:.1f} kN·m (C1 = 1,13), λ̄LT = {lam:.2f}, curva {curva}, "
            f"χLT = {chi_lt:.3f} (DB-SE-A 6.3.3.2).")
    else:
        M.p("Pandeo lateral impedido: ala comprimida arriostrada de forma continua por viguetas y tablero (DB-SE-A 6.3.3.2).")
    M.check(elem, "ELU flexión Md ≤ χLT·Mpl,Rd", Md, chi_lt * Mpl, "kN·m", "DB-SE-A 6.2.6 / 6.3.3")
    M.check(elem, "ELU cortante Vd ≤ Vpl,Rd", Vd, Vpl, "kN", "DB-SE-A 6.2.4")
    if Vd > 0.5 * Vpl:
        M.p("Vd > 0,5·Vpl,Rd: en apoyos el momento es nulo (biapoyada), no hay interacción M-V relevante.")
    EI = N.E_ACERO * s["Iy"] * 1e-9
    fl = flechas(M, elem, L, EI, wG_pp, wG_post, wQ, psi2, 0.0, N.FLECHA_INTEGRIDAD[cfg.get("tabiqueria_tipo", "ordinaria")])
    return dict(seccion=nombre, perfil=s, pp=s["peso"], R_G=(wG_pp + wG_post) * L / 2, R_Q=wQ * L / 2,
                Md=Md, Vd=Vd, flechas=fl)


# ====================================================================== pilares
def pilar_acero(M, elem, nombre, acero, H, NG, NQ, Md_extra, base, cfg):
    s = N.perfil(nombre)
    fy, _ = N.ACEROS[acero]
    eps = math.sqrt(235 / fy)
    Nd = N.GAMMA_G * (NG + s["peso"] * H) + N.GAMMA_Q * NQ
    if s["serie"] == "SHS":
        ct = (s["b"] - 3 * s["t"]) / s["t"]
        clase = 1 if ct <= 33 * eps else 2 if ct <= 38 * eps else 3 if ct <= 42 * eps else 4
        curva = "c"  # conformado en frío (DB-SE-A tabla 6.2)
        Wy = s["Wply"] if clase <= 2 else s["Wely"]
        imin = math.sqrt(s["Iy"] / s["A"])
        M.p(f"Esbeltez de pared c/t = {ct:.1f} → clase {clase} (límites 33ε/38ε/42ε, ε = {eps:.2f}).")
    else:
        clase, curva, Wy = 1, "c", s["Wply"]  # HEB pandeo eje débil: curva c
        imin = math.sqrt(s["Iz"] / s["A"])
    if clase == 4:
        M.check(elem, "Clase de sección (no se admite clase 4)", 4, 3, "-", "DB-SE-A 5.2.4")
        return dict(seccion=nombre, perfil=s, Nd=Nd)
    beta = 2.0 if base == "empotrada" else 1.0  # cabeza libre de girar y desplazarse si base empotrada sin arriostrar
    if base == "empotrada" and cfg["estabilidad"]["tipo"] == "muro":
        beta = 0.7
    Lk = beta * H
    Npl = s["A"] * fy * 1e-3
    Ncr = math.pi ** 2 * N.E_ACERO * s["A"] * imin ** 2 / (Lk * 1000) ** 2 * 1e-3
    lam = math.sqrt(Npl / Ncr)
    chi = N.chi_pandeo(lam, curva)
    Nbrd = chi * Npl / N.GAMMA_M1
    MRd = Wy * fy / N.GAMMA_M1 * 1e-6
    M.p(f"Perfil {nombre} ({acero}); H = {H:.2f} m; base {base}; β = {beta} → Lk = {Lk:.2f} m; "
        f"i = {imin:.1f} mm; λ̄ = {lam:.2f}; curva {curva}; χ = {chi:.3f}.")
    M.p(f"Nd = 1,35·(NG + pp) + 1,5·NQ = {Nd:.1f} kN; Nb,Rd = χ·A·fy/γM1 = {Nbrd:.1f} kN; "
        f"Md = {Md_extra:.2f} kN·m (excentricidad de apoyo de vigas / acción horizontal); MRd = {MRd:.2f} kN·m.")
    M.check(elem, "ELU pandeo por compresión Nd ≤ Nb,Rd", Nd, Nbrd, "kN", "DB-SE-A 6.3.2")
    k = min(1 + 0.6 * lam * Nd / Nbrd, 1 + 0.6 * Nd / Nbrd)
    inter = Nd / Nbrd + k * 0.9 * Md_extra / MRd
    M.check(elem, "ELU interacción N + M (cm = 0,9)", inter, 1.0, "-", "DB-SE-A 6.3.4.2 (simplificada)", ratio=inter)
    return dict(seccion=nombre, perfil=s, Nd=Nd, NG=NG + s["peso"] * H, NQ=NQ, Md=Md_extra, Lk=Lk)


# ====================================================================== placa base
def placa_base(M, elem, pil, Nd, acero, fck, cfg):
    s = pil["perfil"]
    fy, fu = N.ACEROS[acero]
    a = max(200, int(math.ceil((s["b"] + 100) / 10.0) * 10))
    fcd = fck / N.GAMMA_C
    fjd = 2 / 3 * fcd * 1.5  # βj = 2/3, kj ≈ 1,5 (zapata mucho mayor que la placa) DB-SE-A 8.8.1
    sigma = Nd * 1e3 / a ** 2
    c = (a - s["b"]) / 2
    t_req = c * math.sqrt(3 * sigma * N.GAMMA_M0 / fy)
    t = next(x for x in (10, 12, 15, 20, 25, 30) if x >= max(t_req, 10))
    M.p(f"Placa {a}×{a}×{t} mm ({acero}); fjd = βj·kj·fcd = {fjd:.1f} MPa; σ = Nd/A = {sigma:.2f} MPa; "
        f"vuelo c = {c:.0f} mm → t,req = c·√(3σγM0/fy) = {t_req:.1f} mm.")
    M.check(elem, "ELU presión bajo placa σ ≤ fjd", sigma, fjd, "MPa", "DB-SE-A 8.8.1")
    M.check(elem, f"ELU flexión de placa t,req ≤ t = {t} mm", t_req, t, "mm", "DB-SE-A 8.8.1")
    a_w = 4 if t <= 15 else 5
    per = 4 * s["b"]
    Fw = a_w * per * fu / (math.sqrt(3) * N.BETA_W[acero] * N.GAMMA_M2) * 1e-3
    M.check(elem, f"ELU soldadura pilar-placa en ángulo a = {a_w} mm perimetral", Nd, Fw, "kN", "DB-SE-A 8.6.2")
    perno = cfg.get("pernos", "4 M16 barra roscada 8.8 con anclaje químico (ETA), L,emb ≥ 125 mm")
    M.p(f"Anclaje: {perno}. Bajo cargas gravitatorias no hay tracción; el anclaje se dimensiona con el software "
        f"del fabricante (ETA) para el cortante horizontal Hd indicado en la estabilidad lateral.")
    return dict(a=a, t=t, aw=a_w, pernos=perno)


# ====================================================================== zapata
def _qadm(M, cfg, B, D, Nk, Mk, escribir):
    g = cfg.get("geotecnia")
    if g and g.get("fuente") == "geologia":
        return G.presion_admisible_geologia(M, cfg, B, D, Nk, Mk, escribir=escribir)
    return G.presion_admisible(M, cfg, B, D, Nk, Mk, escribir=escribir)


def zapata(M, elem, NG, NQ, Mk, a0, cfg):
    c = cfg["cimentacion"]
    g = cfg.get("geotecnia", {})
    h = max(c.get("canto", 0.40), N.CANTO_MIN_ZAPATA)
    prof = c.get("profundidad", h + 0.20)
    er = g.get("espesor_relleno", 0.0)
    if er and prof < er + 0.20:
        prof = er + 0.20   # apoyo empotrado al menos 20 cm en el terreno natural
    if g.get("profundidad_minima"):
        prof = max(prof, g["profundidad_minima"])
    fck = N.HORMIGONES[cfg["materiales"]["hormigon"]]
    fyk = N.ARMADURAS[cfg["materiales"]["armadura"]]
    fyd = min(fyk / N.GAMMA_S, 400.0)  # tirante en bielas y tirantes ≤ 400 MPa
    rec = c.get("recubrimiento", 0.05)
    Nk = NG + NQ
    peso_f = lambda B: B * B * (h * 25 + (prof - h) * 20)
    B = c.get("lado")
    if not B:
        B = c.get("lado_minimo", 0.60)
        while True:
            Ntot = Nk + peso_f(B)
            e = Mk / Ntot
            sadm, _ = _qadm(M, cfg, B, prof, Ntot, Mk, False)
            smax = Ntot / B ** 2 * (1 + 6 * e / B)
            if Ntot / B ** 2 <= sadm and smax <= 1.25 * sadm and e <= B / 6:
                break
            B = round(B + 0.05, 2)
            if B > 6:
                raise ValueError("Zapata > 6 m: la cimentación directa no es adecuada para este terreno.")
    peso = peso_f(B)
    Ntot = Nk + peso
    e = Mk / Ntot
    smed = Ntot / B ** 2
    smax = smed * (1 + 6 * e / B)
    M.h("7.1 Terreno de cimentación", 3)
    sadm, geo = _qadm(M, cfg, B, prof, Ntot, Mk, True)
    M.h("7.2 Zapata", 3)
    M.p(f"Zapata cuadrada {B:.2f}×{B:.2f}×{h:.2f} m, cota de apoyo −{prof:.2f} m; HA: fck = {fck:.0f} MPa; "
        f"armadura fyk = {fyk:.0f} MPa; σadm = {sadm:.0f} kPa.")
    M.p(f"Nk = {Nk:.1f} kN; peso zapata + tierras = {peso:.1f} kN; Mk = {Mk:.2f} kN·m → e = {e*100:.1f} cm.")
    M.check(elem, "Tensión media σmed ≤ σadm", smed, sadm, "kPa", "DB-SE-C 4.3")
    M.check(elem, "Tensión de borde σmax ≤ 1,25·σadm", smax, 1.25 * sadm, "kPa", "DB-SE-C 4.3")
    if geo.get("s_unit"):
        s_ = geo["s_unit"] * max(smed - geo["q0"], 0)
        s_adm = g.get("asiento_admisible", 25.0)
        M.check(elem, "ELS asiento total s ≤ s,adm", s_, s_adm, "mm", "DB-SE-C 4.2.2.3 / anejo F.2")
        Lmin = min(min(cfg["geometria"]["luces_x"]), min(cfg["geometria"]["luces_y"]))
        dist = 0.5 * s_ / 1000 / Lmin   # asiento diferencial estimado = 50 % del total entre zapatas iguales
        M.check(elem, "ELS distorsión angular β ≤ 1/500", dist, 1 / 500, "-", "DB-SE-C tabla 2.2")
    v = (B - a0) / 2
    rigida = v <= 2 * h
    d = h - rec - 0.008
    Nd = N.GAMMA_G * NG + N.GAMMA_Q * NQ
    M.p(f"Vuelo v = {v:.2f} m {'≤' if rigida else '>'} 2h = {2*h:.2f} m → zapata {'RÍGIDA' if rigida else 'FLEXIBLE'}; "
        f"canto útil d = {d:.3f} m; Nd = {Nd:.1f} kN.")
    if rigida:
        Td = Nd * (B - a0) / (6.8 * d)
        As_calc = Td / fyd * 1e3  # mm²
        M.p(f"Método de bielas y tirantes: Td = Nd·(a − a0)/(6,8·d) = {Td:.1f} kN; As = Td/fyd = {As_calc:.0f} mm² "
            f"(fyd ≤ 400 MPa).")
    else:
        sd = Nd / B ** 2
        lv = v + 0.15 * a0
        Md = sd * B * lv ** 2 / 2
        As_calc = Md * 1e6 / (0.9 * d * 1000 * fyk / N.GAMMA_S)
        M.p(f"Zapata flexible: Md (sección de referencia a 0,15·a0) = {Md:.1f} kN·m; As = {As_calc:.0f} mm².")
    As_min = N.RHO_MIN_ZAPATA * B * h * 1e6
    As_req = max(As_calc, As_min)
    sol = None
    for phi in (12, 16, 20):
        n = math.ceil(As_req / N.BARRAS[phi])
        sep = (B - 2 * rec) / max(n - 1, 1)
        n = max(n, math.ceil((B - 2 * rec) / 0.30) + 1)  # separación ≤ 30 cm
        sep = (B - 2 * rec) / (n - 1)
        if sep >= 0.10:
            sol = (n, phi, sep)
            break
    n, phi, sep = sol
    As_prov = n * N.BARRAS[phi]
    M.check(elem, f"Armadura inferior por dirección: {n}Ø{phi} c/{sep*100:.0f} cm", As_req, As_prov, "mm²",
            "Código Estructural (bielas y tirantes, cuantía mínima)")
    M.p(f"As,min geométrica = {RHO_TXT()} · B · h = {As_min:.0f} mm²; Ø ≥ 12 mm y separación ≤ 30 cm.")
    # compresión localizada bajo la placa base
    return dict(B=B, h=h, prof=prof, n=n, phi=phi, sep=sep, rigida=rigida, smax=smax, smed=smed, Nd=Nd,
                rec=rec, fck=fck, sadm=sadm, geo=geo)


def RHO_TXT():
    return f"{N.RHO_MIN_ZAPATA*1000:.1f} ‰"


# ====================================================================== auto-dimensionado
def _primero_que_cumple(candidatos, prueba):
    """prueba(cand) -> (ok, resultado). Devuelve el primer candidato que cumple."""
    ultimo = None
    for cnd in candidatos:
        ok, res = prueba(cnd)
        ultimo = (cnd, res)
        if ok:
            return cnd, res
    return ultimo


def _ensayo(fn):
    M = Memoria()
    res = fn(M)
    return all(c["cumple"] for c in M.checks), res


def calcular(cfg):
    """Calcula la estructura completa. Devuelve (resultados, memoria)."""
    g = cfg["geometria"]
    d_dir = g.get("direccion_viguetas") or ("x" if max(g["luces_x"]) <= max(g["luces_y"]) else "y")
    Lj = g["luces_x"] if d_dir == "x" else g["luces_y"]   # vanos de viguetas
    Lb = g["luces_y"] if d_dir == "x" else g["luces_x"]   # vanos de vigas principales
    H = g["altura_pilar"]
    M = Memoria()
    M.h(f"MEMORIA DE CÁLCULO DE ESTRUCTURA — {cfg['proyecto']['titulo']}", 1)
    M.p(f"{cfg['proyecto'].get('subtitulo','')} · {cfg['proyecto'].get('emplazamiento','')}")
    M.h("0. Normativa y método")
    M.p("CTE DB-SE (Seguridad estructural), DB-SE-AE (Acciones), DB-SE-A (Acero), DB-SE-M (Madera), "
        "DB-SE-C (Cimientos), DB-SI 6 (Resistencia al fuego de la estructura); Código Estructural (RD 470/2021) "
        "para el hormigón armado; NCSE-02 (sismo). Método de los estados límite (DB-SE 3.2).")
    M.p(f"Esquema: viguetas biapoyadas en dirección {d_dir.upper()} (vanos {', '.join(f'{x:.2f}' for x in Lj)} m) entre vigas "
        f"principales biapoyadas (vanos {', '.join(f'{x:.2f}' for x in Lb)} m) sobre pilares de altura {H:.2f} m. "
        f"Uniones viga-pilar articuladas.")
    C = cargas_superficiales(cfg, M)
    mat = cfg["materiales"]
    s = cfg["forjado"]["separacion"]
    res = dict(direccion=d_dir, Lj=Lj, Lb=Lb, H=H, cargas=C)

    # ------------------------------------------------ viguetas
    M.h("2. Viguetas (DB-SE-M)" if cfg["forjado"]["material"] in N.MADERAS else "2. Viguetas (DB-SE-A)")
    Lv = max(Lj)
    wGpp_extra = sum(c["valor"] for c in C["perm"] if not c.get("posterior")) * s
    wGpost, wQ = C["g_post"] * s, C["q"] * s
    fmat = cfg["forjado"]["material"]
    if fmat in N.MADERAS:
        tipo = N.MADERAS[fmat]["tipo"]
        cands = [tuple(cfg["forjado"]["seccion"])] if cfg["forjado"].get("seccion") else \
            sorted(N.SECCIONES_MADERA[tipo], key=lambda bh: bh[0] * bh[1])
        sec, _ = _primero_que_cumple(cands, lambda bh: _ensayo(lambda m: viga_madera(
            m, "Vigueta", fmat, bh[0], bh[1], Lv, wGpp_extra, wGpost, wQ, C["Q"], cfg)))
        M.p(f"Vigueta tipo: separación {s*100:.0f} cm, luz de cálculo {Lv:.2f} m (entre ejes, del lado de la seguridad).")
        vig = viga_madera(M, "Vigueta", fmat, sec[0], sec[1], Lv, wGpp_extra, wGpost, wQ, C["Q"], cfg)
    else:
        cands = [cfg["forjado"]["seccion"]] if cfg["forjado"].get("seccion") else N.catalogo("IPE")
        sec, _ = _primero_que_cumple(cands, lambda p: _ensayo(lambda m: viga_acero(
            m, "Vigueta", p, fmat, Lv, wGpp_extra, wGpost, wQ, C["Q"], cfg)))
        M.p(f"Vigueta tipo: separación {s*100:.0f} cm, luz de cálculo {Lv:.2f} m.")
        vig = viga_acero(M, "Vigueta", sec, fmat, Lv, wGpp_extra, wGpost, wQ, C["Q"], cfg)
    res["vigueta"] = vig
    R_vig = N.GAMMA_G * vig["R_G"] + N.GAMMA_Q * vig["R_Q"]
    M.p(f"Reacción de cálculo de vigueta: Rd = {R_vig:.2f} kN → estribo/colgador metálico con ETA y capacidad "
        f"≥ {R_vig:.1f} kN (o apoyo directo sobre ala con fijación).")
    res["R_vigueta"] = R_vig
    pp_forjado = vig["pp"] / s  # kN/m² de viguetas

    # ------------------------------------------------ vigas principales
    M.h("3. Vigas principales (DB-SE-A)" if mat["vigas"] in N.ACEROS else "3. Vigas principales (DB-SE-M)")
    n_lin = len(Lj) + 1
    trib = [((Lj[i - 1] if i > 0 else 0) + (Lj[i] if i < len(Lj) else 0)) / 2 for i in range(n_lin)]
    tmax = max(trib)
    barand = cfg["cargas"].get("peso_barandilla", 0.30)
    LbM = max(Lb)
    g_sup = C["g"] - sum(c["valor"] for c in C["perm"] if c.get("posterior")) + pp_forjado
    wG_extra = g_sup * tmax + (barand if trib.index(tmax) in (0, n_lin - 1) else 0)
    wG_post, wQb = C["g_post"] * tmax, C["q"] * tmax
    M.p(f"Ancho tributario máximo = {tmax:.2f} m (vigas interiores = media de vanos adyacentes; de borde = medio vano). "
        f"Se incluye peso de viguetas ({pp_forjado:.2f} kN/m²) y barandilla ({barand:.2f} kN/m) en vigas de borde.")
    arr = cfg.get("vigas_arriostradas", True)
    enrasado = cfg["forjado"].get("apoyo", "enrasado") == "enrasado"
    h_vig = vig["h"] if "h" in vig else vig["perfil"]["h"]
    if enrasado:
        M.p(f"Forjado enrasado: canto de viga principal ≥ canto de vigueta ({h_vig:.0f} mm).")
    if mat["vigas"] in N.ACEROS:
        cands = [cfg["vigas"]["perfil"]] if cfg.get("vigas", {}).get("perfil") else N.catalogo(cfg.get("vigas", {}).get("serie", "IPE"))
        if enrasado and not cfg.get("vigas", {}).get("perfil"):
            # forjado enrasado: el canto de la viga debe alojar la vigueta (criterio constructivo)
            cands = [p for p in cands if N.perfil(p)["h"] >= h_vig] or cands[-1:]
        sec, _ = _primero_que_cumple(cands, lambda p: _ensayo(lambda m: viga_acero(
            m, "Viga principal", p, mat["vigas"], LbM, wG_extra, wG_post, wQb, 0, cfg, arr)))
        vp = viga_acero(M, "Viga principal", sec, mat["vigas"], LbM, wG_extra, wG_post, wQb, 0, cfg, arr)
    else:
        tipo = N.MADERAS[mat["vigas"]]["tipo"]
        cands = [tuple(cfg["vigas"]["seccion"])] if cfg.get("vigas", {}).get("seccion") else \
            sorted(N.SECCIONES_MADERA[tipo], key=lambda bh: bh[0] * bh[1])
        if enrasado and not cfg.get("vigas", {}).get("seccion"):
            cands = [bh for bh in cands if bh[1] >= h_vig] or cands[-1:]
        sec, _ = _primero_que_cumple(cands, lambda bh: _ensayo(lambda m: viga_madera(
            m, "Viga principal", mat["vigas"], bh[0], bh[1], LbM, wG_extra, wG_post, wQb, 0, cfg, 100)))
        vp = viga_madera(M, "Viga principal", mat["vigas"], sec[0], sec[1], LbM, wG_extra, wG_post, wQb, 0, cfg, 100)
    res["viga"] = vp
    res["trib"] = trib

    # ------------------------------------------------ zunchos de borde (dirección d)
    M.h("4. Zunchos de borde")
    wz_G = g_sup * s / 2 + barand + C["g_post"] * s / 2
    wz_Q = C["q"] * s / 2
    Lz = max(Lj)
    if mat["vigas"] in N.ACEROS:
        cands = N.catalogo("IPE")
        sec, _ = _primero_que_cumple(cands, lambda p: _ensayo(lambda m: viga_acero(
            m, "Zuncho", p, mat["vigas"], Lz, g_sup * s / 2 + barand, C["g_post"] * s / 2, wz_Q, 0, cfg, arr)))
        # el zuncho debe tener el mismo canto que las vigas para enrasar: se toma el mayor de ambos criterios
        if N.perfil(sec)["h"] < N.perfil(vp["seccion"])["h"] and cfg.get("zuncho_igual_canto", True):
            sec = vp["seccion"]
        zu = viga_acero(M, "Zuncho", sec, mat["vigas"], Lz, g_sup * s / 2 + barand, C["g_post"] * s / 2, wz_Q, 0, cfg, arr)
    else:
        b, hh = vp["b"], vp["h"]
        zu = viga_madera(M, "Zuncho", mat["vigas"], b, hh, Lz, g_sup * s / 2 + barand, C["g_post"] * s / 2, wz_Q, 0, cfg)
    res["zuncho"] = zu

    # ------------------------------------------------ pilares
    M.h("5. Pilares (DB-SE-A)")
    # reacción máxima en pilar interior/esquina: suma de vigas principales de los dos vanos adyacentes + zunchos
    def reacciones(i, j):
        t = trib[i]
        wG = g_sup * t + C["g_post"] * t + (barand if i in (0, n_lin - 1) else 0) + vp["pp"]
        wQ_ = C["q"] * t
        Lsum = (Lb[j - 1] if j > 0 else 0) + (Lb[j] if j < len(Lb) else 0)
        NG_, NQ_ = wG * Lsum / 2, wQ_ * Lsum / 2
        if j in (0, len(Lb)):  # alineación de borde: zuncho apoyado
            Lz_sum = (Lj[i - 1] if i > 0 else 0) + (Lj[i] if i < len(Lj) else 0)
            NG_ += (wz_G + zu["pp"]) * Lz_sum / 2
            NQ_ += wz_Q * Lz_sum / 2
        # momento por excentricidad de apoyo desequilibrado (e = b/2 + 0,10 m, criterio habitual)
        RL = (wG * (Lb[j - 1] if j > 0 else 0) / 2, wQ_ * (Lb[j - 1] if j > 0 else 0) / 2)
        RR = (wG * (Lb[j] if j < len(Lb) else 0) / 2, wQ_ * (Lb[j] if j < len(Lb) else 0) / 2)
        dR = abs(N.GAMMA_G * (RL[0] - RR[0]) + N.GAMMA_Q * (RL[1] - RR[1]))
        return NG_, NQ_, dR
    pil_N = {(i, j): reacciones(i, j) for i in range(n_lin) for j in range(len(Lb) + 1)}
    crit = max(pil_N, key=lambda k: N.GAMMA_G * pil_N[k][0] + N.GAMMA_Q * pil_N[k][1])
    NG, NQ, dR = pil_N[crit]
    # estabilidad lateral
    est = cfg["estabilidad"]
    Ltot_p, Ltot_d = sum(Lb), sum(Lj)
    Nd_tot = sum(N.GAMMA_G * v[0] + N.GAMMA_Q * v[1] for v in pil_N.values())
    H_imp = Nd_tot / 200.0  # imperfección global φ0 = 1/200 (DB-SE-A 5.4.1, del lado de la seguridad)
    H_bar = N.GAMMA_Q * C["hb"] * max(Ltot_p, Ltot_d) if C["hb"] else 0.0
    Hd = max(H_imp, H_bar)
    npil = len(pil_N)
    base = cfg["pilares"].get("base", "empotrada")
    Md_h = 0.0
    if est["tipo"] == "pilares_empotrados":
        Md_h = Hd / npil * H
    acero_p = mat["pilares"]
    serie_p = cfg["pilares"].get("serie", "SHS")
    def md_pilar(nombre):
        b = N.perfil(nombre)["b"] / 1000
        return dR * (b / 2 + 0.10) + Md_h
    cands = [cfg["pilares"]["perfil"]] if cfg["pilares"].get("perfil") else N.catalogo(serie_p)
    pmin = cfg["pilares"].get("minimo", "SHS 80x4" if serie_p == "SHS" else None)
    if pmin and not cfg["pilares"].get("perfil"):
        A_min = N.perfil(pmin)["A"]
        cands = [p for p in cands if N.perfil(p)["b"] >= N.perfil(pmin)["b"] and N.perfil(p)["A"] >= A_min]
    sec, _ = _primero_que_cumple(cands, lambda p: _ensayo(lambda m: pilar_acero(
        m, "Pilar", p, acero_p, H, NG, NQ, md_pilar(p), base, cfg)))
    M.p(f"Pilar más cargado: alineación {crit}. NG = {NG:.1f} kN, NQ = {NQ:.1f} kN.")
    M.p(f"Estabilidad lateral: Hd = max(imperfección ΣNd/200 = {H_imp:.2f} kN; barandilla 1,5·{C['hb']:.1f} kN/m·L = "
        f"{H_bar:.2f} kN) = {Hd:.2f} kN, resistida mediante "
        f"{'anclaje del forjado al muro existente' if est['tipo']=='muro' else 'pilares empotrados en base (ménsulas)' if est['tipo']=='pilares_empotrados' else 'arriostramiento en cruz'}.")
    pil = pilar_acero(M, "Pilar", sec, acero_p, H, NG, NQ, md_pilar(sec), base, cfg)
    res["pilar"] = pil
    res["pilares_N"] = pil_N
    res["Hd"] = Hd
    if est["tipo"] == "muro":
        sep_a = est.get("separacion_anclajes", 0.60)
        L_muro = est.get("longitud_muro", Ltot_p)
        n_a = max(2, math.floor(L_muro / sep_a) + 1)
        Va = Hd / n_a
        M.p(f"Anclaje a muro: {n_a} anclajes c/{sep_a*100:.0f} cm en {L_muro:.2f} m; Vd por anclaje = {Va:.2f} kN "
            f"(comprobar con ETA del anclaje en la fábrica existente).")
        res["anclajes_muro"] = dict(n=n_a, sep=sep_a, Vd=Va, L=L_muro)
    elif est["tipo"] == "cruces":
        L_b = min(Lb)
        diag = math.hypot(L_b, H)
        Td = Hd / 2 * diag / L_b
        fy = N.ACEROS[acero_p][0]
        A_req = Td * 1e3 * N.GAMMA_M0 / fy
        phi = next(p for p in (12, 16, 20, 25, 30) if math.pi * p ** 2 / 4 * 0.78 >= A_req)
        M.check("Arriostramiento", f"Tirante redondo Ø{phi} (área resistente roscada)", Td,
                math.pi * phi ** 2 / 4 * 0.78 * fy / N.GAMMA_M0 / 1e3, "kN", "DB-SE-A 6.2.3")
        res["cruces"] = dict(phi=phi, Td=Td)

    # ------------------------------------------------ placa base
    M.h("6. Placa de anclaje (DB-SE-A 8.8)")
    fck = N.HORMIGONES[mat["hormigon"]]
    pb = placa_base(M, "Placa base", pil, pil["Nd"], acero_p, fck, cfg)
    res["placa"] = pb

    # ------------------------------------------------ zapata
    M.h("7. Cimentación (DB-SE-C, Código Estructural)")
    Mk = (Md_h / 1.5) if est["tipo"] == "pilares_empotrados" else 0.0
    g = cfg.get("geotecnia", {})
    fuente = g.get("fuente", "orientativo")
    M.h("7.0 Información geotécnica", 3)
    if fuente == "estudio":
        M.p(f"Fuente: estudio geotécnico — {g.get('referencia', 'sin referencia')}.")
    elif fuente == "geologia":
        M.p(f"Fuente: **sin estudio geotécnico**; terreno estimado a partir de la geología del emplazamiento "
            f"({g.get('referencia', 'mapa geológico')}). Valores de PREDIMENSIONADO: el estudio geotécnico es "
            f"preceptivo (DB-SE-C 3.1) y debe confirmarlos antes de la ejecución.")
        if not g.get("litologia"):
            import geologia as GL
            if not g.get("descripcion_geologica") and g.get("coordenadas"):
                try:
                    g["descripcion_geologica"], _ = GL.consultar_magna(*g["coordenadas"])
                except Exception as ex:
                    raise ValueError(f"Sin litología y sin acceso al IGME ({ex}). Indicar 'litologia' o "
                                     f"'descripcion_geologica' copiada del visor https://info.igme.es/visor/")
            g["litologia"], _ = GL.clasificar(g["descripcion_geologica"])
            M.p(f"Descripción geológica: «{g['descripcion_geologica'][:300]}» → litología geotécnica "
                f"«{g['litologia']}».")
        lit = G.GEOLOGIA[g["litologia"]]
        for a_ in lit["avisos"]:
            M.p(f"> ⚠ {a_}")
        if lit.get("sulfatos_suelo") and "sulfatos_suelo" not in g:
            g["sulfatos_suelo"] = lit["sulfatos_suelo"]
        g.setdefault("grupo_terreno_geologia", lit["grupo"])
    else:
        M.p("Fuente: valor de tensión admisible adoptado sin estudio ni geología. PREDIMENSIONADO.")
    rec_geo = G.analizar_reconocimiento(M, cfg, 1.0, cfg["cimentacion"].get("profundidad", 0.6))
    dur = G.durabilidad(M, cfg)
    if N.HORMIGONES[mat["hormigon"]] < N.HORMIGONES[dur["hormigon_min"]]:
        M.p(f"Se eleva el hormigón de cimentación de {mat['hormigon']} a {dur['hormigon_min']} por durabilidad.")
        mat["hormigon"] = dur["hormigon_min"]
    res["geotecnia"] = dict(fuente=fuente, reconocimiento=rec_geo, durabilidad=dur)
    zp = zapata(M, "Zapata", pil["NG"], NQ, Mk, pb["a"] / 1000, cfg)
    res["zapata"] = zp
    Ac0 = (pb["a"] / 1000) ** 2
    fcd = fck / N.GAMMA_C
    Ac1 = min(zp["B"], 3 * pb["a"] / 1000) ** 2
    M.check("Zapata", "Compresión localizada bajo placa", pil["Nd"], Ac0 * fcd * 1e3 * min(math.sqrt(Ac1 / Ac0), 3.3),
            "kN", "Código Estructural art. 61")

    # ------------------------------------------------ unión viga-pilar
    M.h("8. Uniones")
    Rv = N.GAMMA_G * vp["R_G"] + N.GAMMA_Q * vp["R_Q"]
    clase_t = cfg.get("tornillos", "8.8")
    fub = N.CLASES_TORNILLO[clase_t][1]
    FvRd = 0.6 * fub * N.TORNILLOS_AS[16] / N.GAMMA_M2 * 1e-3 if clase_t in ("4.6", "5.6", "8.8") else \
        0.5 * fub * N.TORNILLOS_AS[16] / N.GAMMA_M2 * 1e-3
    nt = max(2, math.ceil(Rv / FvRd))
    M.p(f"Reacción de cálculo de viga principal Rd = {Rv:.1f} kN.")
    if mat["vigas"] in N.ACEROS:
        M.check("Unión viga-pilar", f"{nt} tornillos M16 {clase_t} a cortante (1 plano)", Rv, nt * FvRd, "kN", "DB-SE-A 8.5.2.2")
        fu = N.ACEROS[acero_p][1]
        Fb = 2.5 * 1.0 * fu * 16 * 8 / N.GAMMA_M2 * 1e-3 * nt  # aplastamiento chapa 8 mm, αb ≈ 1
        M.check("Unión viga-pilar", f"Aplastamiento en chapa de 8 mm", Rv, Fb, "kN", "DB-SE-A 8.5.2.2")
    else:
        M.p("Unión viga de madera - pilar: horquilla/estribo metálico con ETA; capacidad requerida ≥ Rd. "
            "Comprobación de pasadores según DB-SE-M 8 con datos del fabricante.")
    res["union"] = dict(Rd=Rv, n_tornillos=nt, clase=clase_t)

    # ------------------------------------------------ sismo y fuego
    M.h("9. Acción sísmica (NCSE-02) y resistencia al fuego (DB-SI 6)")
    ab = cfg.get("sismo", {}).get("ab", 0.0)
    imp = cfg.get("sismo", {}).get("importancia", "normal")
    if ab < 0.04:
        txt = f"ab = {ab:.2f}g < 0,04g → no es obligatoria la aplicación de la NCSE-02 (art. 1.2.3)."
    elif imp == "normal" and ab < 0.08 and est["tipo"] != "pilares_empotrados":
        txt = (f"ab = {ab:.2f}g < 0,08g, construcción de importancia normal con pórticos bien arriostrados "
               f"→ exenta de la NCSE-02 (art. 1.2.3).")
    else:
        txt = f"ab = {ab:.2f}g → APLICA NCSE-02: realizar cálculo sísmico específico (fuera del alcance de esta hoja)."
    M.p(txt)
    res["sismo_txt"] = txt
    rf = cfg.get("resistencia_fuego", "R 30")
    M.p(f"Resistencia al fuego exigida: {rf} (DB-SI 6, tabla 3.1). Acero: protección con pintura intumescente o "
        f"placa según certificado; madera: comprobación por sección reducida (DB-SI anejo E).")
    res["fuego"] = rf

    # ------------------------------------------------ resumen
    M.h("10. Resumen de comprobaciones")
    M.p("| Elemento | Comprobación | Demanda | Capacidad | Aprov. | Estado |\n|---|---|---|---|---|---|")
    for c in M.checks:
        M.p(f"| {c['elemento']} | {c['comprobacion']} | {c['demanda']:.3g} {c['unidad']} | {c['capacidad']:.3g} {c['unidad']} "
            f"| {c['ratio']:.2f} | {'CUMPLE' if c['cumple'] else 'NO CUMPLE'} |")
    ok = all(c["cumple"] for c in M.checks)
    M.p(f"\n**Resultado global: {'TODAS LAS COMPROBACIONES CUMPLEN' if ok else 'HAY COMPROBACIONES QUE NO CUMPLEN'}.**")
    M.p("\n> Documento técnico preliminar generado con ayuda de IA. Debe ser revisado, completado y firmado por "
        "técnico competente antes de su uso en proyecto, licencia u obra.")
    res["ok"] = ok
    res["checks"] = M.checks
    return res, M
