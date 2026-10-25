#!/usr/bin/env python3
"""Geología del emplazamiento para cimentar sin estudio geotécnico.

1. Consulta el WMS del Mapa Geológico MAGNA 1:50.000 del IGME (GetFeatureInfo, capa 0 = litología) en unas
   coordenadas WGS84. Visor: https://info.igme.es/visor/ · WMS:
   https://mapas.igme.es/gis/services/Cartografia_Geologica/IGME_MAGNA_50/MapServer/WMSServer
2. Clasifica la descripción litológica (la del WMS o la copiada a mano de la leyenda del visor/hoja MAGNA)
   en una de las litologías geotécnicas de geotecnia.GEOLOGIA.

Uso:  python3 geologia.py LAT LON            → consulta IGME y clasifica
      python3 geologia.py --texto "Gravas, arenas y limos. Terrazas"   → sólo clasifica
"""
import json
import re
import sys
import unicodedata
import urllib.parse
import urllib.request

WMS_MAGNA = "https://mapas.igme.es/gis/services/Cartografia_Geologica/IGME_MAGNA_50/MapServer/WMSServer"

# Reglas por palabras clave (orden = prioridad). Se comparan sin tildes y en minúsculas.
REGLAS = [
    ("relleno_antropico", ["relleno", "antropico", "escombr", "vertedero"]),
    ("margas_yesiferas", ["yeso", "yesif", "evaporit", "anhidrit", "sal gema"]),
    ("arcilla_blanda", ["marisma", "fango", "turba", "limos organic", "albufera", "llanura de inundacion"]),
    ("granito", ["granit", "granodior", "tonalit", "gabro", "diorit", "porfid", "riolit", "basalt", "andesit"]),
    ("pizarra", ["pizarr", "esquist", "filit", "cuarcit", "gneis", "micacit", "grauvac"]),
    ("caliza", ["caliza", "calcar", "dolom", "marmol", "carniol"]),
    ("marga", ["marga", "margos", "arcillas y margas", "lutita", "argilit"]),
    ("arenisca", ["arenisca", "conglomerado cementado", "microconglomerado"]),
    ("conglomerado", ["conglomerado", "brecha"]),
    ("glacis_coluvial", ["glacis", "coluvi", "costra", "derrubio", "pie de monte", "cono de deyeccion", "abanico"]),
    ("grava_aluvial", ["grava", "terraza", "canto", "aluvial grueso"]),
    ("arena_suelta", ["arena", "duna", "playa", "eolic"]),
    ("arcilla_firme", ["arcilla", "limo", "aluvial", "fondo de valle", "loess"]),
]


def _norm(t):
    t = unicodedata.normalize("NFD", t.lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


RIESGO = ("relleno_antropico", "margas_yesiferas", "arcilla_blanda")  # prevalecen aunque no sean dominantes


def clasificar(texto):
    """Devuelve (clave_litologia, palabra_que_ha_decidido). Prevalecen los terrenos de riesgo (rellenos, yesos,
    fangos); en el resto manda la litología que se nombra primero (dominante en las leyendas MAGNA).
    Si nada coincide → ('arcilla_firme', None), hipótesis prudente para suelos."""
    n = _norm(texto)
    hallados = []
    for prioridad, (clave, palabras) in enumerate(REGLAS):
        for p in palabras:
            i = n.find(p)
            if i >= 0:
                hallados.append((0 if clave in RIESGO else 1, i, prioridad, clave, p))
    if not hallados:
        return "arcilla_firme", None
    _, _, _, clave, p = min(hallados)
    return clave, p


def consultar_magna(lat, lon, timeout=20):
    """GetFeatureInfo WMS 1.3.0 (EPSG:4326, orden de ejes lat,lon). Devuelve texto con los atributos."""
    d = 0.0005
    params = {
        "SERVICE": "WMS", "VERSION": "1.3.0", "REQUEST": "GetFeatureInfo", "LAYERS": "0", "QUERY_LAYERS": "0",
        "STYLES": "", "CRS": "EPSG:4326", "BBOX": f"{lat-d},{lon-d},{lat+d},{lon+d}", "WIDTH": "101",
        "HEIGHT": "101", "I": "50", "J": "50", "INFO_FORMAT": "text/plain", "FORMAT": "image/png",
    }
    url = WMS_MAGNA + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=timeout) as f:
        return f.read().decode("utf-8", "replace"), url


def main():
    if len(sys.argv) >= 3 and sys.argv[1] == "--texto":
        txt = " ".join(sys.argv[2:])
        fuente = "texto aportado"
    elif len(sys.argv) == 3:
        lat, lon = float(sys.argv[1]), float(sys.argv[2])
        try:
            txt, url = consultar_magna(lat, lon)
            fuente = url
        except Exception as ex:  # sin red: indicar cómo obtenerlo a mano
            print(json.dumps({"error": f"No se pudo consultar el IGME ({ex}).",
                              "alternativa": "Abrir https://info.igme.es/visor/ , capa MAGNA 50, pinchar en el punto "
                                             "y copiar la descripción de la unidad; luego: geologia.py --texto \"...\""},
                             ensure_ascii=False, indent=1))
            sys.exit(2)
    else:
        print(__doc__)
        sys.exit(1)
    clave, p = clasificar(txt)
    print(json.dumps({"fuente": fuente, "descripcion": re.sub(r"\s+", " ", txt)[:600], "litologia": clave,
                      "criterio": p}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
