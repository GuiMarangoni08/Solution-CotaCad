"""
Cross-reference entre medidas do DXF e do PDF.
Valida fidelidade e preenche lacunas do DXF com dados do PDF quando confiável.
"""

import math
from typing import Optional

# Tolerância para considerar duas medidas "iguais"
_TOLERANCE_PERCENT = 0.03   # 3%
_TOLERANCE_ABS_M = 0.05     # 5 cm absoluto

# Score mínimo para usar PDF como complemento
_MIN_FIDELIDADE = 70.0


def _values_match(a: Optional[float], b: Optional[float]) -> bool:
    if a is None or b is None:
        return False
    if abs(a - b) <= _TOLERANCE_ABS_M:
        return True
    if max(a, b) > 0:
        pct = abs(a - b) / max(a, b)
        return pct <= _TOLERANCE_PERCENT
    return False


def _calc_fidelidade(dxf_ambientes: list[dict], pdf_ambientes: list[dict]) -> float:
    """
    Calcula % de medidas (área, perímetro, pé direito) que coincidem
    entre DXF e PDF. Comparação por valor, não por nome.
    """
    if not dxf_ambientes or not pdf_ambientes:
        return 0.0

    total = 0
    matches = 0

    dxf_areas = [a["area"] for a in dxf_ambientes if a.get("area") is not None]
    pdf_areas = [a["area"] for a in pdf_ambientes if a.get("area") is not None]

    for da in dxf_areas:
        total += 1
        if any(_values_match(da, pa) for pa in pdf_areas):
            matches += 1

    dxf_pds = [a["pe_direito"] for a in dxf_ambientes if a.get("pe_direito") is not None]
    pdf_pds = [a["pe_direito"] for a in pdf_ambientes if a.get("pe_direito") is not None]

    for dp in dxf_pds:
        total += 1
        if any(_values_match(dp, pp) for pp in pdf_pds):
            matches += 1

    if total == 0:
        return 0.0
    return round((matches / total) * 100, 1)


def _find_best_pdf_match(dxf_amb: dict, pdf_ambientes: list[dict]) -> Optional[dict]:
    """
    Encontra o ambiente PDF mais compatível com um ambiente DXF.
    Critério: nome similar OU área compatível.
    """
    dxf_nome = (dxf_amb.get("nome") or "").lower()
    dxf_area = dxf_amb.get("area")

    best = None
    best_score = 0

    for pa in pdf_ambientes:
        score = 0
        pdf_nome = (pa.get("nome") or "").lower()
        pdf_area = pa.get("area")

        # Nome coincide
        if dxf_nome and pdf_nome and (dxf_nome in pdf_nome or pdf_nome in dxf_nome):
            score += 2

        # Área coincide
        if _values_match(dxf_area, pdf_area):
            score += 3

        if score > best_score:
            best_score = score
            best = pa

    return best if best_score >= 2 else None


def merge(dxf_ambientes: list[dict], pdf_ambientes: list[dict]) -> tuple[list[dict], float]:
    """
    Mescla ambientes DXF e PDF.
    - Calcula fidelidade
    - Se fidelidade >= threshold: preenche lacunas do DXF com dados do PDF
    - Se fidelidade < threshold: mantém DXF intacto, alerta baixa fidelidade
    - Retorna (ambientes_mesclados, fidelidade_score)
    """
    fidelidade = _calc_fidelidade(dxf_ambientes, pdf_ambientes)
    resultado = []

    if fidelidade >= _MIN_FIDELIDADE:
        # Complementa DXF com PDF
        for amb in dxf_ambientes:
            merged = dict(amb)
            pdf_match = _find_best_pdf_match(amb, pdf_ambientes)

            if pdf_match:
                # Nome: usa DXF se confirmado, senão usa PDF
                if merged["nome_flag"] == "missing" and pdf_match.get("nome"):
                    merged["nome"] = pdf_match["nome"]
                    merged["nome_flag"] = "confirmed"
                    merged["fonte"] = "dxf+pdf"

                # Área: usa DXF se confirmado, senão PDF
                if merged["area_flag"] in ("missing",) and pdf_match.get("area") is not None:
                    merged["area"] = pdf_match["area"]
                    merged["area_flag"] = "estimated"
                    merged["fonte"] = "dxf+pdf"

                # Perímetro: idem
                if merged["perimetro_flag"] == "missing" and pdf_match.get("perimetro") is not None:
                    merged["perimetro"] = pdf_match["perimetro"]
                    merged["perimetro_flag"] = "estimated"
                    merged["fonte"] = "dxf+pdf"

                # Pé direito: PDF frequentemente tem essa info
                if merged["pe_direito_flag"] == "missing" and pdf_match.get("pe_direito") is not None:
                    merged["pe_direito"] = pdf_match["pe_direito"]
                    merged["pe_direito_flag"] = "estimated"
                    merged["fonte"] = "dxf+pdf"

            resultado.append(merged)

        # Adiciona ambientes do PDF que não têm correspondente no DXF
        for pa in pdf_ambientes:
            has_match = any(
                _find_best_pdf_match(da, [pa]) is not None
                for da in dxf_ambientes
            )
            if not has_match and (pa.get("nome") or pa.get("area")):
                pa_copy = dict(pa)
                pa_copy["fonte"] = "pdf"
                resultado.append(pa_copy)
    else:
        # Fidelidade baixa — retorna DXF sem complementar, adiciona nota
        resultado = [dict(a) for a in dxf_ambientes]

    return resultado, fidelidade


def merge_pdf_only(pdf_ambientes: list[dict]) -> list[dict]:
    """Retorna ambientes do PDF sem DXF. Fonte = 'pdf' em todos."""
    return [dict(a) for a in pdf_ambientes]
