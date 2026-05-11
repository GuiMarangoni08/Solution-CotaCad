"""
Normaliza todas as medidas para metros (m).
"""

import ezdxf

# Mapa de código INSUNITS do DXF → fator para converter em metros
_INSUNITS_TO_M = {
    0:  1.0,      # sem definição — usa o que o usuário informou
    1:  0.0254,   # polegadas
    2:  0.3048,   # pés
    3:  1609.344, # milhas
    4:  0.001,    # milímetros  ← padrão brasileiro
    5:  0.01,     # centímetros
    6:  1.0,      # metros
    7:  1000.0,   # quilômetros
    8:  0.0000254,# micropolegadas
    9:  0.00001,  # mícrons
    10: 100.0,    # decâmetros
    11: 1000.0,   # hectômetros (não padrão, mesmo que km)
    12: 0.001,    # angstroms — ignorar, tratar como mm
    13: 1e-9,     # nanômetros
    14: 1e-6,     # mícrons
    15: 0.1,      # decímetros
    16: 10.0,     # decâmetros
    17: 100.0,    # hectômetros
    18: 1000.0,   # gigametros — ignorar, tratar como km
    19: 1.496e11, # unidades astronômicas — ignorar
    20: 9.461e15, # anos-luz — ignorar
}

_USER_UNIT_TO_M = {
    "mm": 0.001,
    "cm": 0.01,
    "m":  1.0,
}


def get_factor(doc, user_unit: str = "mm") -> float:
    """
    Retorna o fator de conversão para metros.
    Tenta ler $INSUNITS do header DXF; se não encontrar, usa user_unit.
    """
    try:
        insunits = doc.header.get("$INSUNITS", 0)
        factor = _INSUNITS_TO_M.get(insunits, 0)
        if factor > 0 and insunits != 0:
            return factor
    except Exception:
        pass
    return _USER_UNIT_TO_M.get(user_unit, 0.001)


def to_m(value: float, factor: float) -> float:
    return round(value * factor, 4)
