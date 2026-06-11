from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, Boolean, Text, JSON
from sqlalchemy.orm import relationship
from .database import Base
import uuid


def new_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=new_uuid)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    criado_em = Column(DateTime, default=datetime.utcnow)
    projetos = relationship("Projeto", back_populates="user")


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
    user_id = Column(String, ForeignKey("users.id"), nullable=True)  # nullable p/ projetos existentes
    user = relationship("User", back_populates="projetos")
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

    comprimento = Column(Float, nullable=True)
    largura = Column(Float, nullable=True)

    camada = Column(String, nullable=True)
    fonte = Column(String, default="dxf")               # dxf | pdf | dxf+pdf | manual
    ordem = Column(Integer, default=0)


# ─── Novo: Levantamentos de Stands/Decorados/Triplex ───────────────────────

class Levantamento(Base):
    __tablename__ = "levantamentos"

    id = Column(String, primary_key=True, default=new_uuid)
    usuario_id = Column(String, ForeignKey("users.id"), nullable=False)
    usuario = relationship("User")

    # Metadados do projeto
    orc_numero = Column(String, nullable=False)
    nome = Column(String, nullable=False)
    cliente = Column(String, nullable=True)
    empreendimento = Column(String, nullable=True)
    tipologia = Column(String, nullable=False)  # "stand", "decorado", "triplex"

    # Upload
    arquivo_dxf_original = Column(String, nullable=True)  # filename do upload
    arquivo_dxf_path = Column(String, nullable=True)      # path no /tmp

    # Processamento
    tipo_detectado = Column(String, nullable=True)  # "SOL", "MAPEAMENTO", "TRIPLEX"
    status = Column(String, default="processando")  # processando|revisão|pronto|erro
    dados_extraidos = Column(JSON, nullable=True)   # dict com ambientes, áreas, piso, rodapé, etc
    dados_ajustados = Column(JSON, nullable=True)   # dict com ajustes do usuário
    erro_msg = Column(String, nullable=True)

    # Output
    arquivo_excel_url = Column(String, nullable=True)

    # Timestamps
    criado_em = Column(DateTime, default=datetime.utcnow)
    processado_em = Column(DateTime, nullable=True)
    finalizado_em = Column(DateTime, nullable=True)


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, default=new_uuid)
    levantamento_id = Column(String, ForeignKey("levantamentos.id"), nullable=False)
    levantamento = relationship("Levantamento")

    tipo = Column(String, nullable=False)  # "processar_dxf", "gerar_excel"
    status = Column(String, default="enfileirado")  # enfileirado|processando|pronto|erro
    resultado = Column(JSON, nullable=True)
    erro_msg = Column(String, nullable=True)

    criado_em = Column(DateTime, default=datetime.utcnow)
    finalizado_em = Column(DateTime, nullable=True)
