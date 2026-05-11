from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from .database import Base
import uuid


def new_uuid():
    return str(uuid.uuid4())


class Projeto(Base):
    __tablename__ = "projetos"

    id = Column(String, primary_key=True, default=new_uuid)
    nome = Column(String, nullable=False)
    arquivo_dxf = Column(String, nullable=True)
    arquivo_pdf = Column(String, nullable=True)
    unidade = Column(String, default="mm")          # mm ou m
    modo = Column(String, default="dxf")            # dxf | pdf | dxf+pdf
    fidelidade_score = Column(Float, nullable=True) # % medidas coincidentes DXF x PDF
    confianca_score = Column(Float, nullable=True)  # % confiança geral (modo só PDF)
    criado_em = Column(DateTime, default=datetime.utcnow)
    ambientes = relationship("Ambiente", back_populates="projeto", cascade="all, delete")


class Ambiente(Base):
    __tablename__ = "ambientes"

    id = Column(String, primary_key=True, default=new_uuid)
    projeto_id = Column(String, ForeignKey("projetos.id"), nullable=False)
    projeto = relationship("Projeto", back_populates="ambientes")

    nome = Column(String, nullable=True)
    nome_fonte = Column(String, default="auto")         # auto | manual
    nome_flag = Column(String, default="missing")       # confirmed | missing

    area = Column(Float, nullable=True)
    area_flag = Column(String, default="missing")       # confirmed | estimated | missing

    perimetro = Column(Float, nullable=True)
    perimetro_flag = Column(String, default="missing")

    pe_direito = Column(Float, nullable=True)
    pe_direito_flag = Column(String, default="missing")

    camada = Column(String, nullable=True)
    fonte = Column(String, default="dxf")               # dxf | pdf | dxf+pdf | manual
    ordem = Column(Integer, default=0)
