"""Generador de planos de estructura (matplotlib → PDF vectorial) con el cajetín de
ARISTOSIA PROJECTS (formato de referencia: PLANO_00B, A3 apaisado, panel lateral derecho).

Todo se dibuja en milímetros de papel A3 (420 × 297). Para A1 se escala el conjunto (k = 2)
y la escala nominal de cada vista se ajusta en el rótulo.
"""
import math
import os
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon, Circle
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.image as mpimg

import normativa as N

PT = 72 / 25.4           # puntos por mm
GRIS = "#e6e6e6"
GRIS_M = "#bdbdbd"
NEGRO = "#000000"
LW_F, LW_M, LW_G, LW_MG = 0.18, 0.35, 0.6, 0.9   # grosores de línea (pt a escala A3)
ESCALAS = [5, 10, 15, 20, 25, 50, 75, 100, 150, 200]
FORMATOS = {"A3": (420.0, 297.0, 1.0), "A1": (420.0, 297.0, 841.0 / 420.0)}
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _w(s, size):
    """Ancho aproximado (mm) de un texto con DejaVu Sans."""
    return len(s) * size * 0.52


def wrap(s, ancho_mm, size):
    n = max(8, int(ancho_mm / (size * 0.52)))
    return textwrap.wrap(s, n) or [""]


# ============================================================================ hoja
class Hoja:
    W, H = 420.0, 297.0
    M = 5.5            # margen del marco
    PX = 301.5         # inicio del panel lateral
    PAD = 4.0

    def __init__(self, cfg, numero, titulo, escala_txt, idx, total, cabecera):
        self.cfg = cfg
        self.k = FORMATOS[cfg["proyecto"].get("formato", "A3")][2]
        self.fig = plt.figure(figsize=(self.W * self.k / 25.4, self.H * self.k / 25.4))
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.ax.set_xlim(0, self.W)
        self.ax.set_ylim(0, self.H)
        self.ax.set_aspect("equal")
        self.ax.axis("off")
        self.numero, self.titulo, self.escala_txt = numero, titulo, escala_txt
        self.idx, self.total, self.cabecera = idx, total, cabecera
        self._marco()
        self.panel_y = self.H - self.M - self.PAD - 9   # cursor para cajas del panel (de arriba abajo)

    # -------------------------------------------------------------- primitivas
    def t(self, x, y, s, size=2.0, bold=False, ha="left", va="baseline", rot=0, color=NEGRO, italic=False):
        self.ax.text(x, y, s, fontsize=size * PT * self.k * 0.72 / 0.72 / 1.0 * 0.85, fontweight="bold" if bold else "normal",
                     ha=ha, va=va, rotation=rot, color=color, family="DejaVu Sans",
                     style="italic" if italic else "normal", zorder=10)

    def l(self, xs, ys, lw=LW_M, ls="-", color=NEGRO, z=3):
        self.ax.plot(xs, ys, lw=lw * self.k, ls=ls, color=color, solid_capstyle="butt", zorder=z)

    def r(self, x, y, w, h, lw=LW_M, fc="none", ec=NEGRO, ls="-", hatch=None, z=2):
        self.ax.add_patch(Rectangle((x, y), w, h, lw=lw * self.k, fc=fc, ec=ec, ls=ls, hatch=hatch, zorder=z))

    def poly(self, pts, lw=LW_M, fc="none", ec=NEGRO, hatch=None, z=2):
        self.ax.add_patch(Polygon(pts, closed=True, lw=lw * self.k, fc=fc, ec=ec, hatch=hatch, zorder=z))

    def c(self, x, y, rad, lw=LW_M, fc="white", ec=NEGRO, z=5):
        self.ax.add_patch(Circle((x, y), rad, lw=lw * self.k, fc=fc, ec=ec, zorder=z))

    # -------------------------------------------------------------- marco y cajetín
    def _marco(self):
        M, W, H = self.M, self.W, self.H
        self.r(M, M, W - 2 * M, H - 2 * M, lw=LW_MG)
        self.l([self.PX, self.PX], [M, H - M], lw=LW_G)
        # cabecera del panel
        self.t(self.PX + self.PAD, H - M - 6.0, self.cabecera.upper(), 2.4, bold=True)
        self.l([self.PX + self.PAD, W - M - self.PAD], [H - M - 8.0] * 2, lw=LW_M)
        self._cajetin()

    def _cajetin(self):
        p = self.cfg["proyecto"]
        x0, x1 = self.PX + self.PAD, self.W - self.M - self.PAD
        w = x1 - x0
        y = self.M + self.PAD
        hs = [14.0, 6.8, 7.1, 8.6, 10.0, 18.3]   # autores, fecha, escala gráfica, nº plano, título, proyecto
        tops = [y]
        for h in hs:
            tops.append(tops[-1] + h)
        self.caj_top = tops[-1]
        self.r(x0, y, w, tops[-1] - y, lw=LW_G, z=4)
        for yy in tops[1:-1]:
            self.l([x0, x1], [yy, yy], lw=LW_M)
        # PROYECTO
        yb, yt = tops[5], tops[6]
        self.t(x0 + 1.2, yt - 2.4, "PROYECTO", 1.55)
        lineas = [p["titulo"].upper()] + ([p["subtitulo"].upper()] if p.get("subtitulo") else []) + \
                 ([p["emplazamiento"].upper()] if p.get("emplazamiento") else [])
        yy = yt - 5.4
        for s in lineas[:3]:
            for sub in wrap(s, w - 36, 2.15)[:2]:
                self.t(x0 + 1.2, yy, sub, 2.15, bold=True)
                yy -= 2.7
        if p.get("promotor"):
            self.t(x0 + 1.2, yb + 1.6, f"Promotor: {p['promotor']}", 1.6)
        logo = p.get("logo")
        if logo:
            lp = logo if os.path.isabs(logo) else os.path.join(BASE, logo)
            if os.path.exists(lp):
                img = mpimg.imread(lp)
                lw_, lh_ = 30.0, 30.0 * img.shape[0] / img.shape[1]
                lx, ly = x1 - lw_ - 1.0, yt - lh_ - 1.2
                self.ax.imshow(img, extent=(lx, lx + lw_, ly, ly + lh_), zorder=6, interpolation="bicubic")
                self.t(lx + lw_ / 2, ly - 2.6, "Redacta", 1.55, ha="center")
        # TÍTULO DEL PLANO
        yb, yt = tops[4], tops[5]
        self.r(x0, yb, w, yt - yb, lw=0, fc=GRIS, ec="none", z=1)
        self.t(x0 + 1.2, yt - 2.3, "TÍTULO DEL PLANO", 1.55)
        yy = yt - 5.2
        for s in self.titulo.upper().split("\n")[:2]:
            self.t(x0 + 1.2, yy, s, 2.25, bold=True)
            yy -= 2.7
        # Nº PLANO / HOJA / ESCALA
        yb, yt = tops[3], tops[4]
        c1, c2 = x0 + 0.24 * w, x0 + 0.42 * w
        self.l([c1, c1], [yb, yt]); self.l([c2, c2], [yb, yt])
        self.t(x0 + 1.2, yt - 2.2, "Nº PLANO", 1.55)
        self.t((x0 + c1) / 2, yb + 1.8, self.numero, 2.7, bold=True, ha="center")
        self.t(c1 + 1.2, yt - 2.2, "HOJA", 1.55)
        self.t((c1 + c2) / 2, yb + 1.8, f"{self.idx}/{self.total}", 2.7, bold=True, ha="center")
        self.t(c2 + 1.2, yt - 2.2, "ESCALA · FORMATO", 1.55)
        # el valor de ESCALA se escribe al final (_reescribir_escala), cuando la vista ya la ha fijado
        # ESCALA GRÁFICA / NORMATIVA
        yb, yt = tops[2], tops[3]
        self.t(x0 + 1.2, yt - 2.2, "NORMATIVA", 1.55)
        self.t(x0 + 1.2, yb + 1.3, "CTE DB-SE · SE-AE · SE-A · SE-M · SE-C", 1.65)
        self.t(x0 + 0.55 * w, yt - 2.6, "Código Estructural (RD 470/2021)", 1.65)
        self.t(x0 + 0.55 * w, yb + 1.3, "NCSE-02 · DB-SI 6", 1.65)
        # FECHA
        yb, yt = tops[1], tops[2]
        self.t(x0 + 1.2, yt - 2.6, f"FECHA: {p.get('fecha', '')} · {p.get('estudio', '')}", 1.65)
        self.t(x0 + 1.2, yb + 1.0, f"Impresión {p.get('formato','A3')} al 100 % · Exp. {p.get('codigo', '')} · "
               f"Documento preliminar: requiere revisión y firma", 1.55)
        # AUTORES / FIRMAS
        yb, yt = tops[0], tops[1]
        self.t(x0 + 1.2, yt - 2.2, "AUTORES DEL PLANO / FIRMAS", 1.55)
        autores = p.get("autores", [])[:2] or [dict(nombre="", titulo="")]
        n = len(autores)
        for i, a in enumerate(autores):
            ax0 = x0 + i * w / n
            if i:
                self.l([ax0, ax0], [yb, yt])
            cx = ax0 + w / n / 2
            self.t(cx, yt - 4.8, a["nombre"], 1.9, bold=True, ha="center")
            self.t(cx, yt - 7.2, a.get("titulo", ""), 1.6, ha="center")
            self.r(ax0 + 4, yb + 1.2, w / n - 8, 4.4, lw=LW_F)

    # -------------------------------------------------------------- cajas del panel
    def caja_panel(self, titulo, filas=None, lineas=None, cols=None, size=1.65, alto_fila=3.0, sombrear=False):
        """Caja del panel con tabla (filas + cols=proporciones) o líneas de texto. Se apila hacia abajo."""
        x0, x1 = self.PX + self.PAD, self.W - self.M - self.PAD
        w = x1 - x0
        cont = []
        if filas:
            cont = filas
        txt = []
        for s in (lineas or []):
            txt += wrap(s, w - 3, size)
        h = 4.6 + len(cont) * alto_fila + len(txt) * size * 1.45 + 1.5
        y1 = self.panel_y
        y0 = y1 - h
        if y0 < self.caj_top + 2:
            return False
        self.r(x0, y0, w, h, lw=LW_F, ec="#888888", fc="#fafafa" if not sombrear else GRIS, z=1)
        self.t(x0 + 1.5, y1 - 3.2, titulo, 1.85, bold=True)
        yy = y1 - 4.6
        if cont:
            cols = cols or [1.0 / len(cont[0])] * len(cont[0])
            xs = [x0 + 1.5]
            for f in cols[:-1]:
                xs.append(xs[-1] + f * (w - 3))
            for j, fila in enumerate(cont):
                yy -= alto_fila
                if j == 0:
                    self.r(x0 + 1, yy - 0.6, w - 2, alto_fila, lw=0, fc=GRIS, ec="none", z=1)
                for xi, val in zip(xs, fila):
                    self.t(xi, yy + 0.3, str(val), size, bold=(j == 0))
                if j < len(cont) - 1:
                    self.l([x0 + 1, x1 - 1], [yy - 0.6] * 2, lw=0.1, color="#999999")
        for s in txt:
            yy -= size * 1.45
            self.t(x0 + 1.5, yy, s, size)
        self.panel_y = y0 - 2.0
        return True

    # -------------------------------------------------------------- utilidades de dibujo técnico
    def titulo_vista(self, x, y, num, titulo, escala):
        self.c(x + 3.2, y + 1.2, 3.2, lw=LW_G)
        self.l([x + 0.4, x + 6.0], [y + 1.2, y + 1.2], lw=LW_F)
        self.t(x + 3.2, y + 2.0, str(num), 2.1, bold=True, ha="center")
        self.t(x + 3.2, y - 1.0, self.numero, 1.35, ha="center")
        self.t(x + 8.0, y + 1.0, titulo.upper(), 2.5, bold=True)
        self.l([x + 8.0, x + 8.0 + _w(titulo, 2.5) * 0.92], [y - 0.3, y - 0.3], lw=LW_G)
        self.t(x + 8.0, y - 2.8, f"ESCALA {escala}", 1.7)

    def cota(self, x1, y1, x2, y2, off, txt=None, size=1.7, ext=True):
        """Cota alineada con trazos oblicuos. off > 0 desplaza a la izquierda del sentido 1→2."""
        L = math.hypot(x2 - x1, y2 - y1)
        if L < 1e-6:
            return
        ux, uy = (x2 - x1) / L, (y2 - y1) / L
        nx, ny = -uy, ux
        a1 = (x1 + nx * off, y1 + ny * off)
        a2 = (x2 + nx * off, y2 + ny * off)
        if ext:
            s = 1 if off >= 0 else -1
            self.l([x1 + nx * s * 0.8, a1[0] + nx * s * 1.2], [y1 + ny * s * 0.8, a1[1] + ny * s * 1.2], lw=LW_F)
            self.l([x2 + nx * s * 0.8, a2[0] + nx * s * 1.2], [y2 + ny * s * 0.8, a2[1] + ny * s * 1.2], lw=LW_F)
        self.l([a1[0] - ux * 1.2, a2[0] + ux * 1.2], [a1[1] - uy * 1.2, a2[1] + uy * 1.2], lw=LW_F)
        for (px, py) in (a1, a2):
            dx, dy = (ux + nx) * 0.9, (uy + ny) * 0.9
            self.l([px - dx, px + dx], [py - dy, py + dy], lw=LW_M)
        ang = math.degrees(math.atan2(uy, ux))
        if ang > 90.1 or ang < -89.9:
            ang += 180
        mx, my = (a1[0] + a2[0]) / 2 + nx * 0.8, (a1[1] + a2[1]) / 2 + ny * 0.8
        self.t(mx, my, txt if txt is not None else "", size, ha="center", va="bottom", rot=ang)

    def burbuja(self, x, y, s, rad=2.8):
        self.c(x, y, rad, lw=LW_M)
        self.t(x, y, s, 2.2, bold=True, ha="center", va="center")

    def etiqueta(self, x, y, tx, ty, lineas, size=1.65, ha=None):
        self.c(x, y, 0.35, lw=0, fc=NEGRO)
        ha = ha or ("left" if tx >= x else "right")
        codo = tx + (2.0 if ha == "left" else -2.0)
        self.l([x, tx, codo], [y, ty, ty], lw=LW_F)
        tx2 = codo + (0.6 if ha == "left" else -0.6)
        if isinstance(lineas, str):
            lineas = [lineas]
        for i, s in enumerate(lineas):
            self.t(tx2, ty + 0.7 - i * size * 1.4, s, size, ha=ha, va="center")

    def nivel(self, x, y, txt, lado=1):
        self.poly([(x, y), (x - 1.3, y + 2.0), (x + 1.3, y + 2.0)], lw=LW_F, fc=NEGRO)
        self.l([x, x + lado * 14], [y + 2.0, y + 2.0], lw=LW_F)
        self.t(x + lado * 1.8, y + 2.6, txt, 1.65, ha="left" if lado > 0 else "right")

    def marca_corte(self, x1, y1, x2, y2, letra):
        self.l([x1, x2], [y1, y2], lw=LW_F, ls=(0, (8, 2, 1, 2)))
        L = math.hypot(x2 - x1, y2 - y1)
        ux, uy = (x2 - x1) / L, (y2 - y1) / L
        nx, ny = uy, -ux  # flecha hacia la derecha del sentido 1→2
        for (px, py) in ((x1, y1), (x2, y2)):
            self.l([px - ux * 0, px - ux * 0], [py, py])
            self.poly([(px + nx * 4.0, py + ny * 4.0), (px - ux * 1.4, py - uy * 1.4), (px + ux * 1.4, py + uy * 1.4)],
                      lw=LW_F, fc=NEGRO)
            self.c(px - ux * 4.0, py - uy * 4.0, 2.6, lw=LW_M) if False else None
            self.t(px + nx * 4.0 + nx * 2.5, py + ny * 4.0 + ny * 2.5, letra, 2.6, bold=True, ha="center", va="center")

    def guardar(self, pdf, png=None):
        pdf.savefig(self.fig)
        if png:
            self.fig.savefig(png, dpi=110)
        plt.close(self.fig)


# ============================================================================ utilidades de modelo
def _ejes(cfg):
    g = cfg["geometria"]
    xs = [0.0]
    for v in g["luces_x"]:
        xs.append(xs[-1] + v)
    ys = [0.0]
    for v in g["luces_y"]:
        ys.append(ys[-1] + v)
    return xs, ys


def _letras(n):
    return [chr(ord("A") + i) for i in range(n)]


def _escala(ancho_m, alto_m, aw, ah, margen=30):
    for e in ESCALAS:
        if ancho_m * 1000 / e + margen <= aw and alto_m * 1000 / e + margen <= ah:
            return e
    return ESCALAS[-1]


def _txt_escala(e, k):
    real = e / k
    return f"1:{real:g}" if k == 1 else f"1:{real:.0f}"


def _cotas_verticales(r, cfg):
    """Cotas verticales del conjunto (m, origen en cara superior de solera existente = ±0,00)."""
    c = cfg["cimentacion"]
    zp = r["zapata"]
    z_zap_inf = -zp["prof"]
    z_zap_sup = z_zap_inf + zp["h"]
    z_pil_inf = z_zap_sup + 0.03
    z_pil_sup = z_pil_inf + r["H"]
    tcap = 0.010
    hv = _h_viga(r) / 1000
    z_vinf = z_pil_sup + tcap
    z_vsup = z_vinf + hv
    z_suelo = z_vsup + 0.022
    return dict(zap_inf=z_zap_inf, zap_sup=z_zap_sup, pil_inf=z_pil_inf, pil_sup=z_pil_sup,
                v_inf=z_vinf, v_sup=z_vsup, suelo=z_suelo, tcap=tcap)


def _h_viga(r):
    v = r["viga"]
    return v["perfil"]["h"] if "perfil" in v else v["h"]


def _b_viga(r):
    v = r["viga"]
    return v["perfil"]["b"] if "perfil" in v else v["b"]


def _hj(r):
    v = r["vigueta"]
    return v["perfil"]["h"] if "perfil" in v else v["h"]


def _bj(r):
    v = r["vigueta"]
    return v["perfil"]["b"] if "perfil" in v else v["b"]


def _m(v):
    return f"{v:.2f}".replace(".", ",")


def _desc_vigueta(r, cfg):
    s = cfg["forjado"]["separacion"]
    return f"{r['vigueta']['seccion'].replace('x', '×')} c/{s*100:.0f} cm"


# ============================================================================ dibujo de secciones tipo
def dibujar_I(h, cx, yb, perfil, sc, fc=GRIS_M, lw=LW_M):
    """Sección en I centrada en cx con base en yb. sc: mm papel por mm real."""
    H_, B_, tw, tf = perfil["h"] * sc, perfil["b"] * sc, perfil["tw"] * sc, perfil["tf"] * sc
    pts = [(cx - B_ / 2, yb), (cx + B_ / 2, yb), (cx + B_ / 2, yb + tf), (cx + tw / 2, yb + tf),
           (cx + tw / 2, yb + H_ - tf), (cx + B_ / 2, yb + H_ - tf), (cx + B_ / 2, yb + H_),
           (cx - B_ / 2, yb + H_), (cx - B_ / 2, yb + H_ - tf), (cx - tw / 2, yb + H_ - tf),
           (cx - tw / 2, yb + tf), (cx - B_ / 2, yb + tf)]
    h.poly(pts, lw=lw, fc=fc, z=4)


def dibujar_seccion_viga(h, cx, yb, r, sc, cual="viga"):
    v = r[cual]
    if "perfil" in v:
        dibujar_I(h, cx, yb, v["perfil"], sc)
    else:
        b, hh = v["b"] * sc, v["h"] * sc
        h.r(cx - b / 2, yb, b, hh, lw=LW_M, fc="#f3e3c3", z=4)
        h.l([cx - b / 2, cx + b / 2], [yb, yb + hh], lw=LW_F, z=5)
        h.l([cx - b / 2, cx + b / 2], [yb + hh, yb], lw=LW_F, z=5)


# ============================================================================ PLANOS
def hoja_notas(cfg, r, M, idx, total, indice):
    h = Hoja(cfg, "E-01", "CUADRO DE CARACTERÍSTICAS\nY NOTAS GENERALES", "S/E", idx, total, "Estructura · Notas generales")
    C = r["cargas"]
    mat = cfg["materiales"]
    fmat = cfg["forjado"]["material"]
    zp = r["zapata"]
    colw = (h.PX - h.M - 3 * 6) / 2
    xcols = [h.M + 6, h.M + 6 + colw + 6]
    ycol = [h.H - h.M - 10, h.H - h.M - 10]
    h.t(h.M + 6, h.H - h.M - 6, "CUADRO DE CARACTERÍSTICAS Y NOTAS GENERALES DE ESTRUCTURA", 3.0, bold=True)

    def bloque(i, titulo, lineas, size=2.05):
        x, y = xcols[i], ycol[i] - 4
        h.t(x, y, titulo.upper(), 2.1, bold=True)
        h.l([x, x + colw], [y - 1.0, y - 1.0], lw=LW_M)
        y -= 4.0
        for s in lineas:
            sangria = 2.5 if s[:2] in ("- ", "· ") else 0
            for j, sub in enumerate(wrap(s, colw - sangria, size)):
                h.t(x + (sangria if j else 0), y, sub, size)
                y -= size * 1.42
        ycol[i] = y - 2.0

    psi = C["psi"]
    bloque(0, "1. Normativa de aplicación", [
        "- CTE DB-SE Seguridad estructural · DB-SE-AE Acciones en la edificación.",
        "- CTE DB-SE-A Acero · DB-SE-M Madera · DB-SE-C Cimientos · DB-SI 6 Resistencia al fuego.",
        "- Código Estructural (RD 470/2021): hormigón armado y ejecución de acero.",
        "- NCSE-02 Norma de construcción sismorresistente. " + r["sismo_txt"],
        "- Método de cálculo: estados límite (DB-SE 3.2). Análisis elástico de primer orden, elementos biapoyados.",
    ])
    acc = [f"- Peso propio de la estructura: calculado (acero 78,5 kN/m³; madera {fmat}: densidad media)."]
    acc += [f"- {c['nombre']}: {_m(c['valor'])} kN/m²" for c in C["perm"]]
    acc += [f"- Sobrecarga de uso, categoría {cfg['uso']} ({C['uso_desc'].lower()}): {_m(C['q'])} kN/m²; "
            f"carga concentrada {_m(C['Q'])} kN (DB-SE-AE tabla 3.1).",
            f"- Barandillas: fuerza horizontal {_m(C['hb'])} kN/m en borde superior (DB-SE-AE tabla 3.3)." if C["hb"] else
            "- Sin barandillas.",
            "- Nieve y viento: no actúan (estructura interior). Acción térmica: despreciable (L < 40 m).",
            f"- ψ0/ψ1/ψ2 = {psi[0]}/{psi[1]}/{psi[2]} (DB-SE tabla 4.2). γG = 1,35 (0,80 fav.), γQ = 1,50 (DB-SE tabla 4.1)."]
    bloque(0, "2. Acciones consideradas (DB-SE-AE)", acc)
    lim = N.FLECHA_INTEGRIDAD[cfg.get("tabiqueria_tipo", "ordinaria")]
    bloque(0, "3. Estados límite de servicio (DB-SE 4.3.3)", [
        f"- Integridad: flecha activa ≤ L/{lim} (combinación característica).",
        f"- Confort: flecha por sobrecarga de uso ≤ L/{N.FLECHA_CONFORT}.",
        f"- Apariencia: flecha casi permanente ≤ L/{N.FLECHA_APARIENCIA}.",
        f"- Madera: fluencia kdef = {N.KDEF[cfg.get('clase_servicio', 1)]} (clase de servicio {cfg.get('clase_servicio', 1)}).",
    ])
    bloque(0, "4. Cimentación (DB-SE-C)", [
        f"- Zapatas aisladas de hormigón armado sobre terreno natural. σadm de proyecto = {zp['sadm']:.0f} kPa "
        f"({_txt_fuente(cfg)}). Tipo de construcción {r['geotecnia']['reconocimiento']['tipo']}, grupo de terreno "
        f"{r['geotecnia']['reconocimiento']['grupo']} (DB-SE-C tablas 3.1 y 3.2).",
        f"- Clase de exposición del hormigón de cimentación: {r['geotecnia']['durabilidad']['clase']}.",
        f"- Cota de apoyo −{_m(zp['prof'])} m respecto a cara superior de solera existente (±0,00). Hormigón de limpieza "
        f"HL-150/B/20 de 10 cm.",
        "- Si aparecen rellenos, terreno blando o agua, avisar a la Dirección Facultativa antes de hormigonar.",
        "- Demoler y reponer la solera en el entorno de cada zapata; no descalzar cimentaciones existentes.",
    ])
    fy_p = N.ACEROS[mat["pilares"]][0]
    tab = [
        "HORMIGÓN ESTRUCTURAL (Código Estructural):",
        f"- Zapatas: {mat['hormigon']}/B/20/{r['geotecnia']['durabilidad']['clase']} · nivel de control estadístico · γc = 1,50.",
        f"- Recubrimiento nominal: {zp['rec']*1000:.0f} mm (con hormigón de limpieza). Consistencia blanda, árido 20 mm.",
        f"ACERO EN BARRAS: {mat['armadura']} · fyk = {N.ARMADURAS[mat['armadura']]:.0f} MPa · nivel de control normal · γs = 1,15.",
        f"ACERO ESTRUCTURAL: perfiles laminados y chapas {mat['vigas']}JR (fy = {N.ACEROS[mat['vigas']][0]:.0f} MPa), "
        f"tubos conformados {mat['pilares']}J2H (UNE-EN 10219) · γM0 = γM1 = 1,05 · γM2 = 1,25.",
        f"- Tornillos clase {r['union']['clase']} (UNE-EN 15048 / 14399). Soldadura: electrodo E42/E46 (fu ≥ fu metal base).",
    ]
    if fmat in N.MADERAS:
        mm = N.MADERAS[fmat]
        tab.append(f"MADERA: {fmat} ({'aserrada' if mm['tipo']=='maciza' else 'laminada encolada'}), marcado CE, "
                   f"clase de servicio {cfg.get('clase_servicio', 1)}, clase de uso 1 · γM = {N.GAMMA_M_MADERA[mm['tipo']]}. "
                   f"fm,k = {mm['fm']:.0f} MPa · E0,medio = {mm['E']:.0f} MPa.")
    tab.append(f"TABLERO: {cfg['forjado'].get('tablero', 'tablero estructural OSB/3 22 mm')} (tipo estructural, UNE-EN 300 / 13986).")
    bloque(1, "5. Materiales y coeficientes de seguridad", tab)
    bloque(1, "6. Ejecución de estructura metálica", [
        "- Fabricación y montaje según Código Estructural (anejos de ejecución) y DB-SE-A 10/11. Clase de ejecución EXC2.",
        "- Soldaduras en taller por soldador homologado; espesor de garganta indicado en detalles (mín. 4 mm). "
        "Uniones de obra atornilladas.",
        f"- Protección: chorreado Sa 2½ + imprimación anticorrosiva. Resistencia al fuego {r['fuego']} (DB-SI 6): "
        "pintura intumescente certificada o protección pasiva según cálculo del fabricante.",
        "- Placas de anclaje sobre mortero sin retracción (≥ 40 MPa), espesor 20-30 mm, una vez nivelado el pilar.",
        f"- Anclajes: {r['placa']['pernos']}.",
    ])
    est = cfg["estabilidad"]["tipo"]
    estxt = {"muro": "Arriostramiento horizontal: el tablero actúa como diafragma y se ancla al muro existente "
                     "(ver detalle). Verificar en obra la naturaleza y estado del muro.",
             "pilares_empotrados": "Estabilidad lateral por empotramiento de los pilares en las zapatas (ménsulas).",
             "cruces": "Estabilidad lateral mediante cruces de San Andrés de redondo en los vanos indicados."}[est]
    bloque(1, "7. Forjado y estabilidad", [
        f"- Viguetas {_desc_vigueta(r, cfg)}, enrasadas con las vigas, con estribos metálicos con ETA en cada extremo "
        f"(capacidad ≥ {_m(r['R_vigueta'])} kN).",
        "- Tablero machihembrado, encolado y atornillado a viguetas (tornillos 5×60 c/15 cm en bordes, c/30 cm en interior). "
        "Juntas a tresbolillo, testas sobre vigueta.",
        f"- {estxt}",
        f"- Altura libre bajo vigas: {_m(_cotas_verticales(r, cfg)['v_inf'])} m (comprobar con proyecto de arquitectura).",
    ])
    bloque(1, "8. Notas generales", [
        "- Las cotas prevalecen sobre la medición a escala. Comprobar en obra todas las dimensiones y el estado de la "
        "estructura existente antes de fabricar.",
        "- Cualquier cambio de material o sección requiere aprobación de la Dirección Facultativa.",
        "- Plan de control de calidad según CTE parte I anejo II y Código Estructural.",
        "- DOCUMENTO PRELIMINAR GENERADO CON AYUDA DE IA: debe ser revisado y firmado por técnico competente.",
    ])
    h.caja_panel("ÍNDICE DE PLANOS", filas=[("Nº", "TÍTULO")] + indice, cols=[0.18, 0.82])
    tot = r["Lj"], r["Lb"]
    xs, ys = _ejes(cfg)
    h.caja_panel("RESUMEN DE LA ESTRUCTURA", lineas=[
        f"Planta {_m(xs[-1])} × {_m(ys[-1])} m entre ejes; altura de pilar {_m(r['H'])} m.",
        f"Viguetas: {_desc_vigueta(r, cfg)}.",
        f"Vigas principales VP: {r['viga']['seccion']} {mat['vigas'] if mat['vigas'] in N.ACEROS else ''}.",
        f"Zunchos ZU: {r['zuncho']['seccion']}.",
        f"Pilares P: {r['pilar']['seccion']} {mat['pilares']}, placa {r['placa']['a']}×{r['placa']['a']}×{r['placa']['t']} mm.",
        f"Zapatas Z: {_m(zp['B'])}×{_m(zp['B'])}×{_m(zp['h'])} m, {zp['n']}Ø{zp['phi']} c/{zp['sep']*100:.0f} cm "
        f"por dirección.",
        f"Resultado: {'TODAS LAS COMPROBACIONES CUMPLEN' if r['ok'] else 'HAY COMPROBACIONES QUE NO CUMPLEN'}.",
    ])
    return h


def _plano_base(h, cfg, r, cimentacion):
    xs, ys = _ejes(cfg)
    aw, ah = h.PX - h.M - 20, h.H - 2 * h.M - 30
    e = _escala(xs[-1], ys[-1], aw, ah, margen=60)
    sc = 1.0 / e  # mm papel por mm real
    W_, H_ = xs[-1] * 1000 * sc, ys[-1] * 1000 * sc
    ox = h.M + 12 + (aw - W_) / 2 + 6
    oy = h.M + 20 + (ah - H_) / 2 + 2
    P = lambda x, y: (ox + x * 1000 * sc, oy + y * 1000 * sc)
    ob = max(17.0, r["zapata"]["B"] * 1000 * sc / 2 + 9) if cimentacion else 17.0  # burbujas fuera de zapatas
    oc = ob - 9  # cotas
    # ejes
    letras = _letras(len(xs))
    for i, x in enumerate(xs):
        px, _ = P(x, 0)
        h.l([px, px], [oy - ob + 3, oy + H_ + ob - 3], lw=LW_F, ls=(0, (10, 2, 1.5, 2)), color="#555555", z=1)
        h.burbuja(px, oy + H_ + ob, letras[i])
        h.burbuja(px, oy - ob, letras[i])
    for j, y in enumerate(ys):
        _, py = P(0, y)
        h.l([ox - ob + 3, ox + W_ + ob - 3], [py, py], lw=LW_F, ls=(0, (10, 2, 1.5, 2)), color="#555555", z=1)
        h.burbuja(ox - ob, py, str(j + 1))
        h.burbuja(ox + W_ + ob, py, str(j + 1))
    # cotas entre ejes
    for i in range(len(xs) - 1):
        h.cota(*P(xs[i], ys[-1]), *P(xs[i + 1], ys[-1]), oc, _m(xs[i + 1] - xs[i]))
    if len(xs) > 2:
        h.cota(*P(0, ys[-1]), *P(xs[-1], ys[-1]), oc + 4, _m(xs[-1]))
    for j in range(len(ys) - 1):
        h.cota(*P(xs[0], ys[j]), *P(xs[0], ys[j + 1]), oc, _m(ys[j + 1] - ys[j]))
    if len(ys) > 2:
        h.cota(*P(0, 0), *P(0, ys[-1]), oc + 4, _m(ys[-1]))
    return xs, ys, P, sc, e, ox, oy, W_, H_


def _pilares(h, xs, ys, P, sc, r, etiquetas=True):
    b = max(r["pilar"]["perfil"]["b"] * sc, 1.6)
    n = 1
    pos = {}
    for j, y in enumerate(ys):
        for i, x in enumerate(xs):
            px, py = P(x, y)
            h.r(px - b / 2, py - b / 2, b, b, lw=LW_M, fc=NEGRO, z=6)
            pos[(i, j)] = (px, py, n)
            n += 1
    return pos


def hoja_cimentacion(cfg, r, idx, total):
    h = Hoja(cfg, "E-02", "PLANTA DE CIMENTACIÓN\nCUADROS DE ZAPATAS Y PILARES", "", idx, total, "Estructura · Cimentación")
    xs, ys, P, sc, e, ox, oy, W_, H_ = _plano_base(h, cfg, r, True)
    zp = r["zapata"]
    B = zp["B"] * 1000 * sc
    for j, y in enumerate(ys):
        for i, x in enumerate(xs):
            px, py = P(x, y)
            h.r(px - B / 2, py - B / 2, B, B, lw=LW_G, fc="#f0f0f0", ls="--", z=2)
    pos = _pilares(h, xs, ys, P, sc, r)
    for (i, j), (px, py, n) in pos.items():
        h.t(px + B / 2 + 0.8, py + B / 2 + 0.6, f"Z-1 · P-{n}", 1.65, bold=True)
    # cotas de zapata en la primera
    px, py, _ = pos[(0, 0)]
    h.cota(px + B / 2, py - B / 2, px + B / 2, py + B / 2, -4, _m(zp["B"]))
    h.t(h.M + 6, h.M + 8, "", 1)
    h.titulo_vista(h.M + 8, h.M + 9, 1, "Planta de cimentación", _txt_escala(e, h.k))
    h.escala_txt = _txt_escala(e, h.k)
    h.caja_panel("CUADRO DE ZAPATAS", filas=[
        ("MARCA", "DIMENSIONES (m)", "ARMADO INFERIOR"),
        ("Z-1", f"{_m(zp['B'])}×{_m(zp['B'])}×{_m(zp['h'])}", f"{zp['n']}Ø{zp['phi']} c/{zp['sep']*100:.0f} cm (x e y)")],
        cols=[0.17, 0.38, 0.45])
    h.caja_panel("CUADRO DE PILARES", filas=[
        ("MARCA", "PERFIL", "PLACA BASE", "ALTURA"),
        (f"P-1 a P-{len(pos)}", r["pilar"]["seccion"], f"{r['placa']['a']}×{r['placa']['a']}×{r['placa']['t']}",
         f"{_m(r['H'])} m")], cols=[0.24, 0.26, 0.30, 0.20])
    _caja_geotecnia(h, cfg, r)
    Nmax = max(r["pilares_N"].values(), key=lambda v: v[0] + v[1])
    h.caja_panel("NOTAS DE CIMENTACIÓN", lineas=[
        f"1. σadm de proyecto {zp['sadm']:.0f} kPa ({_txt_fuente(cfg)}).",
        f"2. Cota de apoyo de zapatas −{_m(zp['prof'])} m (±0,00 = cara sup. solera existente). Hormigón de limpieza 10 cm.",
        f"3. Hormigón {cfg['materiales']['hormigon']}/B/20/{r['geotecnia']['durabilidad']['clase']}, acero {cfg['materiales']['armadura']}. "
        f"Recubrimiento {zp['rec']*1000:.0f} mm.",
        f"4. Pilares centrados en zapata. Axil máx. de servicio: G = {_m(Nmax[0])} kN, Q = {_m(Nmax[1])} kN.",
        "5. Ver detalle de zapata y placa de anclaje en plano E-05.",
    ])
    _leyenda(h, [("rect_disc", "Zapata aislada (bajo solera)"), ("pilar", "Pilar metálico")])
    return h


def _txt_fuente(cfg):
    g = cfg.get("geotecnia", {})
    f = g.get("fuente", "orientativo")
    if f == "estudio":
        return f"estudio geotécnico: {g.get('referencia', '')}"
    if f == "geologia":
        return "ESTIMADA SEGÚN GEOLOGÍA, sin estudio geotécnico: confirmar antes de ejecutar"
    return "adoptada sin estudio geotécnico: confirmar"


def _caja_geotecnia(h, cfg, r):
    g = cfg.get("geotecnia", {})
    zp = r["zapata"]
    geo = zp.get("geo", {})
    rc = r["geotecnia"]["reconocimiento"]
    lineas = [f"Fuente: {_txt_fuente(cfg)}."]
    if g.get("fuente") == "geologia":
        import geotecnia as G
        lit = G.GEOLOGIA[g["litologia"]]
        lineas.append(f"Litología: {lit['desc']} ({g.get('referencia', 'mapa geológico')}).")
        if g.get("espesor_relleno"):
            lineas.append(f"Relleno/tierra vegetal estimado {_m(g['espesor_relleno'])} m: apoyar en terreno natural.")
    elif g.get("fuente") == "estudio":
        for e in g.get("estratos", [])[:4]:
            lineas.append(f"{_m(e['desde'])}-{_m(e['hasta'])} m: {e.get('nombre', e['tipo'])}")
    lineas.append(f"Construcción {rc['tipo']} · terreno {rc['grupo']} · NF: "
                  f"{('-' + _m(g['nivel_freatico']) + ' m') if g.get('nivel_freatico') is not None else 'no detectado'}.")
    if geo.get("q_hund"):
        lineas.append(f"qh/γR = {geo['q_hund']:.0f} kPa · por asiento {geo['q_asiento']:.0f} kPa"
                      + (f" · D.25 {geo['q25']:.0f} kPa" if geo.get("q25") else "") + f" → σadm = {zp['sadm']:.0f} kPa.")
    else:
        lineas.append(f"σadm = {zp['sadm']:.0f} kPa.")
    for a in rc["avisos"][:2]:
        lineas.append("⚠ " + a)
    h.caja_panel("DATOS GEOTÉCNICOS (DB-SE-C)", lineas=lineas, sombrear=g.get("fuente") != "estudio", size=1.55)


def _leyenda(h, items):
    x0 = h.PX + h.PAD
    filas = len(items)
    hh = 5 + filas * 4.2
    y1 = h.panel_y
    y0 = y1 - hh
    if y0 < h.caj_top + 2:
        return
    h.r(x0, y0, h.W - h.M - h.PAD - x0, hh, lw=LW_F, ec="#888888", fc="#fafafa", z=1)
    h.t(x0 + 1.5, y1 - 3.2, "LEYENDA", 1.85, bold=True)
    y = y1 - 7
    for tipo, txt in items:
        if tipo == "rect_disc":
            h.r(x0 + 2, y - 1, 7, 2.6, lw=LW_G, ls="--", fc="#f0f0f0", z=3)
        elif tipo == "pilar":
            h.r(x0 + 4.5, y - 0.6, 1.8, 1.8, fc=NEGRO, z=3)
        elif tipo == "viga":
            h.r(x0 + 2, y - 0.2, 7, 1.0, lw=LW_M, fc=GRIS_M, z=3)
        elif tipo == "vigueta":
            h.l([x0 + 2, x0 + 9], [y + 0.3, y + 0.3], lw=LW_M, color="#8a5a1a")
        elif tipo == "eje":
            h.l([x0 + 2, x0 + 9], [y + 0.3, y + 0.3], lw=LW_F, ls=(0, (10, 2, 1.5, 2)))
        h.t(x0 + 12, y, txt, 1.65)
        y -= 4.2
    h.panel_y = y0 - 2


def hoja_planta(cfg, r, idx, total):
    h = Hoja(cfg, "E-03", "PLANTA DE ESTRUCTURA\n(FORJADO DE ENTREPLANTA)", "", idx, total, "Estructura · Planta de forjado")
    xs, ys, P, sc, e, ox, oy, W_, H_ = _plano_base(h, cfg, r, False)
    d = r["direccion"]
    bv = max(_b_viga(r) * sc, 1.2)
    s = cfg["forjado"]["separacion"]
    # vigas principales sobre las alineaciones perpendiculares a las viguetas
    if d == "x":
        lin_vp = [((x, 0), (x, ys[-1])) for x in xs]
        lin_zu = [((0, y), (xs[-1], y)) for y in ys]
        p_pos, p_tot = ys, ys[-1]
    else:
        lin_vp = [((0, y), (xs[-1], y)) for y in ys]
        lin_zu = [((x, 0), (x, ys[-1])) for x in xs]
        p_pos, p_tot = xs, xs[-1]
    # viguetas
    viguetas = []
    for a, b in zip(p_pos[:-1], p_pos[1:]):
        k = 1
        while a + k * s < b - 0.05:
            viguetas.append(a + k * s)
            k += 1
    for v in viguetas:
        if d == "x":
            h.l([P(0, v)[0], P(xs[-1], v)[0]], [P(0, v)[1]] * 2, lw=LW_M, color="#8a5a1a", z=3)
        else:
            h.l([P(v, 0)[0]] * 2, [P(v, 0)[1], P(v, ys[-1])[1]], lw=LW_M, color="#8a5a1a", z=3)
    for (a, b) in lin_vp:
        (x1, y1), (x2, y2) = P(*a), P(*b)
        if d == "x":
            h.r(x1 - bv / 2, y1, bv, y2 - y1, lw=LW_G, fc=GRIS_M, z=4)
        else:
            h.r(x1, y1 - bv / 2, x2 - x1, bv, lw=LW_G, fc=GRIS_M, z=4)
    for (a, b) in lin_zu:
        (x1, y1), (x2, y2) = P(*a), P(*b)
        if d == "x":
            h.r(x1, y1 - bv / 2, x2 - x1, bv, lw=LW_G, fc="white", z=4)
        else:
            h.r(x1 - bv / 2, y1, bv, y2 - y1, lw=LW_G, fc="white", z=4)
    _pilares(h, xs, ys, P, sc, r)
    # rótulos
    vp, zu = r["viga"]["seccion"], r["zuncho"]["seccion"]
    for n, (a, b) in enumerate(lin_vp, 1):
        (x1, y1), (x2, y2) = P(*a), P(*b)
        if d == "x":
            h.t(x1 - bv / 2 - 1.2, (y1 + y2) / 2, f"VP-{n} · {vp}", 1.75, bold=True, ha="center", va="bottom", rot=90)
        else:
            h.t((x1 + x2) / 2, y1 + bv / 2 + 1.0, f"VP-{n} · {vp}", 1.75, bold=True, ha="center", va="bottom")
    for n, (a, b) in enumerate(lin_zu, 1):
        (x1, y1), (x2, y2) = P(*a), P(*b)
        if d == "x":
            h.t((x1 + x2) / 2, y1 + (bv / 2 + 1.0 if n == len(lin_zu) else -bv / 2 - 1.0), f"ZU-{n} · {zu}", 1.75, bold=True,
                ha="center", va="bottom" if n == len(lin_zu) else "top")
        else:
            h.t(x1 + (bv / 2 + 1.0), (y1 + y2) / 2, f"ZU-{n} · {zu}", 1.75, bold=True, ha="center", va="bottom", rot=90)
    # indicador de viguetas (doble flecha)
    if viguetas:
        if d == "x":
            xm = P(xs[0] + (xs[1] - xs[0]) * 0.62, 0)[0]
            y1, y2 = P(0, viguetas[0])[1], P(0, viguetas[-1])[1]
            h.l([xm, xm], [y1, y2], lw=LW_F)
            for yy in (y1, y2):
                h.c(xm, yy, 0.45, lw=0, fc=NEGRO)
            h.etiqueta(xm, (y1 + y2) * 0.5 - (y2 - y1) * 0.2, ox + W_ + 8, (y1 + y2) / 2 - (y2 - y1) * 0.3,
                       [f"Viguetas {r['vigueta']['seccion'].replace('x','×')}", f"c/{s*100:.0f} cm, enrasadas",
                        "estribo con ETA en cada extremo"], ha="left")
        else:
            ym = P(0, ys[0] + (ys[1] - ys[0]) * 0.62)[1]
            x1, x2 = P(viguetas[0], 0)[0], P(viguetas[-1], 0)[0]
            h.l([x1, x2], [ym, ym], lw=LW_F)
            for xx in (x1, x2):
                h.c(xx, ym, 0.45, lw=0, fc=NEGRO)
            h.etiqueta((x1 + x2) / 2, ym, (x1 + x2) / 2 + 6, oy - 8,
                       [f"Viguetas {r['vigueta']['seccion'].replace('x','×')}", f"c/{s*100:.0f} cm, enrasadas"], ha="left")
    # tablero
    h.etiqueta(*P(xs[-1] * 0.80, ys[-1] * 0.82), P(xs[-1], 0)[0] + 4, P(0, ys[-1] * 0.82)[1] + 4,
               ["Tablero OSB/3 22 mm", "encolado y atornillado"], ha="left")
    # marcas de corte
    ym = (ys[0] + ys[1]) / 2 if len(ys) > 1 else 0
    xm = xs[0]
    h.marca_corte(ox - 24, P(0, ym)[1], ox + W_ + 24, P(0, ym)[1], "A")
    h.marca_corte(P(xm, 0)[0] + 0.0, oy - 24, P(xm, 0)[0], oy + H_ + 24, "B")
    h.titulo_vista(h.M + 8, h.M + 9, 1, "Planta de estructura del forjado", _txt_escala(e, h.k))
    h.escala_txt = _txt_escala(e, h.k)
    cv = _cotas_verticales(r, cfg)
    filas = [("MARCA", "SECCIÓN", "LUZ (m)", "Rd (kN)")]
    filas.append(("VP", vp, _m(max(r["Lb"])), _m(r["union"]["Rd"])))
    filas.append(("ZU", zu, _m(max(r["Lj"])), "-"))
    filas.append(("VG", r["vigueta"]["seccion"].replace("x", "×"), _m(max(r["Lj"])), _m(r["R_vigueta"])))
    h.caja_panel("CUADRO DE VIGAS", filas=filas, cols=[0.15, 0.40, 0.22, 0.23])
    h.caja_panel("NOTAS DE FORJADO", lineas=[
        f"1. Forjado enrasado: cara superior de vigas y viguetas a cota +{_m(cv['v_sup'])} m; suelo terminado aprox. "
        f"+{_m(cv['suelo'] + 0.01)} m.",
        f"2. Uniones viga-pilar articuladas sobre chapa de cabeza (ver E-05), {r['union']['n_tornillos']} tornillos "
        f"M16 {r['union']['clase']}.",
        f"3. Viguetas con estribos metálicos con ETA, capacidad ≥ {_m(r['R_vigueta'])} kN, sobre durmiente de madera "
        f"atornillado al alma de la viga (M12 c/50 cm).",
        "4. Barandilla en bordes libres: altura ≥ 0,90 m (DB-SUA 1), sin elementos escalables, huecos < 10 cm.",
        "5. Hueco de escalera: brochales y embrochalados dobles, a confirmar con la DF.",
    ])
    _leyenda(h, [("viga", "Viga principal VP"), ("vigueta", "Vigueta de madera"), ("pilar", "Pilar"),
                 ("eje", "Eje de replanteo")])
    return h


def hoja_secciones(cfg, r, idx, total):
    h = Hoja(cfg, "E-04", "SECCIONES CONSTRUCTIVAS\nA-A Y B-B", "", idx, total, "Estructura · Secciones")
    xs, ys = _ejes(cfg)
    cv = _cotas_verticales(r, cfg)
    d = r["direccion"]
    aw = h.PX - h.M - 45
    ah = (h.H - 2 * h.M - 30) / 2 - 10
    alto = cv["suelo"] - cv["zap_inf"] + 1.2
    ancho = max(xs[-1], ys[-1]) + 1.2
    e = _escala(ancho, alto, aw, ah, margen=20)
    sc = 1.0 / e
    zp = r["zapata"]
    for k, (letra, eje_long, perp) in enumerate([("A", xs, ys), ("B", ys, xs)]):
        y0 = h.H - h.M - 18 - (k + 1) * (ah + 10) + 26
        ox = h.M + 30
        Pz = lambda u, z: (ox + u * 1000 * sc, y0 + (z - cv["zap_inf"]) * 1000 * sc)
        L = eje_long[-1]
        # terreno y solera
        h.l([Pz(-0.6, 0)[0], Pz(L + 0.6, 0)[0]], [Pz(0, 0)[1]] * 2, lw=LW_G)
        h.r(Pz(-0.6, -0.15)[0], Pz(0, -0.15)[1], (L + 1.2) * 1000 * sc, 0.15 * 1000 * sc, lw=LW_F, fc="#f2f2f2",
            hatch="....", z=1)
        corte_es_dir_viguetas = (letra == "A") == (d == "x")
        for u in eje_long:
            # zapata
            Bz = zp["B"]
            h.r(Pz(u - Bz / 2, 0)[0], Pz(0, cv["zap_inf"])[1], Bz * 1000 * sc, zp["h"] * 1000 * sc, lw=LW_G,
                fc="#dcdcdc", hatch="//", z=2)
            h.r(Pz(u - Bz / 2, 0)[0], Pz(0, cv["zap_inf"] - 0.10)[1], Bz * 1000 * sc, 0.10 * 1000 * sc, lw=LW_F,
                fc="#efefef", z=2)
            # pilar
            bp = r["pilar"]["perfil"]["b"] / 1000
            x1, z1 = Pz(u - bp / 2, cv["pil_inf"])
            h.r(x1, z1, bp * 1000 * sc, (cv["pil_sup"] - cv["pil_inf"]) * 1000 * sc, lw=LW_G, fc="white", z=3)
            h.l([x1 + bp * 500 * sc] * 2, [z1, Pz(0, cv["pil_sup"])[1]], lw=LW_F, ls=(0, (6, 2, 1, 2)))
            pa = r["placa"]["a"] / 1000
            h.r(Pz(u - pa / 2, 0)[0], Pz(0, cv["pil_inf"] - r["placa"]["t"] / 1000)[1], pa * 1000 * sc,
                max(r["placa"]["t"] * sc, 0.4), lw=LW_M, fc=NEGRO, z=4)
            h.r(Pz(u - pa / 2 - 0.03, 0)[0], Pz(0, cv["pil_sup"])[1], (pa + 0.06) * 1000 * sc,
                max(cv["tcap"] * 1000 * sc, 0.4), lw=LW_M, fc=NEGRO, z=4)
        if corte_es_dir_viguetas:
            # viguetas en alzado y vigas cortadas en los ejes
            hj = _hj(r) / 1000
            h.r(Pz(0, 0)[0], Pz(0, cv["v_sup"] - hj)[1], L * 1000 * sc, hj * 1000 * sc, lw=LW_M, fc="#f3e3c3", z=3)
            for u in eje_long:
                dibujar_seccion_viga(h, Pz(u, 0)[0], Pz(0, cv["v_inf"])[1], r, sc)
            txt_el = f"Vigueta {r['vigueta']['seccion'].replace('x','×')} c/{cfg['forjado']['separacion']*100:.0f} cm"
            txt_cut = f"VP {r['viga']['seccion']} (sección)"
        else:
            hv = _h_viga(r) / 1000
            h.r(Pz(0, 0)[0], Pz(0, cv["v_inf"])[1], L * 1000 * sc, hv * 1000 * sc, lw=LW_G, fc="white", z=3)
            if "perfil" in r["viga"]:
                tf = r["viga"]["perfil"]["tf"] / 1000
                for zz in (cv["v_inf"] + tf, cv["v_sup"] - tf):
                    h.l([Pz(0, 0)[0], Pz(L, 0)[0]], [Pz(0, zz)[1]] * 2, lw=LW_F)
            s = cfg["forjado"]["separacion"]
            bj, hj = _bj(r) / 1000, _hj(r) / 1000
            for a, b in zip(eje_long[:-1], eje_long[1:]):
                kk = 1
                while a + kk * s < b - 0.05:
                    u = a + kk * s
                    h.r(Pz(u - bj / 2, 0)[0], Pz(0, cv["v_sup"] - hj)[1], max(bj * 1000 * sc, 0.6), hj * 1000 * sc,
                        lw=LW_F, fc="#c9a46a", z=5)
                    kk += 1
            txt_el = f"VP {r['viga']['seccion']} (alzado)"
            txt_cut = "Viguetas (sección)"
        # tablero
        h.r(Pz(-0.02, 0)[0], Pz(0, cv["v_sup"])[1], (L + 0.04) * 1000 * sc, max(0.022 * 1000 * sc, 0.5), lw=LW_F,
            fc="#d8b98a", z=5)
        # barandilla en bordes
        hb = N.altura_barandilla(cv["suelo"])
        for u in (0, L):
            h.l([Pz(u, 0)[0]] * 2, [Pz(0, cv["suelo"])[1], Pz(0, cv["suelo"] + hb)[1]], lw=LW_M, color="#666666")
        h.l([Pz(0, 0)[0], Pz(L, 0)[0]], [Pz(0, cv["suelo"] + hb)[1]] * 2, lw=LW_M, color="#666666", ls="--")
        # niveles
        xl = Pz(L + 0.6, 0)[0] + 3
        for z, txt in ((cv["suelo"] + hb, f"+{_m(cv['suelo'] + hb)} barandilla (≥ {_m(hb)} m)"),
                       (cv["v_sup"], f"+{_m(cv['v_sup'])} cara sup. forjado"),
                       (cv["v_inf"], f"+{_m(cv['v_inf'])} cara inf. vigas"),
                       (0.0, "±0,00 solera existente"),
                       (cv["zap_sup"], f"{_m(cv['zap_sup'])} cara sup. zapata"),
                       (cv["zap_inf"], f"{_m(cv['zap_inf'])} cota de apoyo")):
            h.nivel(xl, Pz(0, z)[1], txt)
        # cotas
        for i in range(len(eje_long) - 1):
            h.cota(*Pz(eje_long[i], cv["suelo"] + hb), *Pz(eje_long[i + 1], cv["suelo"] + hb), 5,
                   _m(eje_long[i + 1] - eje_long[i]))
        h.cota(*Pz(-0.6, 0), *Pz(-0.6, cv["v_inf"]), 4, f"{_m(cv['v_inf'])} libre")
        h.etiqueta(*Pz(L * 0.35, cv["v_sup"] - 0.05), Pz(L * 0.35, 0)[0] + 10, Pz(0, cv["suelo"] + hb * 0.55)[1], txt_el)
        h.etiqueta(*Pz(eje_long[-1] if corte_es_dir_viguetas else L * 0.5, cv["v_inf"] + 0.05),
                   Pz(L * 0.7, 0)[0] + 6, Pz(0, cv["v_inf"] - 0.45)[1], txt_cut)
        h.etiqueta(*Pz(eje_long[0], cv["pil_inf"] + r["H"] * 0.5), Pz(eje_long[0], 0)[0] + 8,
                   Pz(0, cv["pil_inf"] + r["H"] * 0.42)[1], [f"Pilar {r['pilar']['seccion']}", cfg["materiales"]["pilares"]])
        h.etiqueta(*Pz(eje_long[0] + zp["B"] * 0.25, cv["zap_inf"] + zp["h"] * 0.5), Pz(eje_long[0], 0)[0] + 14,
                   Pz(0, cv["zap_inf"] + zp["h"] * 0.2)[1], f"Zapata Z-1 {_m(zp['B'])}×{_m(zp['B'])}×{_m(zp['h'])}")
        letras = _letras(len(xs)) if letra == "A" else [str(i + 1) for i in range(len(ys))]
        for u, lt in zip(eje_long, letras):
            px = Pz(u, 0)[0]
            h.l([px, px], [Pz(0, cv["zap_inf"] - 0.2)[1], Pz(0, cv["suelo"] + hb + 0.35)[1]], lw=LW_F,
                ls=(0, (10, 2, 1.5, 2)), color="#777777", z=1)
            h.burbuja(px, Pz(0, cv["suelo"] + hb + 0.35)[1] + 2.8, lt, rad=2.4)
        h.titulo_vista(h.M + 8, y0 - 8, k + 1, f"Sección {letra}-{letra}", _txt_escala(e, h.k))
    h.escala_txt = _txt_escala(e, h.k)
    h.caja_panel("NOTAS DE SECCIONES", lineas=[
        "1. Cotas en metros referidas a la cara superior de la solera existente (±0,00).",
        "2. Longitud de pilar indicada nominal: verificar niveles en obra antes de cortar.",
        "3. Barandilla en bordes libres según proyecto de arquitectura; donde el forjado acometa a muro existente, "
        "anclar según detalle E-05.",
        "4. No se representan acabados, instalaciones ni tabiquería (ver arquitectura).",
        f"5. Altura libre bajo vigas {_m(cv['v_inf'])} m.",
    ])
    return h


def hoja_detalles(cfg, r, idx, total):
    h = Hoja(cfg, "E-05", "DETALLES DE CIMENTACIÓN\nY UNIONES", "VARIAS", idx, total, "Estructura · Detalles")
    zp, pl, pil = r["zapata"], r["placa"], r["pilar"]["perfil"]
    x0, x1 = h.M, h.PX
    ytop, ybot = h.H - h.M, h.M
    xm, ymid = (x0 + x1) / 2, (ytop + ybot) / 2
    h.l([xm, xm], [ybot, ytop], lw=LW_F, color="#999999")
    h.l([x0, x1], [ymid, ymid], lw=LW_F, color="#999999")
    cw, ch = xm - x0, ytop - ymid
    cv = _cotas_verticales(r, cfg)

    def esc(ancho_mm, alto_mm):
        for e in (5, 10, 15, 20, 25, 50):
            if ancho_mm / e <= cw - 40 and alto_mm / e <= ch - 30:
                return e
        return 50

    # ---------------- 1. zapata + placa (sección)
    Bmm, hmm = zp["B"] * 1000, zp["h"] * 1000
    e1 = esc(Bmm + 400, hmm + 900)
    s1 = 1 / e1
    cx, yb = x0 + cw / 2 - 8, ymid + 22
    h.r(cx - (Bmm / 2 + 50) * s1, yb - 100 * s1, (Bmm + 100) * s1, 100 * s1, lw=LW_F, fc="#efefef", z=1)
    h.r(cx - Bmm / 2 * s1, yb, Bmm * s1, hmm * s1, lw=LW_G, fc="#e4e4e4", z=2)
    rec = zp["rec"] * 1000
    yb_bar = yb + (rec + zp["phi"] / 2) * s1
    h.l([cx - (Bmm / 2 - rec) * s1, cx + (Bmm / 2 - rec) * s1], [yb_bar + zp["phi"] * s1] * 2, lw=LW_G)
    for kk in range(zp["n"]):
        xx = cx - (Bmm / 2 - rec) * s1 + kk * (Bmm - 2 * rec) * s1 / (zp["n"] - 1)
        h.c(xx, yb_bar, max(zp["phi"] / 2 * s1, 0.45), lw=0, fc=NEGRO)
    # patillas
    for sgn in (-1, 1):
        xe = cx + sgn * (Bmm / 2 - rec) * s1
        h.l([xe, xe], [yb_bar + zp["phi"] * s1, yb + (hmm - rec) * s1 * 0.8], lw=LW_G)
    ysol = yb + (zp["prof"] - 0) * 1000 * s1  # ±0,00
    ytz = yb + hmm * s1
    # solera
    h.r(cx - (Bmm / 2 + 200) * s1, ysol - 150 * s1, (Bmm + 400) * s1, 150 * s1, lw=LW_F, fc="#f2f2f2", hatch="....", z=1)
    # pedestal/relleno hasta solera: el pilar arranca en la zapata
    b = pil["b"] * s1
    pa, tp = pl["a"] * s1, pl["t"] * s1
    ymort = ytz + 30 * s1
    h.r(cx - pa / 2, ytz, pa, 30 * s1, lw=LW_F, fc="#cfcfcf", hatch="xx", z=3)
    h.r(cx - pa / 2, ymort, pa, max(tp, 0.5), lw=LW_M, fc=NEGRO, z=4)
    ytop_p = min(ytop - 22, ysol + 45)
    h.r(cx - b / 2, ymort + tp, b, ytop_p - (ymort + tp), lw=LW_G, fc="white", z=3)
    h.l([cx - b / 2 - 2, cx + b / 2 + 2], [ytop_p + 1.5, ytop_p - 1.5], lw=LW_F)
    t = r["pilar"]["perfil"]["t"] * s1 if "t" in r["pilar"]["perfil"] else 1
    h.l([cx - b / 2 + t] * 2, [ymort + tp, ytop_p], lw=LW_F)
    h.l([cx + b / 2 - t] * 2, [ymort + tp, ytop_p], lw=LW_F)
    for sgn in (-1, 1):
        xp = cx + sgn * (pl["a"] / 2 - 40) * s1
        h.l([xp, xp], [ymort + tp + 25 * s1, ytz - 125 * s1], lw=LW_G)
        h.r(xp - 1.0, ymort + tp, 2.0, 0.7, lw=LW_F, fc=NEGRO, z=5)
    h.cota(cx - Bmm / 2 * s1, yb, cx + Bmm / 2 * s1, yb, -6, _m(zp["B"]))
    h.cota(cx + Bmm / 2 * s1, yb, cx + Bmm / 2 * s1, ytz, -4, _m(zp["h"]))
    h.cota(cx + (Bmm / 2 + 200) * s1, yb, cx + (Bmm / 2 + 200) * s1, ysol, -3, _m(zp["prof"]))
    h.etiqueta(cx, ytop_p - 8, cx + 14, ytop_p - 4, [f"Pilar {r['pilar']['seccion']}", cfg["materiales"]["pilares"]])
    h.etiqueta(cx - b / 2, ymort + tp + 1.5, cx - Bmm / 2 * s1 - 6, ysol + 10,
               [f"Placa {pl['a']}×{pl['a']}×{pl['t']}", f"soldadura a = {pl['aw']} mm"], ha="right")
    h.etiqueta(cx + (pl['a'] / 2 - 40) * s1, ytz - 60 * s1, cx + Bmm / 2 * s1 + 10, ytz - 6,
               ["4 M16 8.8 anclaje químico", "L,emb ≥ 125 mm (ETA)"])
    h.etiqueta(cx - pa / 2 + 1, ytz + 15 * s1, cx - Bmm / 2 * s1 - 6, ytz - 4,
               ["Mortero sin retracción", "e = 30 mm"], ha="right")
    h.etiqueta(cx - Bmm / 4 * s1, yb_bar, cx - Bmm / 2 * s1 - 4, yb + 4,
               [f"{zp['n']}Ø{zp['phi']} c/{zp['sep']*100:.0f} cm", "en ambas direcciones", f"rec. {rec:.0f} mm"],
               ha="right")
    h.etiqueta(cx + Bmm / 3 * s1, yb - 50 * s1, cx + Bmm / 2 * s1 + 6, yb - 6, "Hormigón de limpieza 10 cm")
    h.etiqueta(cx - (Bmm / 2 + 120) * s1, ysol - 70 * s1, cx - Bmm / 2 * s1 - 6, ysol + 22,
               ["Solera existente", "(demoler y reponer)"], ha="right")
    h.titulo_vista(x0 + 5, ymid + 6, 1, "Zapata Z-1 y placa de anclaje", f"1:{e1/h.k:g}")

    # ---------------- 2. placa base en planta
    e2 = esc(pl["a"] + 200, pl["a"] + 200)
    s2 = 1 / e2
    cx2, cy2 = xm + cw / 2 - 6, ymid + ch / 2 + 4
    a2 = pl["a"] * s2
    h.r(cx2 - a2 / 2, cy2 - a2 / 2, a2, a2, lw=LW_G, fc="#d9d9d9", z=2)
    b2 = pil["b"] * s2
    h.r(cx2 - b2 / 2, cy2 - b2 / 2, b2, b2, lw=LW_G, fc="white", z=3)
    t2 = pil.get("t", 4) * s2
    h.r(cx2 - b2 / 2 + t2, cy2 - b2 / 2 + t2, b2 - 2 * t2, b2 - 2 * t2, lw=LW_F, fc="#f7f7f7", z=4)
    for sx in (-1, 1):
        for sy in (-1, 1):
            px, py = cx2 + sx * (pl["a"] / 2 - 40) * s2, cy2 + sy * (pl["a"] / 2 - 40) * s2
            h.c(px, py, 9 * s2, lw=LW_M, fc="white")
            h.l([px - 2, px + 2], [py, py], lw=LW_F)
            h.l([px, px], [py - 2, py + 2], lw=LW_F)
    h.cota(cx2 - a2 / 2, cy2 - a2 / 2, cx2 + a2 / 2, cy2 - a2 / 2, -6, f"{pl['a']}")
    h.cota(cx2 + a2 / 2, cy2 - a2 / 2, cx2 + a2 / 2, cy2 + a2 / 2, -6, f"{pl['a']}")
    h.cota(cx2 - (pl["a"] / 2 - 40) * s2, cy2 + a2 / 2, cx2 + (pl["a"] / 2 - 40) * s2, cy2 + a2 / 2, 5,
           f"{pl['a'] - 80}")
    h.etiqueta(cx2 + (pl["a"] / 2 - 40) * s2, cy2 + (pl["a"] / 2 - 40) * s2, cx2 + a2 / 2 + 8, cy2 + a2 / 2 + 8,
               ["Taladro Ø18 para M16", "arandela y doble tuerca"])
    h.etiqueta(cx2 - b2 / 2, cy2 - b2 / 4, cx2 - a2 / 2 - 8, cy2 - a2 / 2 - 6,
               [f"Soldadura en ángulo a = {pl['aw']} mm", "perimetral, en taller"], ha="right")
    h.t(cx2 - a2 / 2, cy2 + a2 / 2 + 12, "Cotas en mm", 1.6, italic=True)
    h.titulo_vista(xm + 5, ymid + 6, 2, "Placa de anclaje (planta)", f"1:{e2/h.k:g}")

    # ---------------- 3. unión viga-pilar (alzado)
    hv = _h_viga(r)
    e3 = esc(900, hv + 600)
    s3 = 1 / e3
    cx3, yb3 = x0 + cw / 2, ybot + 30
    b3 = pil["b"] * s3
    ycap = yb3 + 300 * s3
    h.r(cx3 - b3 / 2, yb3, b3, 300 * s3, lw=LW_G, fc="white", z=3)
    capw = (pil["b"] + 60) * s3
    h.r(cx3 - capw / 2, ycap, capw, 10 * s3, lw=LW_M, fc=NEGRO, z=4)
    Lv = 420 * s3
    gap = 10 * s3
    for sgn in (-1, 1):
        xa = cx3 + sgn * gap / 2
        xb = cx3 + sgn * (gap / 2 + Lv)
        h.r(min(xa, xb), ycap + 10 * s3, abs(xb - xa), hv * s3, lw=LW_G, fc="white", z=3)
        if "perfil" in r["viga"]:
            tf = r["viga"]["perfil"]["tf"] * s3
            for zz in (ycap + 10 * s3 + tf, ycap + 10 * s3 + hv * s3 - tf):
                h.l([xa, xb], [zz, zz], lw=LW_F)
            # rigidizador sobre apoyo
            xr = cx3 + sgn * (gap / 2 + pil["b"] / 2 * s3 * 0.6)
            h.l([xr, xr], [ycap + 10 * s3 + tf, ycap + 10 * s3 + hv * s3 - tf], lw=LW_M)
        xt = cx3 + sgn * (gap / 2 + 0.25 * (pil["b"] + 60) * s3)
        h.l([xt, xt], [ycap - 2, ycap + 10 * s3 + 3], lw=LW_G)
        h.l([xt - 1.2, xt + 1.2], [ycap - 2] * 2, lw=LW_G)
    h.cota(cx3 - capw / 2, ycap, cx3 + capw / 2, ycap, -12, f"{pil['b'] + 60}")
    h.cota(cx3 + gap / 2 + Lv, ycap + 10 * s3, cx3 + gap / 2 + Lv, ycap + (10 + hv) * s3, -4, f"{hv:.0f}")
    h.etiqueta(cx3 + capw / 2 - 0.5, ycap + 5 * s3, cx3 + capw / 2 + 14, ycap - 8,
               [f"Chapa de cabeza {pil['b'] + 60}×{pil['b'] + 60}×10", "soldada al pilar a = 4 mm"])
    h.etiqueta(cx3 - gap / 2 - 0.25 * (pil["b"] + 60) * s3, ycap + 3, cx3 - Lv - 4, ycap - 10,
               [f"{r['union']['n_tornillos']} tornillos M16 {r['union']['clase']}", "por viga, ala inferior"], ha="right")
    h.etiqueta(cx3 - Lv * 0.6, ycap + (10 + hv * 0.75) * s3, cx3 - Lv - 4, ycap + (10 + hv) * s3 + 8,
               [f"VP {r['viga']['seccion']}"], ha="right")
    h.etiqueta(cx3 + gap / 2 + pil["b"] / 2 * s3 * 0.6, ycap + (10 + hv / 2) * s3, cx3 + Lv + 4,
               ycap + (10 + hv) * s3 + 8, ["Rigidizador e = 8 mm", "a ambos lados del alma"])
    h.etiqueta(cx3, yb3 + 100 * s3, cx3 + 16, yb3 + 4, [f"Pilar {r['pilar']['seccion']}"])
    h.t(x0 + 6, ymid - 6, f"Reacción de cálculo por viga Rd = {_m(r['union']['Rd'])} kN", 1.65, italic=True)
    h.titulo_vista(x0 + 5, ybot + 6, 3, "Unión viga - pilar (alzado)", f"1:{e3/h.k:g}")

    # ---------------- 4. vigueta - viga (sección)
    hj, bj = _hj(r), _bj(r)
    e4 = esc(1000, hv + 300)
    s4 = 1 / e4
    cx4, yb4 = xm + cw / 2 - 10, ybot + 40
    if "perfil" in r["viga"]:
        p = r["viga"]["perfil"]
        dibujar_I(h, cx4, yb4, p, s4)
        tf, tw, B4 = p["tf"], p["tw"], p["b"]
        # durmientes
        dw = (B4 - tw) / 2
        for sgn in (-1, 1):
            xd = cx4 + sgn * tw / 2 * s4 if sgn > 0 else cx4 - (tw / 2 + dw) * s4
            h.r(xd, yb4 + tf * s4, dw * s4, (hv - 2 * tf) * s4, lw=LW_M, fc="#f3e3c3", z=5)
            h.l([xd, xd + dw * s4], [yb4 + tf * s4, yb4 + (hv - tf) * s4], lw=LW_F, z=6)
        # tornillo pasante del durmiente
        h.l([cx4 - B4 / 2 * s4, cx4 + B4 / 2 * s4], [yb4 + hv / 2 * s4] * 2, lw=LW_G, z=7)
        # viguetas a ambos lados enrasadas arriba
        for sgn in (-1, 1):
            xa = cx4 + sgn * (B4 / 2 + 3) * s4
            xb = cx4 + sgn * (B4 / 2 + 3 + 380) * s4
            ytop4 = yb4 + hv * s4
            h.r(min(xa, xb), ytop4 - hj * s4, abs(xb - xa), hj * s4, lw=LW_M, fc="#f3e3c3", z=4)
            # estribo
            xs_ = xa
            h.l([cx4 + sgn * B4 / 2 * s4, cx4 + sgn * B4 / 2 * s4], [ytop4 - hj * s4 * 0.9, ytop4 - 5 * s4], lw=LW_G, z=8)
            h.l([cx4 + sgn * B4 / 2 * s4, xs_ + sgn * 60 * s4], [ytop4 - hj * s4 - 1.5 * s4] * 2, lw=LW_G, z=8)
        h.r(cx4 - (B4 / 2 + 400) * s4, yb4 + hv * s4, (B4 + 800) * s4, 22 * s4, lw=LW_M, fc="#d8b98a", z=6)
        h.etiqueta(cx4 + (B4 / 2 + 200) * s4, yb4 + hv * s4 + 11 * s4, cx4 + (B4 / 2 + 250) * s4, yb4 + hv * s4 + 14,
                   ["Tablero OSB/3 22 mm", "encolado y atornillado"])
        h.etiqueta(cx4 - (B4 / 2 + 200) * s4, yb4 + (hv - hj / 2) * s4, cx4 - (B4 / 2 + 250) * s4, yb4 + hv * s4 + 12,
                   [f"Vigueta {r['vigueta']['seccion'].replace('x','×')}", "enrasada con la viga"], ha="right")
        h.etiqueta(cx4 + B4 / 2 * s4, yb4 + (hv - hj * 0.5) * s4, cx4 + (B4 / 2 + 300) * s4, yb4 - 6,
                   ["Estribo metálico con ETA", f"cap. ≥ {_m(r['R_vigueta'])} kN, clavos anillados"])
        h.etiqueta(cx4 - (tw / 2 + dw / 2) * s4, yb4 + tf * s4 + 3, cx4 - (B4 / 2 + 200) * s4, yb4 - 6,
                   ["Durmiente de madera entre alas", "M12 pasante c/50 cm"], ha="right")
        h.etiqueta(cx4, yb4 + 2 * s4, cx4 + 4, yb4 - 14, [f"VP {r['viga']['seccion']}"])
    else:
        dibujar_seccion_viga(h, cx4, yb4, r, s4)
        h.t(cx4, yb4 - 8, "Unión con estribos metálicos con ETA", 1.7, ha="center")
    h.titulo_vista(xm + 5, ybot + 6, 4, "Unión vigueta - viga (sección)", f"1:{e4/h.k:g}")
    h.escala_txt = "VARIAS"
    est = cfg["estabilidad"]
    lineas = [
        "1. Cotas en mm salvo indicación.",
        f"2. Acero {cfg['materiales']['vigas']}JR en perfiles y chapas. Soldaduras en taller, garganta mín. 4 mm.",
        "3. Tornillos con arandela bajo cabeza y tuerca. Apriete a tope (no pretensados).",
        "4. Anclajes químicos con ETA, dimensionados por el fabricante para Vd indicado.",
    ]
    if est["tipo"] == "muro" and "anclajes_muro" in r:
        a = r["anclajes_muro"]
        lineas.append(f"5. Anclaje del forjado al muro: {a['n']} anclajes M12 químicos c/{a['sep']*100:.0f} cm a la viga/zuncho "
                      f"adosado (Vd = {_m(a['Vd'])} kN por anclaje). Verificar el muro.")
    h.caja_panel("NOTAS DE DETALLES", lineas=lineas)
    h.caja_panel("CARACTERÍSTICAS DE UNIONES", filas=[
        ("UNIÓN", "Rd (kN)", "SOLUCIÓN"),
        ("VP - pilar", _m(r["union"]["Rd"]), f"{r['union']['n_tornillos']}M16 {r['union']['clase']}"),
        ("VG - VP", _m(r["R_vigueta"]), "Estribo ETA"),
        ("Pilar - zapata", _m(r["pilar"]["Nd"]), f"Placa e={pl['t']}"),
    ], cols=[0.34, 0.24, 0.42])
    return h


def hoja_calculos(cfg, r, M, idx, total):
    h = Hoja(cfg, "E-06", "RESUMEN DE CÁLCULO\nCOMPROBACIONES ELU / ELS", "S/E", idx, total, "Estructura · Cálculos")
    x0 = h.M + 6
    y = h.H - h.M - 8
    h.t(x0, y, "RESUMEN DE COMPROBACIONES · MÉTODO DE LOS ESTADOS LÍMITE (CTE DB-SE)", 2.8, bold=True)
    y -= 4.0
    h.t(x0, y, "Memoria de cálculo completa con el desarrollo de cada comprobación en documento anexo "
               "(memoria_calculo.md).", 1.7, italic=True)
    y -= 5
    cols = [("ELEMENTO", 30), ("COMPROBACIÓN", 92), ("DEMANDA", 26), ("CAPACIDAD", 26), ("APROV.", 15),
            ("ESTADO", 18), ("REFERENCIA", 75)]
    xs_ = [x0]
    for _, w in cols[:-1]:
        xs_.append(xs_[-1] + w)
    wt = sum(w for _, w in cols)
    rows = r["checks"]
    rh = min(4.0, (y - h.M - 12) / (len(rows) + 1))
    size = min(1.75, rh * 0.45)
    h.r(x0 - 1, y - rh + 1, wt, rh, lw=0, fc=GRIS, ec="none", z=1)
    for (nm, _), xx in zip(cols, xs_):
        h.t(xx, y - rh + 2.0, nm, size, bold=True)
    y -= rh
    prev = None
    for c in rows:
        fill = "#fde2e2" if not c["cumple"] else ("#ffffff" if c["ratio"] < 0.9 else "#fff4d6")
        h.r(x0 - 1, y - rh + 1, wt, rh, lw=0, fc=fill, ec="none", z=1)
        h.l([x0 - 1, x0 - 1 + wt], [y + 1, y + 1], lw=0.1, color="#aaaaaa")
        vals = [c["elemento"] if c["elemento"] != prev else "", c["comprobacion"],
                f"{c['demanda']:.3g} {c['unidad']}", f"{c['capacidad']:.3g} {c['unidad']}",
                f"{c['ratio']:.2f}", "CUMPLE" if c["cumple"] else "NO CUMPLE", c["ref"]]
        for v, xx, (nm, w) in zip(vals, xs_, cols):
            if _w(v, size) > w - 1:
                v = v[: int((w - 1) / (size * 0.6)) - 1] + "…"
            h.t(xx, y - rh + 2.0, v, size, bold=(nm in ("ELEMENTO", "ESTADO")))
        prev = c["elemento"]
        y -= rh
    h.l([x0 - 1, x0 - 1 + wt], [y + 1, y + 1], lw=LW_M)
    # gráfico de aprovechamientos en el panel
    C = r["cargas"]
    h.caja_panel("HIPÓTESIS DE CARGA", filas=[
        ("ACCIÓN", "VALOR", "REF."),
        ("Permanentes (sin p.p.)", f"{_m(C['g'])} kN/m²", "SE-AE C"),
        (f"Uso {cfg['uso']}", f"{_m(C['q'])} kN/m²", "SE-AE 3.1"),
        ("Concentrada", f"{_m(C['Q'])} kN", "SE-AE 3.1"),
        ("Barandilla", f"{_m(C['hb'])} kN/m", "SE-AE 3.3"),
        ("Horizontal global Hd", f"{_m(r['Hd'])} kN", "SE-A 5.4"),
    ], cols=[0.46, 0.30, 0.24])
    # máximo aprovechamiento por elemento
    elems = []
    for c in rows:
        if c["elemento"] not in [e[0] for e in elems]:
            elems.append([c["elemento"], c["ratio"]])
        else:
            for e in elems:
                if e[0] == c["elemento"]:
                    e[1] = max(e[1], c["ratio"])
    x0p, x1p = h.PX + h.PAD, h.W - h.M - h.PAD
    hh = 6 + len(elems) * 3.6
    y1 = h.panel_y
    y0 = y1 - hh
    if y0 > h.caj_top + 2:
        h.r(x0p, y0, x1p - x0p, hh, lw=LW_F, ec="#888888", fc="#fafafa", z=1)
        h.t(x0p + 1.5, y1 - 3.2, "APROVECHAMIENTO MÁXIMO POR ELEMENTO", 1.85, bold=True)
        bx0, bw = x0p + 28, x1p - x0p - 40
        yy = y1 - 7
        for nm, rt in elems:
            h.t(x0p + 1.5, yy, nm, 1.6)
            h.r(bx0, yy - 0.4, bw, 2.2, lw=LW_F, fc="white", ec="#999999", z=2)
            h.r(bx0, yy - 0.4, bw * min(rt, 1.0), 2.2, lw=0, fc="#555555" if rt <= 1 else "#c62828", ec="none", z=3)
            h.t(bx0 + bw + 1.2, yy, f"{rt:.2f}", 1.6, bold=True)
            yy -= 3.6
        h.l([bx0 + bw] * 2, [y0 + 1, y1 - 4.5], lw=LW_F, ls="--", color="#c62828")
        h.panel_y = y0 - 2
    if r.get("optimizacion"):
        filas = [("#", "DIR/SEP", "VIGUETA", "VIGA", "COSTE €")]
        for i, t in enumerate(r["optimizacion"][:5], 1):
            filas.append((str(i), f"{t['direccion'].upper()} {t['separacion']:.2f}", t["vigueta"], t["viga"],
                          f"{t['coste']:.0f}"))
        h.caja_panel(f"OPTIMIZACIÓN ({r['optimizacion_n']} soluciones válidas)", filas=filas,
                     cols=[0.08, 0.20, 0.30, 0.22, 0.20], size=1.5, alto_fila=2.7)
    med = r.get("mediciones")
    if med:
        h.caja_panel("MEDICIONES Y COSTE ESTIMADO", lineas=[
            f"Acero {med['acero_kg']:.0f} kg · madera {med.get('madera_m3', 0):.2f} m³ · hormigón {med['hormigon_m3']:.2f} m³ "
            f"· armadura {med['armado_kg']:.0f} kg · excavación {med['excavacion_m3']:.2f} m³.",
            f"Coste estructura (PEM orientativo): {r['coste']:.0f} €"
            + (f" · ahorro {r['optimizacion_ahorro']:.0f} € frente a la peor solución válida." if r.get("optimizacion") else "."),
        ])
    h.caja_panel("CONCLUSIÓN", lineas=[
        ("Todas las comprobaciones de resistencia (ELU) y aptitud al servicio (ELS) CUMPLEN con la normativa indicada."
         if r["ok"] else "ATENCIÓN: existen comprobaciones que NO CUMPLEN. Revisar secciones antes de emitir."),
        "Cálculo preliminar asistido por IA: debe revisarlo y firmarlo técnico competente.",
    ], sombrear=not r["ok"])
    return h


# ============================================================================ conjunto
def generar_pdf(cfg, r, M, ruta_pdf, carpeta_png=None):
    indice = [("E-01", "Cuadro de características y notas"), ("E-02", "Planta de cimentación"),
              ("E-03", "Planta de estructura"), ("E-04", "Secciones A-A y B-B"),
              ("E-05", "Detalles de cimentación y uniones"), ("E-06", "Resumen de cálculo")]
    total = len(indice)
    hojas = [
        lambda i: hoja_notas(cfg, r, M, i, total, indice),
        lambda i: hoja_cimentacion(cfg, r, i, total),
        lambda i: hoja_planta(cfg, r, i, total),
        lambda i: hoja_secciones(cfg, r, i, total),
        lambda i: hoja_detalles(cfg, r, i, total),
        lambda i: hoja_calculos(cfg, r, M, i, total),
    ]
    with PdfPages(ruta_pdf) as pdf:
        meta = pdf.infodict()
        meta["Title"] = f"Planos de estructura · {cfg['proyecto']['titulo']}"
        meta["Author"] = cfg["proyecto"].get("estudio", "")
        for i, fn in enumerate(hojas, 1):
            h = fn(i)
            # el rótulo de escala del cajetín se fija tras dibujar las vistas
            _reescribir_escala(h)
            png = os.path.join(carpeta_png, f"{indice[i-1][0]}.png") if carpeta_png else None
            h.guardar(pdf, png)


def _reescribir_escala(h):
    """Vuelve a dibujar la celda ESCALA con el valor calculado en la vista."""
    x0, x1 = h.PX + h.PAD, h.W - h.M - h.PAD
    w = x1 - x0
    tops = [h.M + h.PAD]
    for hh in [14.0, 6.8, 7.1, 8.6]:
        tops.append(tops[-1] + hh)
    yb, yt = tops[3], tops[4]
    c2 = x0 + 0.42 * w
    h.t((c2 + x1) / 2, yb + 1.8, f"{h.escala_txt} · {h.cfg['proyecto'].get('formato', 'A3')}", 2.7, bold=True,
        ha="center")
