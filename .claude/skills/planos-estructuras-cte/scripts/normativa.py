"""Tablas normativas (CTE DB-SE, DB-SE-AE, DB-SE-A, DB-SE-M, DB-SE-C, Código Estructural)
y catálogo de perfiles. Unidades: kN, m, MPa (N/mm²), mm para secciones.

Los valores se toman de las tablas del CTE vigente. Cualquier dato nuevo que se añada
debe llevar su referencia (documento + tabla/apartado) en el comentario.
"""
import math
from functools import lru_cache
import numpy as np

# ---------------------------------------------------------------- DB-SE-AE
# Tabla 3.1 DB-SE-AE: sobrecarga de uso  (uniforme kN/m², concentrada kN)
SOBRECARGA_USO = {
    "A1": ("Viviendas y zonas de habitaciones en hospitales y hoteles", 2.0, 2.0),
    "A2": ("Trasteros", 3.0, 2.0),
    "B":  ("Zonas administrativas", 2.0, 2.0),
    "C1": ("Zonas con mesas y sillas", 3.0, 4.0),
    "C2": ("Zonas con asientos fijos", 4.0, 4.0),
    "C3": ("Zonas sin obstáculos que impidan el libre movimiento", 5.0, 4.0),
    "C4": ("Zonas destinadas a gimnasio u actividades físicas", 5.0, 7.0),
    "C5": ("Zonas de aglomeración (salas de conciertos, estadios...)", 5.0, 4.0),
    "D1": ("Locales comerciales", 5.0, 4.0),
    "D2": ("Supermercados, hipermercados o grandes superficies", 5.0, 7.0),
    "E":  ("Zonas de tráfico y aparcamiento de vehículos ligeros", 2.0, 20.0),
    "F":  ("Cubiertas transitables accesibles sólo privadamente", 1.0, 2.0),
    "G1": ("Cubiertas accesibles únicamente para conservación (incl. < 20º)", 1.0, 2.0),
}

# Tabla 3.3 DB-SE-AE: fuerza horizontal en barandillas (kN/m) aplicada en el borde superior
def carga_barandilla(uso):
    if uso == "C5":
        return 3.0
    if uso in ("C3", "C4", "E", "F"):
        return 1.6
    return 0.8

# Altura mínima de barandilla DB-SUA 1, 3.2.1
def altura_barandilla(desnivel_m):
    return 0.90 if desnivel_m <= 6.0 else 1.10

# DB-SE tabla 4.1: coeficientes parciales de seguridad (persistente/transitoria)
GAMMA_G, GAMMA_G_FAV = 1.35, 0.80
GAMMA_Q, GAMMA_Q_FAV = 1.50, 0.0

# DB-SE tabla 4.2: coeficientes de simultaneidad (psi0, psi1, psi2)
PSI = {
    "A": (0.7, 0.5, 0.3), "B": (0.7, 0.5, 0.3), "C": (0.7, 0.7, 0.6),
    "D": (0.7, 0.7, 0.6), "E": (0.7, 0.7, 0.6), "F": (0.0, 0.0, 0.0),
    "G": (0.0, 0.0, 0.0), "nieve": (0.5, 0.2, 0.0), "viento": (0.6, 0.5, 0.0),
}

def psi_uso(uso):
    return PSI[uso[0]]

# DB-SE 4.3.3.1 limites de flecha relativa
FLECHA_INTEGRIDAD = {  # flecha activa, combinación característica
    "fragil": 500,     # tabiques frágiles o pavimentos rígidos sin juntas
    "ordinaria": 400,  # tabiques ordinarios o pavimentos rígidos con juntas
    "resto": 300,      # resto de casos
}
FLECHA_CONFORT = 350      # sólo acciones de corta duración (combinación característica)
FLECHA_APARIENCIA = 300   # combinación casi permanente

# DB-SE-AE Anejo C (tablas C.1 a C.5): pesos orientativos de elementos constructivos (kN/m²)
PESOS_TIPICOS = {
    "tablero_osb_22": 0.15,       # tablero OSB/contrachapado 22 mm (~650 kg/m³)
    "pavimento_ligero": 0.50,     # tarima/laminado/vinílico sobre base
    "pavimento_ceramico": 1.00,   # C.5: pavimento cerámico sobre plastón, < 0,08 m
    "falso_techo_yeso": 0.15,     # placa de yeso laminado 15 mm + perfilería
    "instalaciones": 0.10,
    "tabiqueria_vivienda": 1.00,  # DB-SE-AE 2.1(5): tabiquería ordinaria en viviendas
}

# ---------------------------------------------------------------- DB-SE-A (acero)
ACEROS = {  # fy (t<=16), fu   (DB-SE-A tabla 4.1)
    "S235": (235.0, 360.0), "S275": (275.0, 410.0), "S355": (355.0, 470.0),
}
BETA_W = {"S235": 0.80, "S275": 0.85, "S355": 0.90}  # DB-SE-A tabla 8.1
GAMMA_M0, GAMMA_M1, GAMMA_M2 = 1.05, 1.05, 1.25      # DB-SE-A 2.3.3
E_ACERO, G_ACERO = 210000.0, 81000.0
ALPHA_PANDEO = {"a0": 0.13, "a": 0.21, "b": 0.34, "c": 0.49, "d": 0.76}  # DB-SE-A tabla 6.3

def chi_pandeo(lam, curva):
    a = ALPHA_PANDEO[curva]
    if lam <= 0.2:
        return 1.0
    phi = 0.5 * (1 + a * (lam - 0.2) + lam ** 2)
    return min(1.0, 1.0 / (phi + math.sqrt(phi ** 2 - lam ** 2)))

# Tornillos: área resistente y fub (DB-SE-A 8.5)
TORNILLOS_AS = {12: 84.3, 16: 157.0, 20: 245.0, 24: 353.0}
CLASES_TORNILLO = {"4.6": (240.0, 400.0), "5.6": (300.0, 500.0), "8.8": (640.0, 800.0), "10.9": (900.0, 1000.0)}

# ---------------------------------------------------------------- DB-SE-M (madera)
# Tablas E.1 (UNE-EN 338) y E.3 (UNE-EN 1194) DB-SE-M. fm,k, fv,k, fc90,k, E0,medio, E0,05, rho_k, rho_medio
MADERAS = {
    "C18":   dict(fm=18.0, fv=2.0, fc90=2.2, E=9000.0, E05=6000.0, rho_k=320, rho_m=380, tipo="maciza"),
    "C24":   dict(fm=24.0, fv=2.5, fc90=2.5, E=11000.0, E05=7400.0, rho_k=350, rho_m=420, tipo="maciza"),
    "C30":   dict(fm=30.0, fv=3.0, fc90=2.7, E=12000.0, E05=8000.0, rho_k=380, rho_m=460, tipo="maciza"),
    "GL24h": dict(fm=24.0, fv=2.7, fc90=2.7, E=11600.0, E05=9400.0, rho_k=380, rho_m=420, tipo="laminada"),
    "GL28h": dict(fm=28.0, fv=3.2, fc90=3.0, E=12600.0, E05=10200.0, rho_k=410, rho_m=450, tipo="laminada"),
    "GL32h": dict(fm=32.0, fv=3.8, fc90=3.3, E=13700.0, E05=11100.0, rho_k=430, rho_m=470, tipo="laminada"),
}
GAMMA_M_MADERA = {"maciza": 1.30, "laminada": 1.25}           # DB-SE-M tabla 2.3
KMOD = {1: {"permanente": 0.60, "larga": 0.70, "media": 0.80, "corta": 0.90, "instantanea": 1.10},
        2: {"permanente": 0.60, "larga": 0.70, "media": 0.80, "corta": 0.90, "instantanea": 1.10},
        3: {"permanente": 0.50, "larga": 0.55, "media": 0.65, "corta": 0.70, "instantanea": 0.90}}  # tabla 2.4
KDEF = {1: 0.60, 2: 0.80, 3: 2.00}                             # tabla 5.1 (maciza/laminada)
# Duración de la sobrecarga de uso (DB-SE-M tabla 2.2): vivienda/oficina -> media; mantenimiento -> corta
DURACION_USO = {"A": "media", "B": "media", "C": "media", "D": "media", "E": "media", "F": "corta", "G": "corta"}

def kh_madera(h_mm, tipo):
    """Factor de altura DB-SE-M 2.2.1.2."""
    if tipo == "maciza":
        return min((150.0 / h_mm) ** 0.2, 1.3) if h_mm < 150 else 1.0
    return min((600.0 / h_mm) ** 0.1, 1.1) if h_mm < 600 else 1.0

SECCIONES_MADERA = {
    "maciza": [(45, 145), (45, 195), (70, 145), (70, 170), (70, 195), (70, 220), (70, 245),
               (95, 195), (95, 220), (95, 245), (120, 245), (145, 245)],
    "laminada": [(b, h) for h in range(160, 1001, 40) for b in (80, 100, 120, 140, 160, 200)
                 if h / b <= 6.0],
}

# ---------------------------------------------------------------- Código Estructural (hormigón)
HORMIGONES = {"HA-25": 25.0, "HA-30": 30.0, "HA-35": 35.0}
ARMADURAS = {"B400S": 400.0, "B500S": 500.0, "B500SD": 500.0}
GAMMA_C, GAMMA_S = 1.50, 1.15
BARRAS = {8: 50.3, 10: 78.5, 12: 113.1, 16: 201.1, 20: 314.2, 25: 490.9}
RHO_MIN_ZAPATA = 0.0009   # cuantía geométrica mínima por dirección en cara inferior (criterio: mitad de 1,8 ‰ de losas, B500S)
CANTO_MIN_ZAPATA = 0.25   # Código Estructural: canto mínimo en el borde de zapatas de hormigón armado

# ---------------------------------------------------------------- Perfiles de acero
# IPE (h, b, tw, tf, r) mm — UNE-EN 10365
IPE = {80: (80, 46, 3.8, 5.2, 5), 100: (100, 55, 4.1, 5.7, 7), 120: (120, 64, 4.4, 6.3, 7),
       140: (140, 73, 4.7, 6.9, 7), 160: (160, 82, 5.0, 7.4, 9), 180: (180, 91, 5.3, 8.0, 9),
       200: (200, 100, 5.6, 8.5, 12), 220: (220, 110, 5.9, 9.2, 12), 240: (240, 120, 6.2, 9.8, 15),
       270: (270, 135, 6.6, 10.2, 15), 300: (300, 150, 7.1, 10.7, 15), 330: (330, 160, 7.5, 11.5, 18),
       360: (360, 170, 8.0, 12.7, 18), 400: (400, 180, 8.6, 13.5, 21), 450: (450, 190, 9.4, 14.6, 21),
       500: (500, 200, 10.2, 16.0, 21)}
HEB = {100: (100, 100, 6.0, 10.0, 12), 120: (120, 120, 6.5, 11.0, 12), 140: (140, 140, 7.0, 12.0, 12),
       160: (160, 160, 8.0, 13.0, 15), 180: (180, 180, 8.5, 14.0, 15), 200: (200, 200, 9.0, 15.0, 18),
       220: (220, 220, 9.5, 16.0, 18), 240: (240, 240, 10.0, 17.0, 21), 260: (260, 260, 10.0, 17.5, 24),
       280: (280, 280, 10.5, 18.0, 24), 300: (300, 300, 11.0, 19.0, 27)}
# Tubo cuadrado conformado en frío (UNE-EN 10219): (lado, espesor)
SHS = [(60, 3), (60, 4), (70, 4), (80, 4), (80, 5), (90, 5), (100, 4), (100, 5), (100, 6),
       (120, 5), (120, 6), (140, 6), (150, 6), (150, 8), (160, 8), (180, 8), (200, 8), (200, 10)]


def _raster_props(mask, d):
    """Propiedades a partir de una máscara booleana (celda de lado d mm), simétrica respecto a ambos ejes."""
    ny, nx = mask.shape
    y = (np.arange(ny) - (ny - 1) / 2) * d
    x = (np.arange(nx) - (nx - 1) / 2) * d
    Y, X = np.meshgrid(y, x, indexing="ij")
    dA = d * d
    A = mask.sum() * dA
    Iy = (mask * Y ** 2).sum() * dA
    Iz = (mask * X ** 2).sum() * dA
    Wply = (mask * np.abs(Y)).sum() * dA
    Wplz = (mask * np.abs(X)).sum() * dA
    return A, Iy, Iz, Wply, Wplz


def perfil_I(serie, n):
    h, b, tw, tf, r = (IPE if serie == "IPE" else HEB)[n]
    d = 0.25 if h <= 300 else 0.5
    ys = (np.arange(int(h / d)) + 0.5) * d - h / 2
    xs = (np.arange(int(b / d)) + 0.5) * d - b / 2
    Y, X = np.meshgrid(ys, xs, indexing="ij")
    ala = np.abs(Y) >= h / 2 - tf
    alma = np.abs(X) <= tw / 2
    # acuerdos alma-ala
    cx, cy = tw / 2 + r, h / 2 - tf - r
    zona = (np.abs(X) <= cx) & (np.abs(Y) >= cy) & (np.abs(Y) < h / 2 - tf)
    fuera = (np.abs(X) - cx) ** 2 + (np.abs(Y) - cy) ** 2 >= r ** 2
    acuerdo = zona & fuera & (np.abs(X) > tw / 2)
    mask = ala | alma | acuerdo
    A, Iy, Iz, Wply, Wplz = _raster_props(mask, d)
    It = (2 * b * tf ** 3 + (h - 2 * tf) * tw ** 3) / 3.0
    Iw = Iz * (h - tf) ** 2 / 4.0
    Av = max(A - 2 * b * tf + (tw + 2 * r) * tf, (h - 2 * tf) * tw)
    return dict(nombre=f"{serie} {n}", serie=serie, h=h, b=b, tw=tw, tf=tf, r=r, A=A, Iy=Iy, Iz=Iz,
                Wely=Iy / (h / 2), Wply=Wply, Welz=Iz / (b / 2), Wplz=Wplz, It=It, Iw=Iw, Av=Av,
                peso=A * 7850e-6 * 9.81e-3)  # kN/m


def perfil_SHS(lado, t):
    b = lado
    ro, ri = 2.0 * t, 1.0 * t
    d = 0.1 if b <= 120 else 0.2
    xs = (np.arange(int(b / d)) + 0.5) * d - b / 2
    Y, X = np.meshgrid(xs, xs, indexing="ij")

    def redondeado(semilado, rad):
        dentro = (np.abs(X) <= semilado) & (np.abs(Y) <= semilado)
        c = semilado - rad
        esquina = (np.abs(X) > c) & (np.abs(Y) > c)
        return dentro & ~(esquina & ((np.abs(X) - c) ** 2 + (np.abs(Y) - c) ** 2 > rad ** 2))

    mask = redondeado(b / 2, ro) & ~redondeado(b / 2 - t, ri)
    A, Iy, Iz, Wply, Wplz = _raster_props(mask, d)
    Am = (b - t) ** 2
    It = 4 * Am ** 2 * t / (4 * (b - t))
    return dict(nombre=f"SHS {lado}x{t}", serie="SHS", h=b, b=b, t=t, A=A, Iy=Iy, Iz=Iz,
                Wely=Iy / (b / 2), Wply=Wply, Welz=Iz / (b / 2), Wplz=Wplz, It=It, Iw=0.0,
                Av=A / 2, i=math.sqrt(Iy / A), peso=A * 7850e-6 * 9.81e-3)


@lru_cache(maxsize=None)
def perfil(nombre):
    """'IPE 200', 'HEB 160', 'SHS 100x5'."""
    serie, dim = nombre.split()
    if serie in ("IPE", "HEB"):
        return perfil_I(serie, int(dim))
    lado, t = dim.lower().split("x")
    return perfil_SHS(int(lado), float(t))


def catalogo(serie):
    if serie == "IPE":
        return [f"IPE {n}" for n in IPE]
    if serie == "HEB":
        return [f"HEB {n}" for n in HEB]
    if serie == "SHS":  # ordenados por peso (área) para que el primero que cumple sea el más ligero
        return sorted((f"SHS {l}x{t}" for l, t in SHS), key=lambda p: perfil(p)["A"])
    raise ValueError(serie)
