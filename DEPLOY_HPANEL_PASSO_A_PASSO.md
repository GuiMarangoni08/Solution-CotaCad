# 🚀 Deploy via hPanel Terminal Web — Passo a Passo

**Tempo estimado:** 5 minutos
**Dificuldade:** Muito fácil (copy-paste)

---

## **Passo 1: Abrir hPanel**

Abra seu navegador e vá para:
```
https://hpanel.hostinger.com
```

Você deve ver uma tela de login assim:

```
┌─────────────────────────────────────────┐
│                HOSTINGER                │
│          Faça login em sua conta         │
│                                         │
│  Email: [_________________________]     │
│  Senha: [_________________________]     │
│                                         │
│            [  ENTRAR  ]                │
└─────────────────────────────────────────┘
```

---

## **Passo 2: Fazer Login**

Digite:
- **Email:** `guimarangoni08@gmail.com`
- **Senha:** `Guigui@2013`

Clique em **ENTRAR**

---

## **Passo 3: Ir para VPS**

Depois de logado, você verá a dashboard. Procure por:
- **Serviços** ou **Meus Serviços** (lado esquerdo)
- Encontre **VPS** ou **72.61.6.119**
- Clique nele

---

## **Passo 4: Abrir Terminal Web**

Na página do VPS, procure por:
- **Terminal** 
- **Web Terminal**
- Ou um ícone de **>_**

Clique para abrir o terminal web.

Você verá algo como:

```
root@vps:~# 
```

---

## **Passo 5: Copiar e Colar os Comandos**

No terminal web, copie e cole TUDO isto de uma vez:

```bash
cd /opt/cotacad && git pull origin main && docker-compose -f backend/docker-compose.yml down && docker-compose -f backend/docker-compose.yml up -d --build && sleep 30 && echo "=== STATUS ===" && docker ps | grep cotacad && echo "" && echo "=== HEALTH CHECK ===" && curl -s http://localhost:8000/health && echo "" && echo "=== LOGS ===" && docker-compose -f backend/docker-compose.yml logs api | tail -30
```

**Ou, se preferir executar em partes (mais fácil de acompanhar):**

### **Parte 1: Atualizar código**
```bash
cd /opt/cotacad
git pull origin main
```
Pressione **Enter** e aguarde a mensagem "Already up to date" ou "X files changed".

### **Parte 2: Parar containers antigos**
```bash
docker-compose -f backend/docker-compose.yml down
```
Pressione **Enter** e aguarde.

### **Parte 3: Construir e subir novos containers**
```bash
docker-compose -f backend/docker-compose.yml up -d --build
```
Pressione **Enter**. Isso vai demorar mais (2-3 minutos enquanto faz build).

### **Parte 4: Aguardar e validar**
```bash
sleep 30
docker ps | grep cotacad
```
Pressione **Enter**. Você deve ver os containers "cotacad_db" e "cotacad_api" como "Up".

### **Parte 5: Testar health**
```bash
curl -s http://localhost:8000/health
```
Pressione **Enter**. Deve retornar:
```
{"status":"ok"}
```

### **Parte 6: Ver logs**
```bash
docker-compose -f backend/docker-compose.yml logs api | tail -30
```
Pressione **Enter**. Você verá os logs da aplicação (últimas 30 linhas).

---

## ✅ **Sucesso!**

Se viu:
- `"status":"ok"` no health check
- Containers em status "Up"
- Logs sem erros críticos (palavras como "ERROR" em vermelho)

**Então o deploy foi bem-sucedido! 🎉**

---

## 🌐 **Teste Agora**

Abra em uma aba nova do navegador:

### **1. Frontend:**
```
https://solution-cota-cad.vercel.app
```

Você deve ver a página de login.

### **2. Backend Health:**
```
https://cotacad-solution.duckdns.org/health
```

Deve mostrar:
```
{"status":"ok"}
```

### **3. Fazer Login e Testar**

1. Clique em "Login" (ou vá direto em `/login`)
2. Email: `test@solution.com`
3. Senha: `teste123`
4. Clique "Entrar"
5. Clique "Novo Levantamento"
6. Selecione um arquivo .dxf
7. Preencha os dados
8. Clique "Criar Levantamento"
9. **Aguarde e veja o score de precisão aparecer!** ← Isso é o novo 🎯

---

## 🆘 **Se algo der errado**

### **"docker-compose: command not found"**
- Significa que Docker não está instalado corretamente
- Contactar suporte Hostinger

### **"git: command not found"**
- Git não está no VPS
- Contactar suporte Hostinger

### **Build falha com erro**
- Ver logs: `docker-compose -f backend/docker-compose.yml logs api`
- Causas comuns:
  - Banco de dados não conectando (Supabase pausou)
  - Arquivo .env incorreto
  - Porta 8000 em uso

### **Health check retorna erro**
- Aguardar mais tempo (até 2 minutos)
- Ver logs: `docker-compose -f backend/docker-compose.yml logs api`

### **Containers não ficam "Up"**
- `docker-compose -f backend/docker-compose.yml ps`
- `docker logs cotacad_api_1` para ver erro específico

---

## 💡 **Dicas**

1. **Copiar do terminal web:**
   - Selecionar texto → Ctrl+C (no seu PC)
   - Colar no terminal web → Ctrl+Shift+V

2. **Desfazer algo:**
   - Ctrl+C interrompe um comando em execução
   - Sempre com cuidado de não derrubar os containers

3. **Se perder:**
   - `cd /opt/cotacad` volta para a pasta do projeto
   - `docker ps` mostra containers ativos
   - `docker-compose logs api` mostra logs

---

## ✨ **Resumo**

| Passo | Ação | Tempo |
|-------|------|-------|
| 1 | hPanel login | 30s |
| 2 | Abrir terminal | 10s |
| 3 | Git pull | 20s |
| 4 | Docker down | 10s |
| 5 | Docker build | 90s |
| 6 | Docker up | 30s |
| 7 | Validar | 30s |
| **TOTAL** | **Deploy** | **~5 min** |

---

## 🎯 **Próximo Passo**

Depois de confirmar que tudo está funcionando:

1. ✅ Frontend carrega
2. ✅ Backend responde
3. ✅ Login funciona
4. ✅ Upload DXF funciona
5. ✅ Score de precisão aparece

**Então:** Comece a usar com sua equipe! 🚀

---

**Boa sorte!** 💪

