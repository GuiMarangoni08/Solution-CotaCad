"""
Parser DXF — extrai ambientes com área, perímetro, comprimento, largura e pé direito.
Fontes: LWPOLYLINE, POLYLINE, HATCH, BLOCK/INSERT, DIMENSION entities.
Vão osso: prioriza camadas estruturais (PAREDE, ALVENARIA, WALL) e ignora acabamentos.
"""

import re
import math
from typing import Optional
import ezdxf
from shapely.geometry import Polygon, Point, MultiPolygon, LineString
from shapely.ops import unary_union
from shapely.validation import make_valid
from .unit_normalizer import get_factor, to_m

# ── Camadas estruturais (vão osso) ───────────────────────────────────────────

_STRUCTURAL_MARKERS = [
    "parede", "alvenaria", "wall", "muro", "vao", "vão",
    "estrutura", "alv", "bloco", "tijolo", "concreto",
]
_FINISHING_MARKERS = [
    "revestimento", "reboco", "gesso", "ceramica", "azulejo",
    "acabamento", "pintura", "textura", "porcelana", "drywall",
    "emboço", "emboco", "chapisco",
]
_EXCLUDED_LAYER_LOWER = [
    "mob", "furniture", "mobiliario", "mobiliário",
    "dim", "cota", "dimensao", "dimensão",
    "text", "nota", "anotacao",
    "hachura", "pattern",
    "north", "norte", "grid", "eixo",
    "title", "titulo", "carimbo", "legenda",
    "eletrica", "hidraulica", "estrutural", "fundacao",
    "pen ", "pen0", "pen1", "pen2", "pen3",
]

def _is_structural_layer(layer: str) -> bool:
    """True se a camada representa parede estrutural (vão osso)."""
    low = layer.lower()
    if any(x in low for x in _FINISHING_MARKERS):
        return False
    return any(x in low for x in _STRUCTURAL_MARKERS)

def _layer_excluded(layer: str) -> bool:
    low = layer.lower()
    return any(kw in low for kw in _EXCLUDED_LAYER_LOWER)

# ── Palavras-chave de ambiente ────────────────────────────────────────────────

_ROOM_KEYWORDS = [
    "sala", "quarto", "suite", "suíte", "cozinha", "banheiro", "lavabo",
    "wc", "lavanderia", "garagem", "varanda", "sacada", "corredor", "hall",
    "escritório", "escritorio", "copa", "despensa", "área", "area",
    "dormitorio", "dormitório", "living", "jantar", "circulação", "circulacao",
    "terraço", "terraco", "quintal", "jardim", "piscina", "closet",
    "depósito", "deposito", "acesso", "entrada", "lobby", "recepção",
    "recepcao", "serviço", "servico", "amb", "ambiente",
]

_PD_PATTERNS = [
    r"p[eé]\s*dir[ei]+o\s*[=:]\s*([\d][,.][\d]+)",
    r"\bpd\s*[=:]\s*([\d][,.][\d]+)",
    r"\bh\s*[=:]\s*([\d][,.][\d]+)\s*m",
    r"\balt(?:ura)?\s*[=:]\s*([\d][,.][\d]+)",
    r"([\d]+[,.]\d+)\s*m?\s*p\.?\s*d\.?",
]

_MAX_GAP_M = 0.5
_MIN_AREA_M2 = 0.05


def _parse_number(s: str) -> float:
    return float(s.replace(",", "."))


def _looks_like_room(text: str) -> bool:
    t = text.lower().strip()
    return any(kw in t for kw in _ROOM_KEYWORDS)


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
    for t in texts_inside:
        if _looks_like_room(t["text"]):
            return t["text"].strip()
    for t in texts_inside:
        val = t["text"].strip()
        if 1 < len(val) <= 40 and not re.fullmatch(r"[\d\s.,mM²%°/\\-]+", val):
            return val
    if layer:
        cleaned = re.sub(r"^(A[-_]|AI[-_]|ARQ[-_]|\d+[-_])", "", layer, flags=re.IGNORECASE).strip()
        if cleaned and not _layer_excluded(cleaned):
            return cleaned
    return None


def _extract_pd_from_text(text: str, factor: float) -> Optional[float]:
    for pattern in _PD_PATTERNS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            val = _parse_number(m.group(1))
            if val > 10:
                val = val * factor
            return round(val, 2)
    return None


def _find_pd(texts_inside: list, factor: float) -> tuple[Optional[float], str]:
    for t in texts_inside:
        val = _extract_pd_from_text(t["text"], factor)
        if val:
            return val, "confirmed"
    return None, "missing"


# ── Extração de textos ────────────────────────────────────────────────────────

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


# ── Extração de DIMENSION entities ───────────────────────────────────────────

def _extract_linear_dimensions(msp, factor: float) -> list[dict]:
    """
    Extrai cotas lineares (dimtype 0=Linear, 1=Aligned).
    Retorna lista de {valor, p1, p2, text_pos}.
    """
    dims = []
    for e in msp:
        if e.dxftype() != "DIMENSION":
            continue
        try:
            dimtype = e.dxf.dimtype & 0x0F  # máscara para ignorar flags superiores
            if dimtype not in (0, 1):
                continue
            valor = to_m(e.dxf.actual_measurement, factor)
            if valor <= 0:
                continue
            p1 = e.dxf.defpoint
            p2 = e.dxf.defpoint2
            tp = e.dxf.text_midpoint
            dims.append({
                "valor": round(valor, 3),
                "p1": (to_m(p1.x, factor), to_m(p1.y, factor)),
                "p2": (to_m(p2.x, factor), to_m(p2.y, factor)),
                "text_pos": (to_m(tp.x, factor), to_m(tp.y, factor)),
            })
        except Exception:
            pass
    return dims


def _assign_dims_to_room(
    poly: Polygon,
    dims: list[dict],
    tol: float = 0.5,
) -> tuple[Optional[float], Optional[float]]:
    """
    Associa cotas DIMENSION ao polígono do ambiente.
    Retorna (comprimento, largura):
      - comprimento = maior valor encontrado
      - largura     = segundo maior valor (None se só uma cota)
    Usa buffer de tol metros para capturar cotas na borda da parede.
    Cotas compartilhadas entre ambientes são atribuídas a ambos (correto).
    """
    expanded = poly.buffer(tol)
    matched = []

    for d in dims:
        pt = Point(d["text_pos"])
        # Cota pertence ao ambiente se o texto está dentro do polígono expandido
        if expanded.contains(pt):
            matched.append(d["valor"])
            continue
        # Ou se a linha de medida cruzar o polígono (cota na parede compartilhada)
        try:
            line = LineString([d["p1"], d["p2"]])
            if poly.intersects(line.buffer(tol * 0.4)):
                matched.append(d["valor"])
        except Exception:
            pass

    if not matched:
        return None, None

    # Remove duplicatas muito próximas (tolerância de 2%)
    unique = []
    for v in sorted(set(matched), reverse=True):
        if not any(abs(v - u) / max(u, 0.001) < 0.02 for u in unique):
            unique.append(v)

    comp = unique[0]
    larg = unique[1] if len(unique) > 1 else None
    return comp, larg


# ── Bounding-rect mínimo (fallback) ──────────────────────────────────────────

def _get_dimensions(poly: Polygon) -> tuple[Optional[float], Optional[float]]:
    """Comprimento e largura pelo retângulo mínimo envolvente (estimativa)."""
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


# ── Extração de polilinhas ────────────────────────────────────────────────────

def _polyline_to_pts(entity, factor: float):
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
    results = []
    for e in msp:
        if e.dxftype() != "HATCH":
            continue
        layer = e.dxf.layer
        try:
            for path in e.paths:
                pts = []
                path_type = getattr(path, "PATH_TYPE", "")
                if path_type == "PolylinePath" or hasattr(path, "vertices"):
                    for v in path.vertices:
                        try:
                            pts.append((to_m(float(v[0]), factor), to_m(float(v[1]), factor)))
                        except Exception:
                            pass
                elif path_type == "EdgePath" or hasattr(path, "edges"):
                    for edge in path.edges:
                        try:
                            if hasattr(edge, "start"):
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
    results = []
    try:
        for block in doc.blocks:
            if block.name.startswith("*"):
                continue
            for e in block:
                res = _polyline_to_pts(e, factor)
                if res:
                    pts, closed, layer = res
                    results.append({"pts": pts, "closed": closed, "layer": layer, "source": "block"})
    except Exception:
        pass
    return results


# ── Deduplicação ─────────────────────────────────────────────────────────────

def _deduplicate(ambientes: list) -> list:
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


# ── Parser principal ──────────────────────────────────────────────────────────

def parse_dxf(file_path: str, user_unit: str = "mm") -> list[dict]:
    """
    Retorna lista de ambientes extraídos do DXF.
    Campos: nome, área, perímetro, comprimento, largura, pé direito, camada, fonte.
    Comprimento e largura: prioritariamente de entidades DIMENSION;
    fallback para retângulo mínimo envolvente (estimativa).
    Vão osso: camadas estruturais têm prioridade sobre acabamentos.
    """
    doc = ezdxf.readfile(file_path)
    msp = doc.modelspace()
    factor = get_factor(doc, user_unit)

    texts = _extract_texts(msp, factor)
    dims  = _extract_linear_dimensions(msp, factor)

    # Coleta candidatos a polígono de ambiente
    candidates = []

    # Polilinhas diretas
    for e in msp:
        res = _polyline_to_pts(e, factor)
        if res:
            pts, closed, layer = res
            structural = _is_structural_layer(layer)
            candidates.append({
                "pts": pts, "closed": closed,
                "layer": layer, "source": "poly",
                "structural": structural,
            })

    # HATCH
    for c in _extract_hatch_polys(msp, factor):
        c["structural"] = _is_structural_layer(c["layer"])
        candidates.append(c)

    # Blocos
    for c in _extract_from_blocks(doc, factor):
        c["structural"] = _is_structural_layer(c["layer"])
        candidates.append(c)

    # Se há camadas estruturais, prioriza-as (vão osso)
    has_structural = any(c["structural"] for c in candidates)
    if has_structural:
        candidates = [c for c in candidates if c["structural"] or not _layer_excluded(c["layer"])]

    ambientes = []

    for cand in candidates:
        pts   = cand["pts"]
        layer = cand["layer"]

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

        area_m2  = round(poly.area, 2)
        perim_m  = round(poly.length, 2)

        texts_inside = _text_inside(poly, texts)
        room_name    = _find_room_name(texts_inside, layer)
        pd_val, pd_flag = _find_pd(texts_inside, factor)

        # Comprimento e Largura — prioridade: DIMENSION entities
        comp, larg = _assign_dims_to_room(poly, dims)
        if comp is None:
            # Fallback: bounding-rect mínimo
            comp, larg = _get_dimensions(poly)

        amb = {
            "nome":              room_name,
            "nome_flag":         "confirmed" if room_name else "missing",
            "area":              area_m2,
            "area_flag":         area_flag,
            "perimetro":         perim_m,
            "perimetro_flag":    area_flag,
            "pe_direito":        pd_val,
            "pe_direito_flag":   pd_flag,
            "comprimento":       comp,
            "largura":           larg,
            "camada":            layer,
            "fonte":             "dxf",
            "_polygon":          poly,
        }
        ambientes.append(amb)

    # Deduplica e ordena por área (maior primeiro)
    ambientes = _deduplicate(ambientes)
    ambientes.sort(key=lambda a: a.get("area") or 0, reverse=True)

    # Textos de ambiente sem polilinha associada
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
                "nome":            t["text"].strip(),
                "nome_flag":       "confirmed",
                "area":            None,
                "area_flag":       "missing",
                "perimetro":       None,
                "perimetro_flag":  "missing",
                "pe_direito":      None,
                "pe_direito_flag": "missing",
                "comprimento":     None,
                "largura":         None,
                "camada":          None,
                "fonte":           "dxf",
                "_polygon":        None,
            })

    for a in ambientes:
        a.pop("_polygon", None)

    return ambientes
