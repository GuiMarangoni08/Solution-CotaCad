import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime
import io

from main import app
from db.database import SessionLocal
from db.models import User, Levantamento
from core.security import get_password_hash

@pytest.fixture
def db():
    """Fixture para database session"""
    session = SessionLocal()
    yield session
    session.close()

@pytest.fixture
def client():
    """Fixture para test client"""
    return TestClient(app)

@pytest.fixture
def test_user(db: Session):
    """Cria usuário de teste"""
    user = User(
        email="test@example.com",
        password_hash=get_password_hash("teste123"),
        is_admin=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def auth_headers(client: TestClient, test_user: User):
    """Retorna headers com token JWT válido"""
    response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "teste123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

class TestLevantamentosAPI:
    """Testes para API de levantamentos"""

    def test_list_empty(self, client: TestClient, auth_headers: dict):
        """GET /api/levantamentos retorna lista vazia"""
        response = client.get("/api/levantamentos", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_create_without_auth(self, client: TestClient):
        """POST /api/levantamentos sem autenticação retorna 401"""
        dxf_content = b"0\nSECTION\n2\nENTITIES\n0\nENDSEC\n"
        response = client.post(
            "/api/levantamentos",
            files={"dxf_file": ("test.dxf", io.BytesIO(dxf_content))},
            data={
                "orc_numero": "21000",
                "nome": "Teste",
                "cliente": "Solution",
                "empreendimento": "Teste",
                "tipologia": "decorado"
            }
        )
        assert response.status_code == 401

    def test_create_missing_required_field(self, client: TestClient, auth_headers: dict):
        """POST /api/levantamentos com campo obrigatório vazio"""
        dxf_content = b"0\nSECTION\n"
        response = client.post(
            "/api/levantamentos",
            headers=auth_headers,
            files={"dxf_file": ("test.dxf", io.BytesIO(dxf_content))},
            data={
                "orc_numero": "",
                "nome": "Teste",
                "cliente": "Solution",
                "empreendimento": "Teste",
                "tipologia": "decorado"
            }
        )
        assert response.status_code == 422

    def test_create_invalid_file_type(self, client: TestClient, auth_headers: dict):
        """POST /api/levantamentos com arquivo não-DXF"""
        response = client.post(
            "/api/levantamentos",
            headers=auth_headers,
            files={"dxf_file": ("test.txt", io.BytesIO(b"texto"))},
            data={
                "orc_numero": "21000",
                "nome": "Teste",
                "cliente": "Solution",
                "empreendimento": "Teste",
                "tipologia": "decorado"
            }
        )
        assert response.status_code == 400
        assert "DXF" in response.json()["detail"]

    def test_create_success(self, client: TestClient, auth_headers: dict, db: Session):
        """POST /api/levantamentos cria levantamento com sucesso"""
        dxf_content = (
            b"  0\nSECTION\n  2\nHEADER\n  0\nENDSEC\n"
            b"  0\nSECTION\n  2\nENTITIES\n"
            b"  0\nLINE\n  8\nSOL - AMBIENTES INTERNOS\n"
            b"  0\nENDSEC\n"
        )

        response = client.post(
            "/api/levantamentos",
            headers=auth_headers,
            files={"dxf_file": ("test.dxf", io.BytesIO(dxf_content))},
            data={
                "orc_numero": "21000",
                "nome": "Teste Levantamento",
                "cliente": "Solution",
                "empreendimento": "Teste Project",
                "tipologia": "decorado"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["status"] == "processando"
        assert data["orc_numero"] == "21000"
        assert data["nome"] == "Teste Levantamento"

    def test_get_by_id(self, client: TestClient, auth_headers: dict):
        """GET /api/levantamentos/{id} retorna detalhe"""
        # Criar primeiro
        dxf_content = (
            b"  0\nSECTION\n  2\nHEADER\n  0\nENDSEC\n"
            b"  0\nSECTION\n  2\nENTITIES\n  0\nENDSEC\n"
        )
        create_response = client.post(
            "/api/levantamentos",
            headers=auth_headers,
            files={"dxf_file": ("test.dxf", io.BytesIO(dxf_content))},
            data={
                "orc_numero": "21001",
                "nome": "Teste",
                "cliente": "Solution",
                "empreendimento": "Teste",
                "tipologia": "decorado"
            }
        )
        lev_id = create_response.json()["id"]

        # Agora fazer GET
        response = client.get(f"/api/levantamentos/{lev_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == lev_id
        assert data["orc_numero"] == "21001"

    def test_list_shows_own_only(self, client: TestClient, auth_headers: dict, db: Session):
        """GET /api/levantamentos mostra apenas levantamentos do usuário"""
        # Criar levantamento
        dxf_content = (
            b"  0\nSECTION\n  2\nHEADER\n  0\nENDSEC\n"
            b"  0\nSECTION\n  2\nENTITIES\n  0\nENDSEC\n"
        )
        client.post(
            "/api/levantamentos",
            headers=auth_headers,
            files={"dxf_file": ("test.dxf", io.BytesIO(dxf_content))},
            data={
                "orc_numero": "21002",
                "nome": "Teste 1",
                "cliente": "Solution",
                "empreendimento": "Teste",
                "tipologia": "decorado"
            }
        )

        # Listar
        response = client.get("/api/levantamentos", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()) >= 1
        assert response.json()[0]["orc_numero"] == "21002"

class TestJobStatus:
    """Testes para polling de job status"""

    def test_job_status_enfileirado(self, client: TestClient, auth_headers: dict):
        """GET /api/levantamentos/jobs/{id} retorna status enfileirado"""
        # Criar levantamento e enfileirar job
        dxf_content = (
            b"  0\nSECTION\n  2\nHEADER\n  0\nENDSEC\n"
            b"  0\nSECTION\n  2\nENTITIES\n  0\nENDSEC\n"
        )
        create_response = client.post(
            "/api/levantamentos",
            headers=auth_headers,
            files={"dxf_file": ("test.dxf", io.BytesIO(dxf_content))},
            data={
                "orc_numero": "21003",
                "nome": "Teste",
                "cliente": "Solution",
                "empreendimento": "Teste",
                "tipologia": "decorado"
            }
        )
        lev_id = create_response.json()["id"]

        # Gerar Excel (enfileira job)
        job_response = client.post(
            f"/api/levantamentos/{lev_id}/gerar-excel",
            headers=auth_headers
        )
        assert job_response.status_code == 200
        job_id = job_response.json()["job_id"]

        # Verificar status do job
        status_response = client.get(
            f"/api/levantamentos/jobs/{job_id}",
            headers=auth_headers
        )
        assert status_response.status_code == 200
        data = status_response.json()
        assert data["id"] == job_id
        assert data["tipo"] == "gerar_excel"
