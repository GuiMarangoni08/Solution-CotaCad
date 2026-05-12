from typing import Optional, Literal
from pydantic import BaseModel


Flag = Literal["confirmed", "estimated", "missing"]
Fonte = Literal["dxf", "pdf", "dxf+pdf", "manual"]


class AmbienteOut(BaseModel):
    id: str
    nome: Optional[str]
    nome_flag: Flag
    area: Optional[float]
    area_flag: Flag
    perimetro: Optional[float]
    perimetro_flag: Flag
    pe_direito: Optional[float]
    pe_direito_flag: Flag
    comprimento: Optional[float]
    largura: Optional[float]
    camada: Optional[str]
    fonte: Fonte
    ordem: int

    class Config:
        from_attributes = True


class AmbienteUpdate(BaseModel):
    nome: Optional[str] = None
    area: Optional[float] = None
    perimetro: Optional[float] = None
    pe_direito: Optional[float] = None


class ProjetoOut(BaseModel):
    id: str
    nome: str
    unidade: str
    modo: str
    fidelidade_score: Optional[float]
    confianca_score: Optional[float]
    ambientes: list[AmbienteOut]

    class Config:
        from_attributes = True


class ProjetoListItem(BaseModel):
    id: str
    nome: str
    modo: str
    criado_em: str

    class Config:
        from_attributes = True
