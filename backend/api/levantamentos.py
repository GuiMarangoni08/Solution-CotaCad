"""
Endpoints para levantamento de stands, decorados e triplex.
Fluxo: upload DXF → processamento → revisão → geração Excel
"""

import os
import shutil
import tempfile
from typing import Optional
from fastapi import APIRouter, File, Form, UploadFile, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from db.database import get_db
from db.models import Levantamento, Job, User
from api.deps import get_current_user

router = APIRouter(prefix="/api/levantamentos", tags=["levantamentos"])

_MAX_MB = int(os.getenv("MAX_UPLOAD_MB", "50"))


def _check_size(upload: UploadFile):
    """Valida tamanho do arquivo."""
    upload.file.seek(0, 2)
    size_mb = upload.file.tell() / (1024 * 1024)
    upload.file.seek(0)
    if size_mb > _MAX_MB:
        raise HTTPException(400, f"Arquivo maior que {_MAX_MB}MB")


def _save_temp(upload: UploadFile, suffix: str) -> str:
    """Salva arquivo em /tmp."""
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    shutil.copyfileobj(upload.file, tmp)
    tmp.close()
    return tmp.name


# ─── POST: Criar novo levantamento (upload DXF) ────────────────────────────

@router.post("", status_code=202)
async def criar_levantamento(
    dxf_file: UploadFile = File(...),
    orc_numero: str = Form(...),
    nome: str = Form(...),
    cliente: str = Form(default=""),
    empreendimento: str = Form(default=""),
    tipologia: str = Form(...),  # "stand", "decorado", "triplex"
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Cria novo levantamento e enfileira processamento do DXF.

    POST /api/levantamentos
    - Form: dxf_file, orc_numero, nome, cliente, empreendimento, tipologia
    - Auth: current_user via JWT
    → 202 Accepted: {id, status, tipo_detectado, orc_numero, nome}
    """
    _check_size(dxf_file)

    # Salva DXF em temp
    dxf_path = _save_temp(dxf_file, ".dxf")

    try:
        # Cria registro no DB
        lev = Levantamento(
            usuario_id=current_user.id,
            orc_numero=orc_numero,
            nome=nome,
            cliente=cliente,
            empreendimento=empreendimento,
            tipologia=tipologia,
            arquivo_dxf_original=dxf_file.filename,
            arquivo_dxf_path=dxf_path,
            status="processando",
        )
        db.add(lev)
        db.flush()
        lev_id = lev.id

        # Cria Job (background task)
        job = Job(
            levantamento_id=lev_id,
            tipo="processar_dxf",
            status="enfileirado",
        )
        db.add(job)
        db.commit()

        # ✓ Job enfileirado — scheduler o processará a cada 10s

        return {
            "id": lev_id,
            "status": "processando",
            "orc_numero": orc_numero,
            "nome": nome,
            "tipologia": tipologia,
            "arquivo": dxf_file.filename,
        }

    except Exception as e:
        if os.path.exists(dxf_path):
            os.unlink(dxf_path)
        raise HTTPException(500, str(e))


# ─── GET: Listar levantamentos do usuário ──────────────────────────────────

@router.get("")
def listar_levantamentos(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Lista todos os levantamentos do usuário autenticado.

    GET /api/levantamentos
    → 200: [
      {id, orc_numero, nome, status, tipologia, criado_em, dados_extraidos?, arquivo_excel_url?},
      ...
    ]
    """
    levs = db.query(Levantamento)\
        .filter(Levantamento.usuario_id == current_user.id)\
        .order_by(Levantamento.criado_em.desc())\
        .all()

    return [
        {
            "id": l.id,
            "orc_numero": l.orc_numero,
            "nome": l.nome,
            "cliente": l.cliente,
            "empreendimento": l.empreendimento,
            "tipologia": l.tipologia,
            "status": l.status,
            "criado_em": l.criado_em.isoformat() if l.criado_em else None,
            "processado_em": l.processado_em.isoformat() if l.processado_em else None,
            "tem_dados": bool(l.dados_extraidos),
            "tem_excel": bool(l.arquivo_excel_url),
        }
        for l in levs
    ]


# ─── GET: Detalhe de 1 levantamento ───────────────────────────────────────

@router.get("/{lev_id}")
def get_levantamento(
    lev_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retorna detalhe completo de um levantamento com dados extraídos/ajustados.

    GET /api/levantamentos/{lev_id}
    → 200: {
      id, orc_numero, nome, status, tipologia,
      dados_extraidos: [...],
      dados_ajustados: [...],
      arquivo_excel_url,
      erro_msg,
      criado_em, processado_em, finalizado_em
    }
    """
    lev = db.query(Levantamento)\
        .filter(Levantamento.id == lev_id, Levantamento.usuario_id == current_user.id)\
        .first()

    if not lev:
        raise HTTPException(404, "Levantamento não encontrado")

    return {
        "id": lev.id,
        "orc_numero": lev.orc_numero,
        "nome": lev.nome,
        "cliente": lev.cliente,
        "empreendimento": lev.empreendimento,
        "tipologia": lev.tipologia,
        "status": lev.status,
        "tipo_detectado": lev.tipo_detectado,
        "dados_extraidos": lev.dados_extraidos,
        "dados_ajustados": lev.dados_ajustados,
        "arquivo_excel_url": lev.arquivo_excel_url,
        "erro_msg": lev.erro_msg,
        "criado_em": lev.criado_em.isoformat() if lev.criado_em else None,
        "processado_em": lev.processado_em.isoformat() if lev.processado_em else None,
        "finalizado_em": lev.finalizado_em.isoformat() if lev.finalizado_em else None,
    }


# ─── PATCH: Salvar ajustes (antes de gerar Excel) ────────────────────────

@router.patch("/{lev_id}")
def atualizar_levantamento(
    lev_id: str,
    body: dict,  # {dados_ajustados: [{ambiente, area, piso, rodape, ...}, ...]}
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Salva dados_ajustados do usuário (edições feitas na interface).

    PATCH /api/levantamentos/{lev_id}
    {
      "dados_ajustados": [
        {ambiente: "LIVING", area: 45.5, piso_codigo: "PORCELANATO 01", ...},
        ...
      ]
    }
    → 200: {ok: true}
    """
    lev = db.query(Levantamento)\
        .filter(Levantamento.id == lev_id, Levantamento.usuario_id == current_user.id)\
        .first()

    if not lev:
        raise HTTPException(404, "Levantamento não encontrado")

    if "dados_ajustados" in body:
        lev.dados_ajustados = body["dados_ajustados"]
        db.commit()

    return {"ok": True}


# ─── POST: Gerar Excel final ───────────────────────────────────────────────

@router.post("/{lev_id}/gerar-excel", status_code=202)
def gerar_excel(
    lev_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Enfileira task de geração de Excel com dados ajustados.

    POST /api/levantamentos/{lev_id}/gerar-excel
    → 202 Accepted: {job_id, status: "enfileirado"}
    """
    lev = db.query(Levantamento)\
        .filter(Levantamento.id == lev_id, Levantamento.usuario_id == current_user.id)\
        .first()

    if not lev:
        raise HTTPException(404, "Levantamento não encontrado")

    if lev.status not in ("revisão", "pronto"):
        raise HTTPException(
            400,
            f"Levantamento em status '{lev.status}' não pode gerar Excel. "
            "Aguarde processamento ou revise dados."
        )

    # Cria Job para gerar Excel
    job = Job(
        levantamento_id=lev_id,
        tipo="gerar_excel",
        status="enfileirado",
    )
    db.add(job)
    db.commit()

    # ✓ Job enfileirado — scheduler o processará a cada 10s

    return {
        "job_id": job.id,
        "status": "enfileirado",
        "tipo": "gerar_excel",
    }


# ─── GET: Status de background task ────────────────────────────────────────

@router.get("/jobs/{job_id}")
def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retorna status de uma background task (processar_dxf ou gerar_excel).

    GET /api/levantamentos/jobs/{job_id}
    → 200: {
      id, tipo, status, resultado_url, erro_msg, criado_em, finalizado_em
    }
    """
    job = db.query(Job)\
        .filter(Job.id == job_id)\
        .first()

    if not job:
        raise HTTPException(404, "Job não encontrado")

    # Verifica se usuário tem acesso (via relacionamento com Levantamento)
    lev = job.levantamento
    if lev.usuario_id != current_user.id:
        raise HTTPException(403, "Acesso negado")

    return {
        "id": job.id,
        "tipo": job.tipo,
        "status": job.status,
        "resultado": job.resultado,
        "erro_msg": job.erro_msg,
        "criado_em": job.criado_em.isoformat() if job.criado_em else None,
        "finalizado_em": job.finalizado_em.isoformat() if job.finalizado_em else None,
    }
