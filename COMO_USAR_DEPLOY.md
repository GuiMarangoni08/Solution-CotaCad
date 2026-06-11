# 🚀 Como Usar o Deploy Script

Criei 2 versões do script de deploy automático. Escolha a que se adequa melhor ao seu sistema.

---

## **Option A: PowerShell (Windows) — RECOMENDADO**

### Passo 1: Abrir PowerShell

```powershell
# Windows: Pressionar Win+X e selecionar "Windows PowerShell"
# Ou: Cmd + R → pwsh
```

### Passo 2: Navegar até a pasta do projeto

```powershell
cd "C:\Users\guilherme.SOLUTION\Documents\RACEWEELL 2\cLAUDE CODE\cotacad"
```

### Passo 3: Executar o script

```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
.\deploy.ps1
```

### Passo 4: Acompanhar

O script vai:
1. ✅ Conectar ao VPS via SSH
2. ✅ Fazer git pull
3. ✅ Parar containers antigos
4. ✅ Build e subir novos containers
5. ✅ Aguardar 30 segundos
6. ✅ Mostrar logs e status

**Tempo estimado**: 3-5 minutos

---

## **Option B: Bash (Git Bash / Linux / macOS)**

### Passo 1: Abrir terminal

```bash
# Windows Git Bash: Right-click → Git Bash Here
# Linux/Mac: Terminal nativo
```

### Passo 2: Navegar até a pasta

```bash
cd "C:\Users\guilherme.SOLUTION\Documents\RACEWEELL 2\cLAUDE CODE\cotacad"
# ou no Linux/Mac:
# cd ~/projetos/cotacad
```

### Passo 3: Executar o script

```bash
chmod +x deploy.sh
./deploy.sh
```

### Passo 4: Acompanhar

Mesmo fluxo do PowerShell, mas com output em cores ANSI.

---

## ⚠️ Troubleshooting

### "Permission Denied" ao executar script

**PowerShell:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
.\deploy.ps1
```

**Bash:**
```bash
chmod +x deploy.sh
./deploy.sh
```

---

### "SSH: Could not resolve hostname"

Verificar:
```bash
ping 72.61.6.119
# Esperado: responde com ICMP
```

Se não responder, verificar conexão de internet.

---

### "Authentication failed"

Verificar credenciais SSH:
- Host: `72.61.6.119`
- User: `root`
- Password: `mo(rwQR!C@n&-5nV`

Tentar manualmente:
```bash
ssh root@72.61.6.119
# Quando pedir, copie: mo(rwQR!C@n&-5nV
```

---

### "Docker build failed"

Ver logs completos:
```bash
ssh root@72.61.6.119
cd /opt/cotacad
docker-compose logs -f api
```

Problemas comuns:
- Banco de dados não conectando → Verificar Supabase
- Arquivo .env incorreto → Verificar variáveis
- Porta 8000 em uso → `docker ps` e verificar containers

---

## ✅ Validação Depois de Deploy

Depois que o script terminar, teste:

### 1. Health Check Local (no VPS)
```bash
ssh root@72.61.6.119
curl http://localhost:8000/health
# Esperado: {"status":"ok"}
```

### 2. Health Check Remoto (seu computador)
```bash
curl https://cotacad-solution.duckdns.org/health
# Esperado: {"status":"ok"}
```

### 3. Frontend
```
https://solution-cota-cad.vercel.app
# Esperado: Carrega página de login
```

### 4. Teste E2E
1. Login: `test@solution.com` / `teste123`
2. Novo Levantamento
3. Upload DXF
4. Veja score de precisão aparecer ← Isso é novo!
5. Gere Excel

---

## 🎯 O Que Esperar

```
[1/6] Preparando SSH...
[2/6] Conectando via SSH...
[3/6] Git pull origin main
[4/6] Docker down
[5/6] Docker build & up
[6/6] Aguardando & validação

=== OUTPUT ===
(logs dos containers)

╔════════════════════════════════════════════════════════════╗
║           DEPLOY COMPLETO COM SUCESSO!                    ║
╚════════════════════════════════════════════════════════════╝

Proximos passos:
1. https://solution-cota-cad.vercel.app
2. curl https://cotacad-solution.duckdns.org/health
3. Login + teste
```

---

## 🆘 Se algo der muito errado

Volte ao manual:
```bash
ssh root@72.61.6.119
cd /opt/cotacad

# Ver status
docker ps
docker-compose logs api

# Limpar e recomeçar
docker-compose down -v
docker-compose up -d --build
```

---

## 📞 Checklist Final

- [ ] Script iniciado
- [ ] SSH conectou
- [ ] Git pull completou
- [ ] Docker build completou
- [ ] Health check retornou `{"status":"ok"}`
- [ ] Logs não mostram erros críticos
- [ ] Script terminou com "DEPLOY COMPLETO"
- [ ] Frontend acessível
- [ ] Backend respondendo em produção

Se tudo OK: **🎉 PRONTO PARA USAR!**

---

Escolha PowerShell (opção A) ou Bash (opção B) e execute!
