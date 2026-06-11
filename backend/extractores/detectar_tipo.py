"""
Detecta tipo de DXF baseado na estrutura de camadas.
Retorna: "SOL", "MAPEAMENTO", "TRIPLEX", ou "DESCONHECIDO"
"""

import ezdxf


def detectar_tipo_dxf(dxf_path: str) -> str:
    """
    Detecta o tipo de DXF pela análise de camadas.

    Args:
        dxf_path: Caminho absoluto do arquivo DXF

    Returns:
        "SOL" | "MAPEAMENTO" | "TRIPLEX" | "DESCONHECIDO"

    Estratégia:
    - SOL: Tem camada "SOL - AMBIENTES INTERNOS"
    - MAPEAMENTO: Tem "SOL - AMBIENTES INTERNOS" mas também "MAPEAMENTO" ou
      arquivo em pasta MAPEAMENTO
    - TRIPLEX: Tem camadas iniciadas com "TPLX_" ou "TRIPLEX"
    - Padrão: Usa extensão de filename ou primeira camada encontrada
    """
    try:
        doc = ezdxf.readfile(dxf_path)
        msp = doc.modelspace()

        # Coleta todas as camadas do arquivo
        layer_names = set()
        for entity in msp:
            if hasattr(entity.dxf, 'layer'):
                layer_names.add(entity.dxf.layer.upper())

        # Estratégia 1: Detecta TRIPLEX
        if any(layer.startswith('TPLX_') for layer in layer_names):
            return "TRIPLEX"
        if 'TRIPLEX' in layer_names or any('TRIPLEX' in layer for layer in layer_names):
            return "TRIPLEX"

        # Estratégia 2: Detecta SOL (padrão Solution/Exemplar)
        if 'SOL - AMBIENTES INTERNOS' in layer_names or \
           any('SOL' in layer and 'AMBIENTE' in layer for layer in layer_names):

            # Verifica se é MAPEAMENTO (variação do SOL)
            if "MAPEAMENTO" in dxf_path.upper():
                return "MAPEAMENTO"
            if any('MAPEAMENTO' in layer for layer in layer_names):
                return "MAPEAMENTO"

            return "SOL"

        # Estratégia 3: Fallback por padrão de filename
        filename_upper = dxf_path.upper()
        if "TRIPLEX" in filename_upper or "TPLX" in filename_upper:
            return "TRIPLEX"
        if "MAPEAMENTO" in filename_upper:
            return "MAPEAMENTO"
        if "SOL" in filename_upper or "LAY" in filename_upper or "LAYOUT" in filename_upper:
            return "SOL"

        return "DESCONHECIDO"

    except Exception as e:
        print(f"[WARN] Erro ao detectar tipo DXF: {e}")
        return "DESCONHECIDO"
