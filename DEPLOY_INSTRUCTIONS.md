# 🚀 QuanttunAI: Instruções de Deploy

## VPS Hostinger

### 1. Aceder ao VPS via SSH

```bash
ssh root@72.61.6.119
# Senha: mo(rwQR!C@n&-5nV
```

### 2. Deploy do Backend

```bash
cd /opt/cotacad

# Atualizar código
git pull origin main

# Parar containers antigos
docker-compose -f backend/docker-compose.yml down

# Compilar e iniciar
docker-compose -f backend/docker-compose.yml up -d --build

# Verificar logs
docker-compose -f backend/docker-compose.yml logs -f api
```

### 3. Verificar status

```bash
# Backend health check
curl https://cotacad-solution.duckdns.org/health

# Docker status
docker ps
docker logs cotacad_api_1

# Logs do nginx
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

---

## Vercel (Frontend)

✅ **Deploy automático**: Já está configurado no repositório GitHub.

Quando fizer `git push origin main`:
1. GitHub webhook notifica Vercel
2. Vercel faz build e deploy automático
3. Site atualiza em ~30 segundos

**URL:** https://solution-cota-cad.vercel.app

Para verificar builds:
- Painel: https://vercel.com/dashboard
- Logs: https://vercel.com/docs/builds

---

## Checklist de Deploy

- [ ] Backend: `docker-compose up -d --build`
- [ ] Verificar: `curl https://cotacad-solution.duckdns.org/health`
- [ ] Frontend: Push para `main` (auto-deploy via Vercel)
- [ ] Verificar: Acessar https://solution-cota-cad.vercel.app
- [ ] Testes: Login → Upload DXF → Gerar Excel

---

## Variáveis de Ambiente Críticas

### Backend (.env no VPS)

```env
DATABASE_URL=postgresql://postgres:...@db...supabase.co:5432/postgres
SECRET_KEY=seu_jwt_secret_aleatorio
ENVIRONMENT=production
FRONTEND_URL=https://solution-cota-cad.vercel.app
MAX_UPLOAD_MB=50
```

### Frontend (.env.local — não versionado)

```env
NEXT_PUBLIC_API_URL=https://cotacad-solution.duckdns.org/api
```

---

## Troubleshooting

### Backend não inicia
```bash
# Limpar volumes antigos
docker-compose -f backend/docker-compose.yml down -v
docker-compose -f backend/docker-compose.yml up -d --build
```

### Conexão com banco falha
```bash
# Verificar se Supabase está ativo
# Acessar: https://supabase.com/dashboard

# Re-testar conexão localmente
psql postgresql://user:pass@db...supabase.co:5432/postgres
```

### Frontend: CORS ou 404 API
```bash
# Verificar NEXT_PUBLIC_API_URL em .env.local
# Deve apontar para: https://cotacad-solution.duckdns.org/api
```

---

## Rollback (se necessário)

```bash
cd /opt/cotacad
git revert HEAD
git push origin main
docker-compose -f backend/docker-compose.yml down
docker-compose -f backend/docker-compose.yml up -d --build
```

---

## Links úteis

| Recurso | URL |
|---------|-----|
| Vercel Dashboard | https://vercel.com/dashboard |
| GitHub Repo | https://github.com/GuiMarangoni08/Solution-CotaCad |
| Supabase Console | https://supabase.com/dashboard |
| hPanel (Hostinger) | https://hpanel.hostinger.com |
| Backend Health | https://cotacad-solution.duckdns.org/health |
| Frontend App | https://solution-cota-cad.vercel.app |

