# QuanttunAI — Sistema de Levantamento de Medidas Automático

Uma plataforma web para extração automática de medidas de projetos arquitetônicos (DXF) com revisão interativa e geração de relatórios em Excel.

**Status:** MVP Completo
**Stack:** Next.js 14 + FastAPI + PostgreSQL
**Deploy:** Vercel (Frontend) + Hostinger VPS (Backend)

---

## 🎯 Funcionalidades

- ✅ **Upload de DXF**: Arraste e solte ou clique para selecionar arquivo
- ✅ **Processamento Automático**: Detecta tipo (SOL/MAPEAMENTO/TRIPLEX) e extrai medidas
- ✅ **Revisão Interativa**: Ajuste dados extraídos antes de finalizar
- ✅ **Geração de Excel**: Exporte com um clique
- ✅ **Multi-Projeto**: Gerencie múltiplos levantamentos simultâneos
- ✅ **Autenticação**: Login/Signup para sua equipe

---

## 🚀 Quick Start

### 1. Clone e Setup

```bash
# Clone o repositório
git clone https://github.com/GuiMarangoni08/Solution-CotaCad.git
cd Solution-CotaCad

# Backend
cd backend
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

### 2. Configure Environment Variables

**Backend** (`backend/.env`):
```env
DATABASE_URL=postgresql://user:pass@db.supabase.co:5432/postgres
SECRET_KEY=seu_jwt_secret_aleatorio
ENVIRONMENT=development
FRONTEND_URL=http://localhost:3000
MAX_UPLOAD_MB=50
```

**Frontend** (`frontend/.env.local`):
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

### 3. Rode localmente

```bash
# Terminal 1 — Backend
cd backend
python -m uvicorn main:app --reload

# Terminal 2 — Frontend
cd frontend
npm run dev
```

Acesse: **http://localhost:3000**

---

## 📁 Estrutura do Projeto

```
cotacad/
├── backend/
│   ├── api/               # Endpoints FastAPI
│   │   ├── auth.py       # Login/Signup
│   │   ├── levantamentos.py  # CRUD levantamentos
│   │   └── deps.py       # Dependências (JWT, DB)
│   ├── db/
│   │   ├── models.py     # SQLAlchemy models
│   │   └── database.py   # Conexão Supabase
│   ├── extractores/      # DXF parsing
│   │   ├── detectar_tipo.py
│   │   └── build_sol.py
│   ├── tasks/            # Background jobs (APScheduler)
│   │   └── processar_dxf.py
│   ├── core/
│   │   └── security.py   # JWT, password hashing
│   ├── main.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── frontend/
│   ├── app/
│   │   ├── (auth)/       # Login/Signup pages
│   │   └── (protected)/
│   │       └── dashboard/levantamentos/
│   │           ├── page.tsx           # Lista
│   │           ├── novo/page.tsx      # Upload
│   │           └── [id]/page.tsx      # Detalhe
│   ├── components/
│   │   ├── LevantamentoCard.tsx
│   │   ├── DataPreview.tsx
│   │   └── ...
│   ├── contexts/
│   │   ├── AuthContext.tsx
│   │   └── LevantamentoContext.tsx
│   ├── package.json
│   ├── tsconfig.json
│   └── tailwind.config.ts
│
└── README.md
```

---

## 🔐 Autenticação

### Fluxo

1. **Signup**: Cria novo usuário
2. **Login**: Retorna JWT token
3. **Token**: Enviado em `Authorization: Bearer {token}` em requests

### Endpoints

```bash
# Criar usuário
POST /auth/signup
{
  "email": "user@example.com",
  "password": "senha123"
}

# Login
POST /auth/login
{
  "email": "user@example.com",
  "password": "senha123"
}
# Retorna: {"access_token": "eyJ...", "token_type": "bearer"}

# Dados do usuário autenticado
GET /auth/me
# Requer: Authorization header
```

---

## 📊 API Endpoints

### Levantamentos

```bash
# Listar (paginado)
GET /api/levantamentos
Authorization: Bearer {token}

# Criar + upload
POST /api/levantamentos
  - Form: dxf_file, orc_numero, nome, cliente, empreendimento, tipologia
  - Retorna: levantamento com status "processando"

# Detalhe
GET /api/levantamentos/{id}

# Atualizar dados ajustados
PATCH /api/levantamentos/{id}
{
  "dados_ajustados": [...]
}

# Gerar Excel
POST /api/levantamentos/{id}/gerar-excel
# Retorna: {"job_id": "...", "status": "enfileirado"}

# Status de job
GET /api/levantamentos/jobs/{job_id}
# Retorna: {"id": "...", "status": "processando|pronto|erro", ...}
```

---

## 🧪 Testes

### Backend

```bash
cd backend

# Instalar dependências de teste
pip install pytest pytest-asyncio pytest-cov

# Rodar testes
pytest

# Com cobertura
pytest --cov=. --cov-report=html
```

### Frontend

```bash
cd frontend

# Testes com vitest ou jest
npm test
```

---

## 📦 Fluxo de Processamento

```
1. Upload DXF (2MB max, .dxf only)
   ↓
2. Backend cria Levantamento (status="processando")
   ↓
3. APScheduler enfileira task (a cada 10s)
   ↓
4. Detecta tipo (SOL/MAPEAMENTO/TRIPLEX)
   ↓
5. Extrai medidas com build_sol.py/build_mapeamento.py/extract_triplex.py
   ↓
6. Salva em dados_extraidos
   ↓
7. Status muda para "revisao"
   ↓
8. Usuário faz ajustes (dados_ajustados)
   ↓
9. Clica "Gerar Excel"
   ↓
10. Job enfileirado (status="gerar_excel")
    ↓
11. Gera XLSX com dados finais
    ↓
12. Status muda para "pronto" + arquivo_excel_url
    ↓
13. Usuário baixa Excel
```

---

## 🐳 Deploy com Docker

```bash
cd backend

# Build image
docker build -t cotacad:latest .

# Rodar localmente
docker run -p 8000:8000 --env-file .env cotacad:latest

# Docker Compose (recomendado — inclui PostgreSQL)
docker-compose up -d
```

Para deploy em produção, veja [DEPLOY_INSTRUCTIONS.md](./DEPLOY_INSTRUCTIONS.md).

---

## 🔧 Troubleshooting

### Frontend não conecta ao backend
- Verificar `NEXT_PUBLIC_API_URL` em `.env.local`
- Confirmar backend está rodando: `curl http://localhost:8000/health`
- CORS: backend está configurado para aceitar requests do frontend

### Backend demora para processar DXF
- DXF muito grande? Limite é 2MB
- Verificar logs: `docker logs cotacad_api_1`
- APScheduler pode estar fora de sincronismo — reiniciar container

### Excel não é gerado
- Banco de dados conectado? Testar: `psql $DATABASE_URL -c "SELECT 1"`
- Supabase pausou? Acessar https://supabase.com/dashboard para reativar
- Verificar permissões de upload/download

---

## 📚 Documentação Adicional

- [DEPLOY_INSTRUCTIONS.md](./DEPLOY_INSTRUCTIONS.md) — Deploy em produção
- [PRIORIDADE_5_PLAN.md](./PRIORIDADE_5_PLAN.md) — Roadmap de melhorias
- Swagger/OpenAPI: `http://localhost:8000/docs` (quando backend está rodando)

---

## 👥 Time

- **Desenvolvedor**: Guilherme Marangoni
- **Email**: guimarangoni08@gmail.com
- **Repositório**: https://github.com/GuiMarangoni08/Solution-CotaCad

---

## 📝 Licença

Proprietary — Solution Consultoria & Tecnologia

---

## 🎓 Stack Versions

| Tecnologia | Versão |
|-----------|--------|
| Node.js | 18+ |
| Python | 3.10+ |
| Next.js | 14 |
| FastAPI | 0.111 |
| PostgreSQL | 15 |
| Docker | 20+ |

---

## Próximos Passos

- [ ] Suporte para MAPEAMENTO e TRIPLEX
- [ ] Batch processing (múltiplos DXF simultâneos)
- [ ] Histórico de revisions
- [ ] Integração com Revit/AutoCAD
- [ ] Export para PDF + memorial descritivo
- [ ] Colaboração em tempo real (múltiplos usuários)

