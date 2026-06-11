# ⚡ DEPLOY AGORA — Copie e Cole

Escolha uma opção e siga:

---

## **OPÇÃO 1: PowerShell (Windows) — MAIS FÁCIL**

### Passo 1: Abrir PowerShell

Windows 11:
- Pressione `Win + X`
- Clique em "Terminal (Admin)"
- Ou: `Win + R` → `pwsh` → Enter

### Passo 2: Copie e cole TUDO isto:

```powershell
cd "C:\Users\guilherme.SOLUTION\Documents\RACEWEELL 2\cLAUDE CODE\cotacad"
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
.\deploy.ps1
```

### Passo 3: Pressione Enter

Pronto! O script vai:
- Conectar ao VPS
- Fazer git pull
- Rebuild dos containers
- Mostrar resultado

**Tempo:** ~5 minutos

---

## **OPÇÃO 2: Git Bash (Windows)**

### Passo 1: Abrir Git Bash

Navegue até a pasta do projeto → Right-click → "Git Bash Here"

### Passo 2: Copie e cole:

```bash
chmod +x deploy.sh && ./deploy.sh
```

### Passo 3: Pressione Enter

Pronto!

---

## **OPÇÃO 3: Terminal Linux/Mac**

```bash
cd ~/caminho/para/cotacad
chmod +x deploy.sh
./deploy.sh
```

---

## ✅ Validação Depois

Se vir isto no final:

```
╔════════════════════════════════════════════════════════════╗
║           DEPLOY COMPLETO COM SUCESSO!                    ║
╚════════════════════════════════════════════════════════════╝
```

**Significa que funcionou!** 🎉

---

## 🌐 Teste Agora

Abra no navegador:

**Frontend:** https://solution-cota-cad.vercel.app

**Backend:** https://cotacad-solution.duckdns.org/health

Deve retornar: `{"status":"ok"}`

---

## 🎯 Próximo: Teste com DXF Real

1. Vá para: https://solution-cota-cad.vercel.app
2. Login: `test@solution.com` / `teste123`
3. Clique: "Novo Levantamento"
4. Upload um DXF real
5. Veja o **score de precisão aparecer automaticamente** ← Isso é o novo!

---

## 🆘 Se der erro

1. **"Permission denied":**
   ```powershell
   # PowerShell
   Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
   .\deploy.ps1
   ```

2. **"SSH: Connection timeout":**
   - Verificar internet
   - Tentar: `ping 72.61.6.119`

3. **"Authentication failed":**
   - Senha SSH: `mo(rwQR!C@n&-5nV`
   - Tentar manualmente:
   ```bash
   ssh root@72.61.6.119
   ```

4. **Outro erro?**
   - Ver: [COMO_USAR_DEPLOY.md](./COMO_USAR_DEPLOY.md)
   - Ver: [DEPLOY_COM_OBSESSAO.md](./DEPLOY_COM_OBSESSAO.md)

---

## ✨ Resumo

| Item | Status |
|------|--------|
| Frontend | ✅ Já online |
| Backend | ⏳ Precisa rodar deploy.ps1 |
| Documentação | ✅ Completa |
| Precision Obsession | ✅ Ativado |

**Um comando = Deploy em 5 minutos**

Vá! 🚀
