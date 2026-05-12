"""
Extrator de medidas de PDF — suporta PDFs vetoriais e escaneados (OCR).
Detecta automaticamente o tipo e aplica o pipeline adequado.
"""

import re
import math
from typing import Optional
import fitz  # pymupdf
from PIL import Image
import pytesseract
import cv2
import numpy as np

# Padrões de medidas em texto (m², m, cm, mm, valores decimais)
_MEASURE_PATTERNS = [
    # Área: ex: 18,40 m², 18.40m2
    (r"([\d]{1,4}[,.][\d]{1,4})\s*m[²2]", "area"),
    # Pé direito: ex: PD=2,80 / pé direito: 2,80 / h=2,80m
    (r"p[eé]\s*dir[ei]+o\s*[=:]\s*([\d][,.][\d]+)", "pe_direito"),
    (r"\bpd\s*[=:]\s*([\d][,.][\d]+)", "pe_direito"),
    (r"\bh\s*[=:]\s*([\d][,.][\d]+)\s*m", "pe_direito"),
    (r"\balt(?:ura)?\s*[=:]\s*([\d][,.][\d]+)", "pe_direito"),
    # Medida genérica: ex: 3,50 / 3.50 (sem unidade — contexto decide)
    (r"(?<!\d)([\d]{1,2}[,.][\d]{2,4})(?!\d)", "generico"),
    # Medida em mm: ex: 3500 (4-5 dígitos, sem ponto/vírgula)
    (r"(?<!\d)([1-9]\d{3,4})(?!\d)", "mm_candidato"),
]

_ROOM_KEYWORDS = [
    "sala", "quarto", "suite", "suíte", "cozinha", "banheiro", "lavabo",
    "wc", "lavanderia", "garagem", "varanda", "sacada", "corredor", "hall",
    "escritório", "escritorio", "copa", "despensa", "área", "area",
    "dormitorio", "dormitório", "living", "jantar", "circulação", "circulacao",
    "terraço", "terraco", "quintal", "jardim", "piscina", "closet",
    "depósito", "deposito", "acesso", "entrada", "lobby"
]

_MIN_TEXT_CHARS = 50  # mínimo de caracteres para considerar PDF vetorial


def _parse_number(s: str) -> float:
    return float(s.replace(",", "."))


def _looks_like_room(text: str) -> bool:
    t = text.lower().strip()
    return any(kw in t for kw in _ROOM_KEYWORDS)


def _preprocess_image(img_array: np.ndarray) -> np.ndarray:
    """Pré-processa imagem para melhorar OCR: escala de cinza, binarização, deskew."""
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    # Aumenta contraste
    gray = cv2.equalizeHist(gray)
    # Binarização adaptativa (lida bem com fundos não uniformes)
    binary = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 31, 10
    )
    # Remove ruído
    denoised = cv2.fastNlMeansDenoising(binary, h=10)
    return denoised


def _ocr_page(page: fitz.Page, dpi: int = 300) -> list[dict]:
    """Converte página para imagem e aplica OCR. Retorna lista de {text, x, y}."""
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    img_array = np.array(img)
    processed = _preprocess_image(img_array)

    # OCR com dados de posição
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


def _extract_vectorial(page: fitz.Page) -> list[dict]:
    """Extrai texto com posição de página vetorial."""
    blocks = page.get_text("words")  # (x0, y0, x1, y1, word, block_no, line_no, word_no)
    tokens = []
    for b in blocks:
        tokens.append({"text": b[4].strip(), "x": b[0], "y": b[1], "conf": 100})
    return tokens


def _is_vectorial(page: fitz.Page) -> bool:
    text = page.get_text("text").strip()
    return len(text) >= _MIN_TEXT_CHARS


def _extract_tokens(pdf_path: str) -> tuple[list[dict], bool]:
    """Extrai todos os tokens de todas as páginas. Retorna (tokens, is_ocr)."""
    doc = fitz.open(pdf_path)
    all_tokens = []
    is_ocr = False
    for page in doc:
        if _is_vectorial(page):
            tokens = _extract_vectorial(page)
        else:
            tokens = _ocr_page(page)
            is_ocr = True
        all_tokens.extend(tokens)
    return all_tokens, is_ocr


def _cluster_by_proximity(tokens: list[dict], radius: float = 60) -> list[list[dict]]:
    """Agrupa tokens próximos em clusters (possíveis ambientes)."""
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


def _parse_cluster(cluster: list[dict], user_unit: str = "mm") -> Optional[dict]:
    """Tenta extrair um ambiente de um cluster de tokens."""
    full_text = " ".join(t["text"] for t in cluster)

    # Nome do ambiente
    nome = None
    for t in cluster:
        if _looks_like_room(t["text"]):
            nome = t["text"].strip()
            break

    area = None
    area_flag = "missing"
    pe_direito = None
    pe_direito_flag = "missing"
    perimetro = None
    perimetro_flag = "missing"

    # Área
    m = re.search(r"([\d]{1,4}[,.][\d]{1,4})\s*m[²2]", full_text, re.IGNORECASE)
    if m:
        area = round(_parse_number(m.group(1)), 2)
        area_flag = "confirmed"

    # Pé direito
    for pattern, _ in _MEASURE_PATTERNS[1:4]:
        m = re.search(pattern, full_text, re.IGNORECASE)
        if m:
            val = _parse_number(m.group(1))
            if val > 10:
                val = val * (0.001 if user_unit == "mm" else 0.01)
            pe_direito = round(val, 2)
            pe_direito_flag = "confirmed"
            break

    # Se não achou área mas tem valores genéricos, tenta inferir
    if area is None:
        genericos = re.findall(r"(?<!\d)([\d]{1,3}[,.][\d]{2})(?!\d)", full_text)
        if genericos:
            vals = [_parse_number(g) for g in genericos if 1.0 < _parse_number(g) < 500]
            if vals:
                area = round(max(vals), 2)  # maior valor genérico como candidato a área
                area_flag = "estimated"

    # Só retorna se tem pelo menos nome ou área
    if nome is None and area is None:
        return None

    return {
        "nome": nome,
        "nome_flag": "confirmed" if nome else "missing",
        "area": area,
        "area_flag": area_flag,
        "perimetro": perimetro,
        "perimetro_flag": perimetro_flag,
        "pe_direito": pe_direito,
        "pe_direito_flag": pe_direito_flag,
        "comprimento": None,
        "largura": None,
        "camada": None,
        "fonte": "pdf",
    }


def extract_pdf_measurements(pdf_path: str, user_unit: str = "mm") -> tuple[list[dict], float, bool]:
    """
    Extrai ambientes do PDF.
    Retorna: (ambientes, confianca_score 0-100, is_ocr)
    """
    tokens, is_ocr = _extract_tokens(pdf_path)
    clusters = _cluster_by_proximity(tokens)

    ambientes = []
    for cluster in clusters:
        amb = _parse_cluster(cluster, user_unit)
        if amb:
            ambientes.append(amb)

    # Score de confiança: proporção de campos confirmed vs total
    if not ambientes:
        return [], 0.0, is_ocr

    total_fields = len(ambientes) * 4  # nome, area, perimetro, pe_direito
    confirmed = sum(
        (1 if a["nome_flag"] == "confirmed" else 0) +
        (1 if a["area_flag"] == "confirmed" else 0) +
        (1 if a["perimetro_flag"] == "confirmed" else 0) +
        (1 if a["pe_direito_flag"] == "confirmed" else 0)
        for a in ambientes
    )
    confianca = round((confirmed / total_fields) * 100, 1) if total_fields > 0 else 0.0

    return ambientes, confianca, is_ocr
