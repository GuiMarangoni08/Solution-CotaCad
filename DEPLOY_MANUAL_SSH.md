# 🔧 Deploy Manual — SSH no VPS

**Se você estiver vendo isso, o deploy automático foi bloqueado por segurança. Vou instruir o deploy manual (é simples!).**

---

## 📋 Passo 1: Abrir Terminal SSH

### **Opção A: Git Bash (Windows)**
```bash
ssh root@72.61.6.119
# Quando pedir senha, copie e cole:
mo(rwQR!C@n&-5nV
```

### **Opção B: PowerShell (Windows)**
```powershell
ssh root@72.61.6.119
# Senha: mo(rwQR!C@n&-5nV
```

### **Opção C: hPanel Web (sem terminal)**
1. Acesse: https://hpanel.hostinger.com
2. Email: guimarangoni08@gmail.com
3. Senha: Guigui@2013
4. Vá em: VPS / Terminal web
5. Cole os comandos abaixo

---

## 🚀 Passo 2: Executar Deploy (copie-cola)

Dentro do terminal SSH, execute:

```bash
cd /opt/cotacad

echo "=== Git Pull ==="
git pull origin main

echo "=== Docker Down ==="
docker-compose -f backend/docker-compose.yml down

echo "=== Docker Build & Up ==="
docker-compose -f backend/docker-compose.yml up -d --build

echo "=== Esperando 15 segundos ==="
sleep 15

echo "=== Docker Status ==="
docker ps | grep cotacad

echo "=== Health Check ==="
curl -s http://localhost:8000/health

echo "=== Logs (ultimas 20 linhas) ==="
docker-compose -f backend/docker-compose.yml logs api | tail -20

echo "PRONTO!"
```

---

## ✅ Passo 3: Validar Deploy

Se viu algo como isso, está OK:

```
cotacad_db_1      postgres:15-alpine    Up 12 seconds    5432/tcp
cotacad_api_1     cotacad:latest        Up 5 seconds     0.0.0.0:8000->8000/tcp
{"status":"ok"}
```

---

## 🌐 Passo 4: Testar em Produção

```bash
# 1. Testar backend via domínio
curl https://cotacad-solution.duckdns.org/health

# 2. Abrir frontend
https://solution-cota-cad.vercel.app

# 3. Login
email: test@solution.com
password: teste123

# 4. Fazer upload de um DXF real
# 5. Verificar score de precisão
# 6. Gerar Excel
```

---

## 🆘 Se algo der errado

### **"Permission denied"**
- Verifique a senha: `mo(rwQR!C@n&-5nV`
- Tente novamente: `ssh root@72.61.6.119`

### **"Git pull failed"**
- Verificar se há commits locais não feitos
- `cd /opt/cotacad && git status`
- Se houver, fazer `git add . && git commit -m "backup"`

### **"Docker não inicia"**
- Ver logs: `docker logs cotacad_api_1`
- Limpar volumes: `docker-compose -f backend/docker-compose.yml down -v`
- Reconstruir: `docker-compose -f backend/docker-compose.yml up -d --build`

### **"Health check retorna erro"**
- Aguardar mais tempo (até 30 segundos)
- Ver logs: `docker-compose -f backend/docker-compose.yml logs api`
- Problema pode ser: banco de dados, arquivo env, ou código quebrado

---

## 📞 Se precisar de ajuda

Vá em: [DEPLOY_COM_OBSESSAO.md](./DEPLOY_COM_OBSESSAO.md) para troubleshooting completo

