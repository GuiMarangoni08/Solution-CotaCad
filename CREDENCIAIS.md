# Guia de Credenciais — CotaCAD

Siga na ordem abaixo. Cada etapa gera uma credencial que você vai usar nas próximas.

---

## 1. GitHub — repositório do código

1. Acesse **github.com** → faça login (ou crie conta)
2. Clique em **"New repository"**
3. Nome: `cotacad`
4. Visibilidade: **Private**
5. Clique em **"Create repository"**
6. Anote a URL do repositório: `https://github.com/SEU_USUARIO/cotacad`

### Enviar o código para o GitHub (rode no terminal dentro da pasta `cotacad`):
```bash
git init
git add .
git commit -m "chore: projeto inicial CotaCAD"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/cotacad.git
git push -u origin main
```

---

## 2. Supabase — banco de dados PostgreSQL

1. Acesse **supabase.com** → faça login → clique em **"New project"**
2. Nome: `cotacad`
3. Crie uma senha forte → anote ela (você vai precisar)
4. Região: **South America (São Paulo)** — mais próximo do Brasil
5. Clique em **"Create new project"** e aguarde ~2 minutos

### Pegar a DATABASE_URL:
1. No painel do projeto → menu lateral → **Settings** → **Database**
2. Role até **"Connection string"** → aba **"URI"**
3. Copie a string (começa com `postgresql://postgres:...`)
4. **Substitua `[YOUR-PASSWORD]` pela senha que você criou**

A string final fica assim:
```
postgresql://postgres:SUA_SENHA@db.XXXXX.supabase.co:5432/postgres
```

---

## 3. Hostinger VPS — servidor do backend

1. Acesse **hostinger.com.br** → **VPS Hosting**
2. Escolha o plano **KVM 2** (mínimo para OCR funcionar bem)
3. Sistema operacional: **Ubuntu 22.04**
4. Após criar → vá em **VPS → Gerenciar → Acesso SSH**
5. Anote o **IP do servidor** (ex: `123.456.78.90`)

### Configurar o VPS (acesse via SSH):
```bash
# No terminal do seu computador:
ssh root@IP_DO_SEU_VPS

# No servidor, rode este script de configuração:
apt update && apt install -y docker.io docker-compose git curl

# Criar pasta do projeto:
mkdir -p /opt/cotacad
cd /opt/cotacad
git clone https://github.com/SEU_USUARIO/cotacad.git .

# Criar arquivo .env no backend:
cd backend
cp .env.example .env
nano .env
# → Preencha DATABASE_URL, SECRET_KEY, FRONTEND_URL
# → Ctrl+X para salvar

# Subir o servidor:
docker compose up -d --build

# Verificar se está rodando:
curl http://localhost:8000/health
# Deve retornar: {"status":"ok"}
```

### Configurar domínio/HTTPS (opcional mas recomendado):
```bash
# Instalar Nginx como proxy reverso:
apt install -y nginx certbot python3-certbot-nginx

# Configure seu domínio no painel da Hostinger apontando para o IP do VPS
# Depois rode:
certbot --nginx -d api.seudominio.com.br
```

---

## 4. Vercel — hospedagem do frontend

1. Acesse **vercel.com** → faça login com GitHub
2. Clique em **"Add New Project"**
3. Selecione o repositório `cotacad`
4. **Root Directory:** `frontend`
5. Em **Environment Variables**, adicione:
   - Nome: `NEXT_PUBLIC_API_URL`
   - Valor: `https://IP_DO_VPS:8000/api` (ou `https://api.seudominio.com/api`)
6. Clique em **Deploy**
7. Anote a URL gerada (ex: `https://cotacad.vercel.app`)

---

## 5. GitHub Actions Secrets — CI/CD automático

No repositório GitHub → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**:

| Nome do Secret    | Valor                                          |
|-------------------|------------------------------------------------|
| `VPS_HOST`        | IP do seu VPS Hostinger (ex: `123.456.78.90`) |
| `VPS_USER`        | `root`                                         |
| `VPS_SSH_KEY`     | Chave SSH privada (veja abaixo)                |
| `BACKEND_URL`     | `https://api.seudominio.com` (ou `http://IP:8000`) |

### Gerar chave SSH para o GitHub Actions:
```bash
# No seu computador:
ssh-keygen -t ed25519 -C "github-actions-cotacad" -f ~/.ssh/cotacad_deploy

# Copie a chave PÚBLICA para o VPS:
ssh-copy-id -i ~/.ssh/cotacad_deploy.pub root@IP_DO_VPS

# O conteúdo da chave PRIVADA vai no secret VPS_SSH_KEY:
cat ~/.ssh/cotacad_deploy
# Copie tudo (de -----BEGIN até -----END-----) e cole no secret
```

---

## 6. Atualizar o .env do backend com a URL do Vercel

Após obter a URL do Vercel, atualize no VPS:
```bash
ssh root@IP_DO_VPS
cd /opt/cotacad/backend
nano .env
# Atualize FRONTEND_URL=https://cotacad.vercel.app
docker compose restart
```

---

## Resumo das variáveis de ambiente

### backend/.env (no VPS)
```env
DATABASE_URL=postgresql://postgres:SENHA@db.REF.supabase.co:5432/postgres
SECRET_KEY=chave_longa_aleatoria
ENVIRONMENT=production
FRONTEND_URL=https://cotacad.vercel.app
MAX_UPLOAD_MB=50
```

### frontend/.env.local (Vercel — via painel)
```env
NEXT_PUBLIC_API_URL=https://api.seudominio.com/api
```

---

## Fluxo após configurado

Toda vez que você fizer alterações no código e rodar:
```bash
git add .
git commit -m "descrição da mudança"
git push
```

O GitHub Actions vai:
1. Fazer SSH no VPS e atualizar o backend automaticamente
2. O Vercel vai detectar o push e atualizar o frontend automaticamente

**Você não precisa fazer mais nada manualmente.**
