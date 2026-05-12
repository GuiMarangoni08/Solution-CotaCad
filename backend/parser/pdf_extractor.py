"""
Extrator de medidas de PDF — suporta PDFs vetoriais e escaneados (OCR).
Para PDFs vetoriais: extrai linhas de cota (dimension lines) graficamente.
Para PDFs escaneados: OCR com detecção de padrões numéricos.
"""

import re
import math
from typing import Optional
import fitz  # pymupdf
from PIL import Image
import pytesseract
import cv2
import numpy as np

# ── Padrões de medidas em texto ───────────────────────────────────────────────

_ROOM_KEYWORDS = [
    "sala", "quarto", "suite", "suíte", "cozinha", "banheiro", "lavabo",
    "wc", "lavanderia", "garagem", "varanda", "sacada", "corredor", "hall",
    "escritório", "escritorio", "copa", "despensa", "área", "area",
    "dormitorio", "dormitório", "living", "jantar", "circulação", "circulacao",
    "terraço", "terraco", "quintal", "jardim", "piscina", "closet",
    "depósito", "deposito", "acesso", "entrada", "lobby", "recepção",
    "amb", "ambiente",
]

_MIN_TEXT_CHARS = 50


def _parse_number(s: str) -> float:
    return float(s.replace(",", "."))


def _looks_like_room(text: str) -> bool:
    t = text.lower().strip()
    return any(kw in t for kw in _ROOM_KEYWORDS)


def _is_plausible_dim(val: float) -> bool:
    """Dimensão plausível para um ambiente (0.30m a 50m)."""
    return 0.30 <= val <= 50.0


def _is_plausible_area(val: float) -> bool:
    return 0.10 <= val <= 2000.0


# ── Pré-processamento de imagem (OCR) ────────────────────────────────────────

def _preprocess_image(img_array: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    gray = cv2.equalizeHist(gray)
    binary = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 31, 10
    )
    denoised = cv2.fastNlMeansDenoising(binary, h=10)
    return denoised


# ── Extração de tokens (vetorial ou OCR) ─────────────────────────────────────

def _ocr_page(page: fitz.Page, dpi: int = 300) -> list[dict]:
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    img_array = np.array(img)
    processed = _preprocess_image(img_array)

    config = "--oem 3 --psm 6 -l por+eng"
    data = pytesseract.image_to_data(
        processed, config=config, output_type=pytesseract.Output.DICT
    )

    scale_x = page.rect.width / pix.width
    scale_y = page.rect.height / pix.height

    tokens = []
    for i, text in enumerate(data["text"]):
        text = text.strip()
        if not text or data["conf"][i] < 30:
            continue
        x = data["left"][i] * scale_x
        y = data["top"][i] * scale_y
        tokens.append({"text": text, "x": x, "y": y, "conf": data["conf"][i]})
    return tokens


def _extract_vectorial_tokens(page: fitz.Page) -> list[dict]:
    blocks = page.get_text("words")
    tokens = []
    for b in blocks:
        tokens.append({"text": b[4].strip(), "x": b[0], "y": b[1], "conf": 100})
    return tokens


def _is_vectorial(page: fitz.Page) -> bool:
    return len(page.get_text("text").strip()) >= _MIN_TEXT_CHARS


# ── Extração de linhas de cota (PDF vetorial) ─────────────────────────────────

def _extract_pdf_dim_lines(page: fitz.Page) -> list[dict]:
    """
    Em PDFs vetoriais, cotas são linhas finas (width pequeno) horizontais ou verticais
    com texto numérico próximo ao centro.
    Retorna lista de {valor_m (estimado em pts), cx, cy, comprimento_pts}.
    """
    dim_candidates = []
    try:
        # Coleta spans de texto numérico (candidatos a valor de cota)
        num_spans = []
        text_data = page.get_text("rawdict")
        for block in text_data.get("blocks", []):
            for ln in block.get("lines", []):
                for span in ln.get("spans", []):
                    txt = span["text"].strip()
                    # Aceita: 3,50 / 3.50 / 350 / 3500 (sem símbolo de unidade ou com m/cm/mm)
                    if re.match(r"^\d+[,.]?\d*\s*(?:m|cm|mm)?$", txt):
                        bb = span["bbox"]
                        num_spans.append({
                            "text": txt,
                            "cx": (bb[0] + bb[2]) / 2,
                            "cy": (bb[1] + bb[3]) / 2,
                        })

        # Coleta paths (linhas de cota são paths com items do tipo 'l' - lineto)
        drawings = page.get_drawings()
        for path in drawings:
            # Linha de cota: width pequeno, não é preenchimento
            stroke_width = path.get("width", 99)
            if stroke_width is None or stroke_width > 2.0:
                continue

            rect = path.get("rect")
            if not rect:
                continue

            w = abs(rect.x1 - rect.x0)
            h = abs(rect.y1 - rect.y0)

            # Linha = retângulo muito estreito em uma direção
            if min(w, h) > 8:
                continue

            length_pts = max(w, h)
            if length_pts < 15:  # muito curta
                continue

            cx = (rect.x0 + rect.x1) / 2
            cy = (rect.y0 + rect.y1) / 2

            # Texto numérico mais próximo (dentro de 60pt ~ 2cm a 72dpi)
            if not num_spans:
                continue
            closest = min(num_spans, key=lambda s: math.hypot(s["cx"] - cx, s["cy"] - cy))
            dist = math.hypot(closest["cx"] - cx, closest["cy"] - cy)
            if dist > 60:
                continue

            dim_candidates.append({
                "texto": closest["text"],
                "length_pts": length_pts,
                "cx": cx,
                "cy": cy,
            })

    except Exception:
        pass

    return dim_candidates


def _parse_dim_value(texto: str, page_unit: str = "mm") -> Optional[float]:
    """
    Converte texto de cota para metros.
    Ex: '3,50' → 3.50m  |  '350' → 0.35m (mm)  |  '3500' → 3.50m (mm)
    """
    txt = re.sub(r"[^\d,.]", "", texto).strip()
    if not txt:
        return None
    try:
        val = _parse_number(txt)
    except ValueError:
        return None

    # Heurística de unidade
    if val > 100:
        # Provavelmente em mm
        return round(val / 1000, 3)
    elif val > 10:
        # Provavelmente em cm
        return round(val / 100, 3)
    else:
        # Metros
        return round(val, 3)


# ── Cluster por proximidade ───────────────────────────────────────────────────

def _extract_tokens(pdf_path: str) -> tuple[list[dict], bool]:
    doc = fitz.open(pdf_path)
    all_tokens = []
    is_ocr = False
    for page in doc:
        if _is_vectorial(page):
            tokens = _extract_vectorial_tokens(page)
        else:
            tokens = _ocr_page(page)
            is_ocr = True
        all_tokens.extend(tokens)
    return all_tokens, is_ocr


def _cluster_by_proximity(tokens: list[dict], radius: float = 60) -> list[list[dict]]:
    visited = [False] * len(tokens)
    clusters = []
    for i, t in enumerate(tokens):
        if visited[i]:
            continue
        cluster = [t]
        visited[i] = True
        for j, t2 in enumerate(tokens):
            if visited[j]:
                continue
            if math.dist((t["x"], t["y"]), (t2["x"], t2["y"])) <= radius:
                cluster.append(t2)
                visited[j] = True
        clusters.append(cluster)
    return clusters


# ── Parse de um cluster de tokens ────────────────────────────────────────────

def _parse_cluster(
    cluster: list[dict],
    dim_lines: list[dict],
    user_unit: str = "mm",
) -> Optional[dict]:
    """
    Tenta extrair um ambiente de um cluster de tokens + linhas de cota próximas.
    """
    full_text = " ".join(t["text"] for t in cluster)

    # Centro do cluster (para associar linhas de cota)
    cx = sum(t["x"] for t in cluster) / len(cluster)
    cy = sum(t["y"] for t in cluster) / len(cluster)

    # Nome do ambiente
    nome = None
    for t in cluster:
        if _looks_like_room(t["text"]):
            nome = t["text"].strip()
            break

    area        = None
    area_flag   = "missing"
    pe_direito  = None
    pd_flag     = "missing"
    perimetro   = None
    perim_flag  = "missing"
    comprimento = None
    largura     = None

    # Área explícita: ex. 18,40 m²
    m = re.search(r"([\d]{1,4}[,.][\d]{1,4})\s*m[²2]", full_text, re.IGNORECASE)
    if m:
        area = round(_parse_number(m.group(1)), 2)
        if _is_plausible_area(area):
            area_flag = "confirmed"
        else:
            area = None

    # Pé direito
    for pat in [
        r"p[eé]\s*dir[ei]+o\s*[=:]\s*([\d][,.][\d]+)",
        r"\bpd\s*[=:]\s*([\d][,.][\d]+)",
        r"\bh\s*[=:]\s*([\d][,.][\d]+)\s*m",
        r"\balt(?:ura)?\s*[=:]\s*([\d][,.][\d]+)",
    ]:
        m2 = re.search(pat, full_text, re.IGNORECASE)
        if m2:
            val = _parse_number(m2.group(1))
            if val > 10:
                val *= 0.001 if user_unit == "mm" else 0.01
            if 1.5 <= val <= 6.0:
                pe_direito = round(val, 2)
                pd_flag = "confirmed"
                break

    # ── Linhas de cota próximas ao cluster ──────────────────────────────────
    # Raio de busca: 120pt ≈ 4cm a 72dpi
    nearby_dims = [
        d for d in dim_lines
        if math.hypot(d["cx"] - cx, d["cy"] - cy) < 120
    ]

    dim_values = []
    for d in nearby_dims:
        v = _parse_dim_value(d["texto"], user_unit)
        if v and _is_plausible_dim(v):
            dim_values.append(v)

    # Também busca padrão "NxM" no texto do cluster (ex: "3,50 x 4,20")
    m3 = re.search(
        r"([\d]+[,.][\d]+)\s*[xX×]\s*([\d]+[,.][\d]+)",
        full_text,
    )
    if m3:
        v1 = _parse_number(m3.group(1))
        v2 = _parse_number(m3.group(2))
        # Se valores parecem estar em mm, converte
        if v1 > 100: v1 /= 1000
        if v2 > 100: v2 /= 1000
        if _is_plausible_dim(v1) and _is_plausible_dim(v2):
            dim_values.extend([v1, v2])

    if dim_values:
        dim_values = sorted(set(round(v, 3) for v in dim_values), reverse=True)
        # Remove duplicatas próximas (2%)
        unique = []
        for v in dim_values:
            if not any(abs(v - u) / max(u, 0.001) < 0.02 for u in unique):
                unique.append(v)
        comprimento = unique[0] if len(unique) >= 1 else None
        largura     = unique[1] if len(unique) >= 2 else None

        # Calcula área se não encontrada explicitamente
        if area is None and comprimento and largura:
            area = round(comprimento * largura, 2)
            if _is_plausible_area(area):
                area_flag = "estimated"
            else:
                area = None

    # Valores genéricos como fallback de área
    if area is None:
        genericos = re.findall(r"(?<!\d)([\d]{1,3}[,.][\d]{2})(?!\d)", full_text)
        vals = [_parse_number(g) for g in genericos if _is_plausible_area(_parse_number(g))]
        if vals:
            area = round(max(vals), 2)
            area_flag = "estimated"

    if nome is None and area is None:
        return None

    return {
        "nome":            nome,
        "nome_flag":       "confirmed" if nome else "missing",
        "area":            area,
        "area_flag":       area_flag,
        "perimetro":       perimetro,
        "perimetro_flag":  perim_flag,
        "pe_direito":      pe_direito,
        "pe_direito_flag": pd_flag,
        "comprimento":     comprimento,
        "largura":         largura,
        "camada":          None,
        "fonte":           "pdf",
    }


# ── Extração principal ────────────────────────────────────────────────────────

def extract_pdf_measurements(
    pdf_path: str,
    user_unit: str = "mm",
) -> tuple[list[dict], float, bool]:
    """
    Extrai ambientes do PDF.
    Retorna: (ambientes, confianca_score 0-100, is_ocr)
    """
    doc = fitz.open(pdf_path)
    tokens, is_ocr = _extract_tokens(pdf_path)

    # Extrai linhas de cota de todas as páginas (só vetorial)
    all_dim_lines = []
    for page in doc:
        if _is_vectorial(page):
            all_dim_lines.extend(_extract_pdf_dim_lines(page))

    clusters = _cluster_by_proximity(tokens)

    ambientes = []
    for cluster in clusters:
        amb = _parse_cluster(cluster, all_dim_lines, user_unit)
        if amb:
            ambientes.append(amb)

    if not ambientes:
        return [], 0.0, is_ocr

    # Score de confiança
    total_fields = len(ambientes) * 5  # nome, area, perimetro, pe_direito, comprimento
    confirmed = sum(
        (1 if a["nome_flag"] == "confirmed" else 0) +
        (1 if a["area_flag"] == "confirmed" else 0) +
        (1 if a["perimetro_flag"] == "confirmed" else 0) +
        (1 if a["pe_direito_flag"] == "confirmed" else 0) +
        (1 if a["comprimento"] is not None else 0)
        for a in ambientes
    )
    confianca = round((confirmed / total_fields) * 100, 1) if total_fields > 0 else 0.0

    return ambientes, confianca, is_ocr
