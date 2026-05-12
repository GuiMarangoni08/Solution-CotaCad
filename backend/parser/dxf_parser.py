"""
Parser DXF — extrai ambientes com área, perímetro e pé direito.
Suporta LWPOLYLINE, POLYLINE, HATCH e INSERT/BLOCK.
"""

import re
import math
from typing import Optional
import ezdxf
from shapely.geometry import Polygon, Point, MultiPolygon
from shapely.ops import unary_union
from shapely.validation import make_valid
from .unit_normalizer import get_factor, to_m

_ROOM_KEYWORDS = [
    "sala", "quarto", "suite", "suíte", "cozinha", "banheiro", "lavabo",
    "wc", "lavanderia", "garagem", "varanda", "sacada", "corredor", "hall",
    "escritório", "escritorio", "copa", "despensa", "área", "area",
    "dormitorio", "dormitório", "living", "jantar", "circulação", "circulacao",
    "terraço", "terraco", "quintal", "jardim", "piscina", "closet",
    "depósito", "deposito", "acesso", "entrada", "lobby", "recepção",
    "recpcao", "recepcao", "serviço", "servico", "roupeiro", "dressing",
    "amb", "ambiente", "apto", "apartamento"
]

# Camadas que claramente NÃO são ambientes
_EXCLUDED_LAYER_LOWER = [
    "mob", "furniture", "mobiliario", "mobiliário",
    "dim", "cota", "dimensao", "dimensão", "quota",
    "text", "nota", "anotacao", "anotação",
    "hachura", "pattern",
    "north", "norte", "compass",
    "grid", "eixo", "axis",
    "title", "titulo", "carimbo", "legenda",
    "eletrica", "eletrico", "hidraulica", "hidraulico",
    "estrutura", "estrutural", "fundacao",
    "pen ", "pen0", "pen1", "pen2", "pen3",
]

_PD_PATTERNS = [
    r"p[eé]\s*dir[ei]+o\s*[=:]\s*([\d][,.][\d]+)",
    r"\bpd\s*[=:]\s*([\d][,.][\d]+)",
    r"\bh\s*[=:]\s*([\d][,.][\d]+)\s*m",
    r"\balt(?:ura)?\s*[=:]\s*([\d][,.][\d]+)",
    r"([\d]+[,.]\d+)\s*m?\s*p\.?\s*d\.?",
]

_MAX_GAP_M = 0.5
_MIN_AREA_M2 = 0.05  # abaixo disso descartamos (5cm x 1m)


def _parse_number(s: str) -> float:
    return float(s.replace(",", "."))


def _looks_like_room(text: str) -> bool:
    t = text.lower().strip()
    for kw in _ROOM_KEYWORDS:
        if kw in t:
            return True
    return False


def _layer_excluded(layer: str) -> bool:
    low = layer.lower()
    return any(kw in low for kw in _EXCLUDED_LAYER_LOWER)


def _extract_pd_from_text(text: str, factor: float) -> Optional[float]:
    for pattern in _PD_PATTERNS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            val = _parse_number(m.group(1))
            if val > 10:
                val = val * factor
            return round(val, 2)
    return None


def _gap(pts) -> float:
    if len(pts) < 2:
        return 0.0
    return math.dist(pts[0], pts[-1])


def _build_polygon(pts, close=False) -> Optional[Polygon]:
    if close and len(pts) >= 1 and pts[0] != pts[-1]:
        pts = list(pts) + [pts[0]]
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
    inside = []
    for t in texts:
        try:
            if polygon.contains(Point(t["x"], t["y"])):
                inside.append(t)
        except Exception:
            pass
    return inside


def _find_room_name(texts_inside: list, layer: str) -> Optional[str]:
    # 1. Texto que parece nome de ambiente dentro do polígono
    for t in texts_inside:
        if _looks_like_room(t["text"]):
            return t["text"].strip()
    # 2. Qualquer texto curto não-numérico dentro
    for t in texts_inside:
        val = t["text"].strip()
        if 1 < len(val) <= 40 and not re.fullmatch(r"[\d\s.,mM²%°/\\-]+", val):
            return val
    # 3. Usa nome da camada (limpando prefixos comuns)
    if layer:
        cleaned = re.sub(r"^(A[-_]|AI[-_]|ARQ[-_]|\d+[-_])", "", layer, flags=re.IGNORECASE).strip()
        if cleaned and not _layer_excluded(cleaned):
            return cleaned
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


def _polyline_to_pts(entity, factor: float):
    """Retorna (pts, closed, layer) ou None."""
    try:
        t = entity.dxftype()
        if t == "LWPOLYLINE":
            pts = [(to_m(x, factor), to_m(y, factor)) for x, y in entity.get_points("xy")]
            return pts, entity.closed, entity.dxf.layer
        elif t == "POLYLINE":
            mode = entity.get_mode()
            if mode not in ("AcDb2dPolyline", "AcDb3dPolyline"):
                return None
            pts = [(to_m(v.dxf.location.x, factor), to_m(v.dxf.location.y, factor))
                   for v in entity.vertices]
            closed = bool(entity.dxf.flags & 1)
            return pts, closed, entity.dxf.layer
    except Exception:
        pass
    return None


def _extract_hatch_polys(msp, factor: float) -> list:
    """Extrai polígonos de entidades HATCH."""
    results = []
    for e in msp:
        if e.dxftype() != "HATCH":
            continue
        layer = e.dxf.layer
        try:
            for path in e.paths:
                pts = []
                path_type = getattr(path, 'PATH_TYPE', '')

                if path_type == 'PolylinePath' or hasattr(path, 'vertices'):
                    raw = path.vertices
                    for v in raw:
                        try:
                            pts.append((to_m(float(v[0]), factor), to_m(float(v[1]), factor)))
                        except Exception:
                            pass

                elif path_type == 'EdgePath' or hasattr(path, 'edges'):
                    for edge in path.edges:
                        edge_type = getattr(edge, 'EDGE_TYPE', '')
                        try:
                            if edge_type in ('LineEdge', '') and hasattr(edge, 'start'):
                                s = edge.start
                                pts.append((to_m(float(s[0]), factor), to_m(float(s[1]), factor)))
                        except Exception:
                            pass

                if len(pts) >= 3:
                    results.append({"pts": pts, "closed": True, "layer": layer, "source": "hatch"})
        except Exception:
            pass
    return results


def _extract_from_blocks(doc, factor: float) -> list:
    """Extrai polilinhas de dentro de blocos inseridos (INSERT)."""
    results = []
    try:
        for block in doc.blocks:
            if block.name.startswith("*"):  # blocos internos do AutoCAD
                continue
            for e in block:
                res = _polyline_to_pts(e, factor)
                if res:
                    pts, closed, layer = res
                    results.append({"pts": pts, "closed": closed, "layer": layer, "source": "block"})
    except Exception:
        pass
    return results


def _get_dimensions(poly: Polygon) -> tuple[Optional[float], Optional[float]]:
    """Retorna (comprimento, largura) em metros via retângulo mínimo envolvente."""
    try:
        mrr = poly.minimum_rotated_rectangle
        coords = list(mrr.exterior.coords)
        sides = []
        for i in range(4):
            dx = coords[i + 1][0] - coords[i][0]
            dy = coords[i + 1][1] - coords[i][1]
            sides.append(math.sqrt(dx * dx + dy * dy))
        comp = round(max(sides[0], sides[1]), 2)
        larg = round(min(sides[0], sides[1]), 2)
        return comp, larg
    except Exception:
        return None, None


def _deduplicate(ambientes: list) -> list:
    """Remove ambientes com polígonos quase idênticos (sobreposição > 90%)."""
    keep = []
    polys = []
    for amb in ambientes:
        poly = amb.get("_polygon")
        if poly is None:
            keep.append(amb)
            continue
        duplicate = False
        for existing in polys:
            try:
                inter = poly.intersection(existing)
                if inter.area / min(poly.area, existing.area) > 0.85:
                    duplicate = True
                    break
            except Exception:
                pass
        if not duplicate:
            keep.append(amb)
            polys.append(poly)
    return keep


def parse_dxf(file_path: str, user_unit: str = "mm") -> list[dict]:
    """
    Retorna lista de ambientes extraídos do DXF.
    """
    doc = ezdxf.readfile(file_path)
    msp = doc.modelspace()
    factor = get_factor(doc, user_unit)

    texts = _extract_texts(msp, factor)

    # Coleta todas as fontes de polígonos
    candidates = []

    # 1. Polilinhas diretas no model space
    for e in msp:
        res = _polyline_to_pts(e, factor)
        if res:
            pts, closed, layer = res
            candidates.append({"pts": pts, "closed": closed, "layer": layer, "source": "poly"})

    # 2. HATCH entities
    candidates.extend(_extract_hatch_polys(msp, factor))

    # 3. Polilinhas dentro de blocos
    candidates.extend(_extract_from_blocks(doc, factor))

    ambientes = []

    for cand in candidates:
        pts = cand["pts"]
        layer = cand["layer"]
        source = cand.get("source", "poly")

        if len(pts) < 3:
            continue

        is_closed = cand.get("closed", False)
        gap = _gap(pts)

        if is_closed or gap < 0.01:
            poly = _build_polygon(pts, close=True)
            area_flag = "confirmed"
        elif gap <= _MAX_GAP_M:
            poly = _build_polygon(pts, close=True)
            area_flag = "estimated"
        else:
            continue

        if poly is None or poly.area < _MIN_AREA_M2:
            continue

        area_m2 = round(poly.area, 2)
        perim_m = round(poly.length, 2)

        texts_inside = _text_inside(poly, texts)
        room_name = _find_room_name(texts_inside, layer)
        pd_val, pd_flag = _find_pd(texts_inside, factor)
        comp, larg = _get_dimensions(poly)

        amb = {
            "nome": room_name,
            "nome_flag": "confirmed" if room_name else "missing",
            "area": area_m2,
            "area_flag": area_flag,
            "perimetro": perim_m,
            "perimetro_flag": area_flag,
            "pe_direito": pd_val,
            "pe_direito_flag": pd_flag,
            "comprimento": comp,
            "largura": larg,
            "camada": layer,
            "fonte": "dxf",
            "_polygon": poly,
        }
        ambientes.append(amb)

    # Deduplica e ordena por área (maior primeiro)
    ambientes = _deduplicate(ambientes)
    ambientes.sort(key=lambda a: a.get("area") or 0, reverse=True)

    # Textos de ambiente sem polilinha correspondente
    for t in texts:
        if not _looks_like_room(t["text"]):
            continue
        pt = Point(t["x"], t["y"])
        already_covered = any(
            a.get("_polygon") and a["_polygon"].contains(pt)
            for a in ambientes
        )
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
                "_polygon": None,
            })

    # Remove campo interno
    for a in ambientes:
        a.pop("_polygon", None)

    return ambientes
