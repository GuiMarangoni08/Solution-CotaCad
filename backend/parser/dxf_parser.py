"""
Parser DXF — extrai ambientes com área, perímetro, comprimento, largura e pé direito.
Fontes: LWPOLYLINE, POLYLINE, HATCH, BLOCK/INSERT, DIMENSION entities.
Vão osso: prioriza camadas de piso (AI-Piso) e ignora acabamentos/mobiliário.
"""

import re
import math
from typing import Optional
import ezdxf
from shapely.geometry import Polygon, Point, MultiPolygon, LineString
from shapely.ops import unary_union
from shapely.validation import make_valid
from .unit_normalizer import get_factor, to_m

# ── Limites de área plausível para um ambiente ────────────────────────────────

_MIN_AREA_M2 = 0.30    # menor que isso é elemento (parafuso, vão, etc.)
_MAX_AREA_M2 = 5000.0  # maior que isso é lote/divisa/edificação inteira
_MAX_GAP_M   = 0.50    # gap máximo para polilinha "quase fechada"

# ── Prefixo XREF ──────────────────────────────────────────────────────────────

def _strip_xref_prefix(layer: str) -> str:
    """Remove prefixo de XREF — ex: 'PROJ$0$AI-Piso' → 'AI-Piso'."""
    if "$0$" in layer:
        return layer.split("$0$")[-1]
    return layer


# ── Classificação de camadas ──────────────────────────────────────────────────

# Camadas que SÃO ambientes / piso
_FLOOR_MARKERS = ["piso", "floor", "pavimento", "planta baixa"]

# Camadas que NÃO são ambientes (acabamentos, mobiliário, elementos)
_NON_ROOM_MARKERS = [
    "marcenaria", "movel", "móvel",
    "bas-por", "bas-rev", "porta", "janela", "esquadria", "arq-bas",
    "forro", "ceil",
    "alv-vista", "alv vista",
    "pedra", "granito", "mármore", "marmore",
    "drywall",
    "equip", "sanit",
    "curva", "curvas", "cn-curva",
    "alinhamento", "predial", "divisa",
    "_cx", "_bl",
    "pen-0", "pen0", "pen1", "pen2", "pen3", "pen-01",
    "imperme", "imperm",
    "marcação", "marcacao", "locação", "locacao",
    "cobertura",
    "estrutura met",
    "grade", "gradil",
    "calçada", "calcada",
]

# Camadas estruturais (vão osso)
_STRUCTURAL_MARKERS = [
    "parede", "alvenaria", "wall", "muro", "vao", "vão",
    "estrutura", "alv", "bloco", "tijolo", "concreto",
]
_FINISHING_MARKERS = [
    "revestimento", "reboco", "gesso", "ceramica", "azulejo",
    "acabamento", "pintura", "textura", "porcelana", "drywall",
    "emboço", "emboco", "chapisco",
]


def _strip(layer: str) -> str:
    return _strip_xref_prefix(layer).lower()


def _is_floor_layer(layer: str) -> bool:
    s = _strip(layer)
    return any(m in s for m in _FLOOR_MARKERS)


def _is_non_room_layer(layer: str) -> bool:
    s = _strip(layer)
    return any(m in s for m in _NON_ROOM_MARKERS)


def _is_structural_layer(layer: str) -> bool:
    s = _strip(layer)
    if any(x in s for x in _FINISHING_MARKERS):
        return False
    return any(x in s for x in _STRUCTURAL_MARKERS)


# ── Palavras-chave de nome de ambiente ────────────────────────────────────────

_ROOM_KEYWORDS = [
    "sala", "quarto", "suite", "suíte", "cozinha", "banheiro", "lavabo",
    "wc", "lavanderia", "garagem", "varanda", "sacada", "corredor", "hall",
    "escritório", "escritorio", "copa", "despensa", "área", "area",
    "dormitorio", "dormitório", "living", "jantar", "circulação", "circulacao",
    "terraço", "terraco", "quintal", "jardim", "piscina", "closet",
    "depósito", "deposito", "dep ", "acesso", "entrada", "lobby",
    "recepção", "recepcao", "serviço", "servico", "amb", "ambiente",
    "deck", "café", "cafe", "lounge", "maquete", "imersão", "imersao",
    "técnica", "tecnica", "reunião", "reuniao", "vestiário", "vestiario",
    "juridico", "jurídico", "staff", "atendimento", "vip", "apoio",
    "deposito", "deposição",
]

_PD_PATTERNS = [
    r"p[eé]\s*dir[ei]+o\s*[=:]\s*([\d][,.][\d]+)",
    r"\bpd\s*[=:]\s*([\d][,.][\d]+)",
    r"\bh\s*[=:]\s*([\d][,.][\d]+)\s*m",
    r"\balt(?:ura)?\s*[=:]\s*([\d][,.][\d]+)",
    r"([\d]+[,.]\d+)\s*m?\s*p\.?\s*d\.?",
]

# Nomes de camada que NÃO devem ser usados como nome de ambiente
_GENERIC_LAYER_NAMES = {
    "piso", "floor", "ai-piso", "ai-piso externo", "0", "defpoints",
    "parede", "alvenaria", "wall",
}


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
    """Retorna textos cujo ponto de inserção está dentro do polígono."""
    expanded = polygon.buffer(0.05)  # tolerância de 5cm
    inside = []
    for t in texts:
        try:
            if expanded.contains(Point(t["x"], t["y"])):
                inside.append(t)
        except Exception:
            pass
    return inside


def _find_room_name(texts_inside: list, layer_clean: str) -> Optional[str]:
    # Prioridade 1: texto que parece nome de ambiente
    for t in sorted(texts_inside, key=lambda x: len(x["text"]), reverse=True):
        if _looks_like_room(t["text"]):
            return t["text"].strip()
    # Prioridade 2: qualquer texto alfabético razoável (não número)
    for t in sorted(texts_inside, key=lambda x: len(x["text"]), reverse=True):
        val = t["text"].strip()
        if 2 < len(val) <= 60 and not re.fullmatch(r"[\d\s.,mM²%°/\\|–—-]+", val):
            return val
    # Prioridade 3: nome da camada (se não for genérica)
    cl = layer_clean.lower().strip()
    if cl not in _GENERIC_LAYER_NAMES:
        cleaned = re.sub(r"^(A[-_]|AI[-_]|ARQ[-_]|\d+[-_])", "", layer_clean, flags=re.IGNORECASE).strip()
        if cleaned and len(cleaned) > 2:
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


# ── Extração de textos (modelspace + blocos inseridos) ────────────────────────

def _extract_texts(doc, msp, factor: float) -> list:
    """
    Extrai TEXT e MTEXT do modelspace e de todos os blocos INSERT.
    Aplica transformação de posição/escala/rotação do INSERT.
    """
    texts = []

    def add_text(val: str, x: float, y: float):
        val = val.strip()
        if val:
            texts.append({"text": val, "x": to_m(x, factor), "y": to_m(y, factor)})

    # Direto no modelspace
    for e in msp:
        try:
            if e.dxftype() == "TEXT":
                add_text(e.dxf.text, e.dxf.insert.x, e.dxf.insert.y)
            elif e.dxftype() == "MTEXT":
                add_text(e.plain_mtext(), e.dxf.insert.x, e.dxf.insert.y)
        except Exception:
            pass

    # Dentro de blocos INSERT (inclui XREFs)
    for e in msp:
        if e.dxftype() != "INSERT":
            continue
        try:
            block_name = e.dxf.block_name
            if block_name not in doc.blocks:
                continue
            ins_x = float(e.dxf.insert.x)
            ins_y = float(e.dxf.insert.y)
            sx = float(getattr(e.dxf, "xscale", 1) or 1)
            sy = float(getattr(e.dxf, "yscale", 1) or 1)
            rot = math.radians(float(getattr(e.dxf, "rotation", 0) or 0))
            cos_r, sin_r = math.cos(rot), math.sin(rot)

            for be in doc.blocks[block_name]:
                try:
                    if be.dxftype() == "TEXT":
                        val = be.dxf.text
                        bx = float(be.dxf.insert.x) * sx
                        by = float(be.dxf.insert.y) * sy
                    elif be.dxftype() == "MTEXT":
                        val = be.plain_mtext()
                        bx = float(be.dxf.insert.x) * sx
                        by = float(be.dxf.insert.y) * sy
                    else:
                        continue
                    tx = bx * cos_r - by * sin_r + ins_x
                    ty = bx * sin_r + by * cos_r + ins_y
                    add_text(val, tx, ty)
                except Exception:
                    pass
        except Exception:
            pass

    return texts


# ── Extração de DIMENSION entities ───────────────────────────────────────────

def _extract_linear_dimensions(msp, factor: float) -> list[dict]:
    dims = []
    for e in msp:
        if e.dxftype() != "DIMENSION":
            continue
        try:
            dimtype = e.dxf.dimtype & 0x0F
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


def _assign_dims_to_room(poly: Polygon, dims: list[dict], tol: float = 0.5):
    expanded = poly.buffer(tol)
    matched = []
    for d in dims:
        pt = Point(d["text_pos"])
        if expanded.contains(pt):
            matched.append(d["valor"])
            continue
        try:
            line = LineString([d["p1"], d["p2"]])
            if poly.intersects(line.buffer(tol * 0.4)):
                matched.append(d["valor"])
        except Exception:
            pass
    if not matched:
        return None, None
    unique = []
    for v in sorted(set(matched), reverse=True):
        if not any(abs(v - u) / max(u, 0.001) < 0.02 for u in unique):
            unique.append(v)
    return unique[0], (unique[1] if len(unique) > 1 else None)


def _get_dimensions(poly: Polygon):
    try:
        mrr = poly.minimum_rotated_rectangle
        coords = list(mrr.exterior.coords)
        sides = []
        for i in range(4):
            dx = coords[i + 1][0] - coords[i][0]
            dy = coords[i + 1][1] - coords[i][1]
            sides.append(math.sqrt(dx * dx + dy * dy))
        return round(max(sides[0], sides[1]), 2), round(min(sides[0], sides[1]), 2)
    except Exception:
        return None, None


# ── Extração de polilinhas e hatches ─────────────────────────────────────────

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
    Prioriza camadas de piso (AI-Piso). Extrai nomes de TEXT/MTEXT dentro dos polígonos.
    Comprimento/Largura: de DIMENSION entities ou retângulo mínimo (fallback).
    """
    doc = ezdxf.readfile(file_path)
    msp = doc.modelspace()
    factor = get_factor(doc, user_unit)

    texts = _extract_texts(doc, msp, factor)
    dims  = _extract_linear_dimensions(msp, factor)

    # ── Coleta todos os candidatos ────────────────────────────────────────────
    all_candidates = []

    for e in msp:
        res = _polyline_to_pts(e, factor)
        if res:
            pts, closed, layer = res
            all_candidates.append({"pts": pts, "closed": closed, "layer": layer, "source": "poly"})

    for c in _extract_hatch_polys(msp, factor):
        all_candidates.append(c)

    # ── Decide estratégia de filtro ───────────────────────────────────────────
    # Se o DXF tem camadas de piso (AI-Piso), usa APENAS essas + estruturais
    has_floor_layers = any(_is_floor_layer(c["layer"]) for c in all_candidates)

    candidates = []
    for c in all_candidates:
        layer = c["layer"]

        # Sempre exclui camadas que claramente não são ambientes
        if _is_non_room_layer(layer):
            continue

        if has_floor_layers:
            # Com camadas de piso: só aceita piso ou estrutural
            if not _is_floor_layer(layer) and not _is_structural_layer(layer):
                continue

        c["layer_clean"] = _strip_xref_prefix(layer)
        candidates.append(c)

    # ── Constrói polígonos e extrai informações ───────────────────────────────
    ambientes = []

    for cand in candidates:
        pts        = cand["pts"]
        layer_clean = cand.get("layer_clean", cand["layer"])

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

        if poly is None:
            continue

        area_m2 = round(poly.area, 2)

        if area_m2 < _MIN_AREA_M2 or area_m2 > _MAX_AREA_M2:
            continue

        perim_m = round(poly.length, 2)

        texts_inside = _text_inside(poly, texts)
        room_name    = _find_room_name(texts_inside, layer_clean)
        pd_val, pd_flag = _find_pd(texts_inside, factor)

        comp, larg = _assign_dims_to_room(poly, dims)
        if comp is None:
            comp, larg = _get_dimensions(poly)

        ambientes.append({
            "nome":            room_name,
            "nome_flag":       "confirmed" if room_name else "missing",
            "area":            area_m2,
            "area_flag":       area_flag,
            "perimetro":       perim_m,
            "perimetro_flag":  area_flag,
            "pe_direito":      pd_val,
            "pe_direito_flag": pd_flag,
            "comprimento":     comp,
            "largura":         larg,
            "camada":          layer_clean,
            "fonte":           "dxf",
            "_polygon":        poly,
        })

    # ── Deduplica e ordena ────────────────────────────────────────────────────
    ambientes = _deduplicate(ambientes)
    ambientes.sort(key=lambda a: a.get("area") or 0, reverse=True)

    # ── Textos de ambiente sem polígono associado ─────────────────────────────
    for t in texts:
        if not _looks_like_room(t["text"]):
            continue
        pt = Point(t["x"], t["y"])
        already = any(
            a.get("_polygon") and a["_polygon"].contains(pt)
            for a in ambientes
        )
        if not already:
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
