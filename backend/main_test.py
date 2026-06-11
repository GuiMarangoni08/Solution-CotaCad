"""Servidor mínimo para testar auth localmente (sem parsers DXF/PDF)."""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from db.database import Base, engine
from api.auth import router as auth_router

load_dotenv()

Base.metadata.create_all(bind=engine)

app = FastAPI(title="QuanttunAI Auth Test")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)

@app.get("/health")
def health():
    return {"status": "ok"}
