import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from db.database import Base, engine, SessionLocal
from db.models import Job, Levantamento
from api.routes import router
from api.auth import router as auth_router
from api.levantamentos import router as levantamentos_router
from tasks.processar_dxf import processar_dxf, gerar_excel

load_dotenv()

# Cria tabelas automaticamente na primeira execução
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="QuanttunAI API",
    description="Leitura automática de projetos arquitetônicos — DXF e PDF",
    version="2.0.0",
)

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:3000"],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(router, prefix="/api")
app.include_router(levantamentos_router)


# ─── Background Task Scheduler ───────────────────────────────────────────

def processar_jobs_enfileirados():
    """
    Background job: processa todas as tasks enfileiradas.
    Roda a cada 10 segundos.
    """
    db = SessionLocal()
    try:
        # Busca jobs enfileirados
        jobs = db.query(Job).filter(Job.status == "enfileirado").all()

        for job in jobs:
            print(f"[SCHEDULER] Processando job {job.id} (tipo={job.tipo})")
            job.status = "processando"
            db.commit()

            try:
                if job.tipo == "processar_dxf":
                    sucesso = processar_dxf(job.levantamento_id)
                elif job.tipo == "gerar_excel":
                    sucesso = gerar_excel(job.levantamento_id)
                else:
                    print(f"[WARN] Job tipo desconhecido: {job.tipo}")
                    sucesso = False

                # Atualiza job status
                job.status = "pronto" if sucesso else "erro"
                if not sucesso:
                    job.erro_msg = "Erro ao processar task"

            except Exception as e:
                job.status = "erro"
                job.erro_msg = str(e)
                print(f"[ERROR] Exceção ao processar job {job.id}: {e}")

            db.commit()

    except Exception as e:
        print(f"[ERROR] Erro no scheduler: {e}")
    finally:
        db.close()


# Inicializa scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(
    processar_jobs_enfileirados,
    trigger=IntervalTrigger(seconds=10),
    id="processar_jobs",
    name="Processa jobs enfileirados a cada 10s",
    replace_existing=True,
)


@app.on_event("startup")
async def startup_event():
    """Inicia o scheduler quando a app sobe."""
    scheduler.start()
    print("[INFO] Background scheduler iniciado")


@app.on_event("shutdown")
async def shutdown_event():
    """Para o scheduler quando a app encerra."""
    scheduler.shutdown()
    print("[INFO] Background scheduler encerrado")


@app.get("/health")
def health():
    return {"status": "ok"}
