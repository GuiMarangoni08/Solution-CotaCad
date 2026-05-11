"""
Parser DXF — extrai ambientes com área, perímetro e pé direito.
Suporta polilinhas fechadas (confirmed), abertas com gap pequeno (estimated)
e ambientes identificados apenas por texto (missing).
"""

import re
import math
from typing import Optional
import ezdxf
from shapely.geometry import Polygon, Point, MultiPolygon
from shapely.validation import make_valid
from .unit_normalizer import get_factor, to_m

# Palavras-chave que indicam nome de ambiente (em PT-BR)
_ROOM_KEYWORDS = [
    "sala", "quarto", "suite", "suíte", "cozinha", "banheiro", "lavabo",
    "wc", "lavanderia", "garagem", "varanda", "sacada", "corredor", "hall",
    "escritório", "escritorio", "copa", "despensa", "área", "area",
    "dormitorio", "dormitório", "living", "jantar", "circulação", "circulacao",
    "terraço", "terraco", "quintal", "jardim", "piscina", "closet",
    "depósito", "deposito", "acesso", "entrada", "lobby"
]

# Padrões de pé direito em texto
_PD_PATTERNS = [
    r"p[eé]\s*dir[ei]+o\s*[=:]\s*([\d][,.][\d]+)",
    r"\bpd\s*[=:]\s*([\d][,.][\d]+)",
    r"\bh\s*[=:]\s*([\d][,.][\d]+)\s*m",
    r"\balt(?:ura)?\s*[=:]\s*([\d][,.][\d]+)",
    r"([\d]+[,.]\d+)\s*m?\s*p\.?\s*d\.?",
]

# Gap máximo (em metros) para considerar polilinha "quase fechada"
_MAX_GAP_M = 0.3


def _parse_number(s: str) -> float:
    return float(s.replace(",", "."))


def _looks_like_room(text: str) -> bool:
    t = text.lower().strip()
    for kw in _ROOM_KEYWORDS:
        if kw in t:
            return True
    return False


def _extract_pd_from_text(text: str, factor: float) -> Optional[float]:
    """Tenta extrair pé direito de uma string de texto."""
    for pattern in _PD_PATTERNS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            val = _parse_number(m.group(1))
            # Se valor parecer estar em mm (>10), converte
            if val > 10:
                val = val * factor
            return round(val, 2)
    return None


def _get_lwpolyline_points(entity, factor: float):
    """Extrai pontos de LWPOLYLINE em metros."""
    pts = [(to_m(x, factor), to_m(y, factor)) for x, y in entity.get_points("xy")]
    closed = entity.closed
    return pts, closed


def _get_polyline_points(entity, factor: float):
    """Extrai pontos de POLYLINE 2D em metros."""
    pts = []
    for v in entity.vertices:
        pts.append((to_m(v.dxf.location.x, factor), to_m(v.dxf.location.y, factor)))
    closed = bool(entity.dxf.flags & 1)
    return pts, closed


def _gap(pts) -> float:
    if len(pts) < 2:
        return 0.0
    return math.dist(pts[0], pts[-1])


def _build_polygon(pts, close=False) -> Optional[Polygon]:
    if close and pts[0] != pts[-1]:
        pts = pts + [pts[0]]
    if len(pts) < 3:
        return None
    try:
        poly = Polygon(pts)
        if not poly.is_valid:
            poly = make_valid(poly)
        if isinstance(poly, MultiPolygon):
            poly = max(poly.geoms, key=lambda g: g.area)
        return poly if poly.area > 0 else None
    except Exception:
        return None


def _text_inside(polygon: Polygon, texts: list) -> list:
    """Retorna textos cujo ponto de inserção está dentro do polígono."""
    inside = []
    for t in texts:
        try:
            if polygon.contains(Point(t["x"], t["y"])):
                inside.append(t)
        except Exception:
            pass
    return inside


def _find_room_name(texts_inside: list) -> Optional[str]:
    for t in texts_inside:
        if _looks_like_room(t["text"]):
            return t["text"].strip()
    # fallback: qualquer texto não numérico curto
    for t in texts_inside:
        val = t["text"].strip()
        if len(val) > 1 and not re.fullmatch(r"[\d\s.,mM²]+", val):
            return val
    return None


def _find_pd(texts_inside: list, factor: float) -> tuple[Optional[float], str]:
    for t in texts_inside:
        val = _extract_pd_from_text(t["text"], factor)
        if val:
            return val, "confirmed"
    return None, "missing"


def _extract_texts(msp, factor: float) -> list:
    texts = []
    for e in msp:
        try:
            if e.dxftype() == "TEXT":
                val = e.dxf.text.strip()
                ins = e.dxf.insert
                texts.append({"text": val, "x": to_m(ins.x, factor), "y": to_m(ins.y, factor)})
            elif e.dxftype() == "MTEXT":
                val = e.plain_mtext().strip()
                ins = e.dxf.insert
                texts.append({"text": val, "x": to_m(ins.x, factor), "y": to_m(ins.y, factor)})
        except Exception:
            pass
    return texts


def _extract_polylines(msp, factor: float) -> list:
    polylines = []
    for e in msp:
        try:
            if e.dxftype() == "LWPOLYLINE":
                pts, closed = _get_lwpolyline_points(e, factor)
                polylines.append({"pts": pts, "closed": closed, "layer": e.dxf.layer})
            elif e.dxftype() == "POLYLINE" and e.get_mode() in ("AcDb2dPolyline",):
                pts, closed = _get_polyline_points(e, factor)
                polylines.append({"pts": pts, "closed": closed, "layer": e.dxf.layer})
        except Exception:
            pass
    return polylines


def parse_dxf(file_path: str, user_unit: str = "mm") -> list[dict]:
    """
    Retorna lista de ambientes extraídos do DXF.
    Cada item: nome, nome_flag, area, area_flag, perimetro, perimetro_flag,
                pe_direito, pe_direito_flag, camada, fonte
    """
    doc = ezdxf.readfile(file_path)
    msp = doc.modelspace()
    factor = get_factor(doc, user_unit)

    texts = _extract_texts(msp, factor)
    polylines = _extract_polylines(msp, factor)

    ambientes = []
    used_text_indices = set()

    # --- Polilinhas fechadas (confirmed) ---
    for pl in polylines:
        pts = pl["pts"]
        if len(pts) < 3:
            continue

        is_closed = pl["closed"]
        gap = _gap(pts)
        area_flag = "confirmed"

        if is_closed or gap < 0.01:
            poly = _build_polygon(pts, close=True)
            area_flag = "confirmed"
        elif gap <= _MAX_GAP_M:
            poly = _build_polygon(pts, close=True)
            area_flag = "estimated"
        else:
            continue  # polilinha muito aberta — não usamos como área

        if poly is None or poly.area < 0.01:
            continue

        area_m2 = round(poly.area, 2)
        perim_m = round(poly.length, 2)

        texts_inside = _text_inside(poly, texts)
        room_name = _find_room_name(texts_inside)
        pd_val, pd_flag = _find_pd(texts_inside, factor)

        ambientes.append({
            "nome": room_name,
            "nome_flag": "confirmed" if room_name else "missing",
            "area": area_m2,
            "area_flag": area_flag,
            "perimetro": perim_m,
            "perimetro_flag": area_flag,  # mesmo nível de confiança da área
            "pe_direito": pd_val,
            "pe_direito_flag": pd_flag,
            "camada": pl["layer"],
            "fonte": "dxf",
        })

    # --- Textos de ambiente sem polilinha (listed as missing) ---
    covered = set()
    for amb in ambientes:
        pass  # já processados acima

    for i, t in enumerate(texts):
        if i in used_text_indices:
            continue
        if not _looks_like_room(t["text"]):
            continue
        # Verifica se esse texto já está dentro de um ambiente já detectado
        already_covered = False
        for amb in ambientes:
            if amb.get("_polygon") and amb["_polygon"].contains(Point(t["x"], t["y"])):
                already_covered = True
                break
        if not already_covered:
            ambientes.append({
                "nome": t["text"].strip(),
                "nome_flag": "confirmed",
                "area": None,
                "area_flag": "missing",
                "perimetro": None,
                "perimetro_flag": "missing",
                "pe_direito": None,
                "pe_direito_flag": "missing",
                "camada": None,
                "fonte": "dxf",
            })

    # Remove campo interno _polygon antes de retornar
    for a in ambientes:
        a.pop("_polygon", None)

    return ambientes
