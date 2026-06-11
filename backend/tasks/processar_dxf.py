"""
Background tasks para processamento de DXF.
Usadas com APScheduler para rodar fora da thread da requisição.
"""

import os
from datetime import datetime
from sqlalchemy.orm import Session

from db.database import SessionLocal
from db.models import Levantamento, Job
from extractores.detectar_tipo import detectar_tipo_dxf
from extractores.build_sol import extrair_sol_dxf


def processar_dxf(levantamento_id: str) -> bool:
    """
    Background task: Processa DXF, detecta tipo, roda extrator.

    1. Detecta tipo de DXF (SOL, MAPEAMENTO, TRIPLEX)
    2. Roda extrator apropriado
    3. Salva dados_extraidos em DB
    4. Atualiza status: processando → revisão (ou erro)
    5. Retorna True se sucesso, False se erro

    Args:
        levantamento_id: UUID do levantamento

    Função é async-safe: cria sua própria session DB.
    """
    db = SessionLocal()

    try:
        # 1. Lê levantamento do DB
        lev = db.query(Levantamento).filter(Levantamento.id == levantamento_id).first()
        if not lev:
            print(f"[ERROR] Levantamento {levantamento_id} não encontrado")
            return False

        print(f"[INFO] Processando {levantamento_id}: {lev.orc_numero} - {lev.nome}")

        # 2. Detecta tipo
        tipo = detectar_tipo_dxf(lev.arquivo_dxf_path)
        print(f"[INFO] Tipo detectado: {tipo}")

        # 3. Roda extrator apropriado
        if tipo == "SOL":
            dados = extrair_sol_dxf(lev.arquivo_dxf_path, unidade="m")
        elif tipo == "MAPEAMENTO":
            # TODO: Implementar build_mapeamento quando necessário
            # Para agora, usa SOL como fallback
            dados = extrair_sol_dxf(lev.arquivo_dxf_path, unidade="m")
        elif tipo == "TRIPLEX":
            # TODO: Implementar extract_triplex quando necessário
            dados = {"status": "erro", "erro_msg": "TRIPLEX não implementado ainda"}
        else:
            dados = {"status": "erro", "erro_msg": f"Tipo desconhecido: {tipo}"}

        # 4. Salva no DB
        lev.tipo_detectado = tipo
        lev.dados_extraidos = dados
        lev.processado_em = datetime.utcnow()

        if dados.get("status") == "ok":
            lev.status = "revisão"  # Pronto para user revisar
            print(f"[OK] {len(dados.get('ambientes', []))} ambientes extraídos")
        else:
            lev.status = "erro"
            lev.erro_msg = dados.get("erro_msg", "Erro desconhecido")
            print(f"[ERROR] {lev.erro_msg}")

        db.commit()
        return True

    except Exception as e:
        print(f"[ERROR] Exceção ao processar {levantamento_id}: {e}")

        # Salva erro no DB
        try:
            lev = db.query(Levantamento).filter(Levantamento.id == levantamento_id).first()
            if lev:
                lev.status = "erro"
                lev.erro_msg = str(e)
                db.commit()
        except:
            pass

        return False

    finally:
        db.close()


def gerar_excel(levantamento_id: str) -> bool:
    """
    Background task: Gera Excel final com dados ajustados.

    1. Lê levantamento + dados_ajustados (ou dados_extraidos se não houver ajustes)
    2. Monta Excel com abas: Resumo, Por Ambiente, Memorial, etc
    3. Salva em /tmp ou S3
    4. Atualiza arquivo_excel_url
    5. Status: revisão → pronto

    Args:
        levantamento_id: UUID do levantamento

    Retorna: True se sucesso, False se erro
    """
    db = SessionLocal()

    try:
        # 1. Lê levantamento
        lev = db.query(Levantamento).filter(Levantamento.id == levantamento_id).first()
        if not lev:
            print(f"[ERROR] Levantamento {levantamento_id} não encontrado")
            return False

        print(f"[INFO] Gerando Excel para {levantamento_id}: {lev.nome}")

        # 2. Usa dados_ajustados ou dados_extraidos
        dados = lev.dados_ajustados or lev.dados_extraidos
        if not dados:
            raise Exception("Nenhum dado disponível para gerar Excel")

        # 3. TODO: Montar e salvar Excel aqui
        # Para MVP, apenas salva uma URL fake
        excel_filename = f"Levantamento_{lev.orc_numero}_{lev.nome.replace(' ', '_')}.xlsx"
        excel_url = f"/downloads/{excel_filename}"  # TODO: URL real após S3/storage implementado

        # 4. Atualiza DB
        lev.arquivo_excel_url = excel_url
        lev.status = "pronto"
        lev.finalizado_em = datetime.utcnow()
        db.commit()

        print(f"[OK] Excel gerado: {excel_filename}")
        return True

    except Exception as e:
        print(f"[ERROR] Erro ao gerar Excel {levantamento_id}: {e}")

        # Salva erro
        try:
            lev = db.query(Levantamento).filter(Levantamento.id == levantamento_id).first()
            if lev:
                lev.status = "erro"
                lev.erro_msg = f"Erro ao gerar Excel: {str(e)}"
                db.commit()
        except:
            pass

        return False

    finally:
        db.close()
