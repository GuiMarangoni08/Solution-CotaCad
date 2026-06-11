#!/bin/bash
# QuanttunAI Deploy Script — Interativo
# Funciona em: Git Bash (Windows), Linux, macOS

set -e

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║     QUANTTUNAI DEPLOY — Precision Obsession Edition       ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuração
HOST="72.61.6.119"
USER="root"
REMOTE_PATH="/opt/cotacad"

echo -e "${BLUE}[1/6]${NC} Verificando conexão SSH..."
echo "Host: $HOST"
echo "User: $USER"
echo ""

# Verificar se consegue fazer SSH
if ! ssh -o ConnectTimeout=5 -o BatchMode=yes $USER@$HOST "echo 'SSH OK'" &>/dev/null; then
    echo -e "${YELLOW}[!] SSH com autenticação de chave não funciona.${NC}"
    echo "    Usaremos SSH com prompt de senha."
    echo ""
    read -p "Pressione Enter para continuar (será pedida a senha)..."
fi

echo -e "${GREEN}[2/6]${NC} Fazendo git pull no VPS..."
ssh $USER@$HOST "cd $REMOTE_PATH && git pull origin main" || {
    echo -e "${RED}[!] Git pull falhou${NC}"
    exit 1
}

echo ""
echo -e "${GREEN}[3/6]${NC} Parando containers antigos..."
ssh $USER@$HOST "cd $REMOTE_PATH && docker-compose -f backend/docker-compose.yml down" || {
    echo -e "${YELLOW}[!] Down teve erro (pode ser normal se containers não existem)${NC}"
}

echo ""
echo -e "${GREEN}[4/6]${NC} Buildando e iniciando containers..."
ssh $USER@$HOST "cd $REMOTE_PATH && docker-compose -f backend/docker-compose.yml up -d --build" || {
    echo -e "${RED}[!] Build falhou${NC}"
    exit 1
}

echo ""
echo -e "${BLUE}[5/6]${NC} Aguardando containers iniciarem (30 segundos)..."
ssh $USER@$HOST "sleep 30" || true

echo ""
echo -e "${GREEN}[6/6]${NC} Validando deployment..."
echo ""

# Health check
HEALTH=$(ssh $USER@$HOST "curl -s http://localhost:8000/health" 2>/dev/null || echo "ERRO")

if [ "$HEALTH" == '{"status":"ok"}' ]; then
    echo -e "${GREEN}✓ Backend health check: OK${NC}"
else
    echo -e "${YELLOW}⚠ Health check respondeu: $HEALTH${NC}"
fi

echo ""
echo -e "${BLUE}=== LOGS (últimas 20 linhas) ===${NC}"
ssh $USER@$HOST "cd $REMOTE_PATH && docker-compose -f backend/docker-compose.yml logs api | tail -20" || true

echo ""
echo -e "${BLUE}=== DOCKER STATUS ===${NC}"
ssh $USER@$HOST "cd $REMOTE_PATH && docker ps | grep cotacad" || true

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo -e "${GREEN}║           DEPLOY COMPLETO COM SUCESSO!                 ║${NC}"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Próximos passos:"
echo "1. Acesse o frontend:"
echo "   https://solution-cota-cad.vercel.app"
echo ""
echo "2. Teste o backend:"
echo "   curl https://cotacad-solution.duckdns.org/health"
echo ""
echo "3. Faça login e upload um DXF:"
echo "   email: test@solution.com"
echo "   senha: teste123"
echo ""
echo "4. Veja o score de precisão aparecer automaticamente!"
echo ""
