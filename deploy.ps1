# QuanttunAI Deploy Script — PowerShell (Windows)
# Executa: git pull -> docker rebuild -> validação

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     QUANTTUNAI DEPLOY — Precision Obsession Edition       ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

$host_ip = "72.61.6.119"
$user = "root"
$remote_path = "/opt/cotacad"

Write-Host "[1/6] Preparando SSH..." -ForegroundColor Blue
Write-Host "Host: $host_ip"
Write-Host "User: $user"
Write-Host ""

# Criar comando completo
$ssh_commands = @"
cd $remote_path
echo '=== GIT PULL ==='
git pull origin main
echo ''
echo '=== DOCKER DOWN ==='
docker-compose -f backend/docker-compose.yml down
echo ''
echo '=== DOCKER BUILD & UP ==='
docker-compose -f backend/docker-compose.yml up -d --build
echo ''
echo '=== AGUARDANDO 30 SEGUNDOS ==='
sleep 30
echo ''
echo '=== STATUS DOS CONTAINERS ==='
docker ps | grep cotacad
echo ''
echo '=== HEALTH CHECK ==='
curl -s http://localhost:8000/health
echo ''
echo '=== LOGS (ULTIMAS 30 LINHAS) ==='
docker-compose -f backend/docker-compose.yml logs api | tail -30
"@

try {
    Write-Host "[2/6] Conectando via SSH..." -ForegroundColor Green

    # Executar comandos via SSH
    $output = ssh $user@$host_ip $ssh_commands

    Write-Host ""
    Write-Host "=== OUTPUT DO SERVIDOR ===" -ForegroundColor Blue
    Write-Host $output

    Write-Host ""
    Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║           DEPLOY COMPLETO COM SUCESSO!                    ║" -ForegroundColor Green
    Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Green
    Write-Host ""

    Write-Host "Proximos passos:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "1. Acesse o frontend:" -ForegroundColor White
    Write-Host "   https://solution-cota-cad.vercel.app" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "2. Teste o backend:" -ForegroundColor White
    Write-Host "   curl https://cotacad-solution.duckdns.org/health" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "3. Faça login e upload um DXF:" -ForegroundColor White
    Write-Host "   email: test@solution.com" -ForegroundColor Yellow
    Write-Host "   senha: teste123" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "4. Veja o score de precisao aparecer automaticamente!" -ForegroundColor Magenta
    Write-Host ""

} catch {
    Write-Host ""
    Write-Host "[ERRO] Deploy falhou:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "Dicas:" -ForegroundColor Yellow
    Write-Host "- Verificar senha SSH: mo(rwQR!C@n&-5nV" -ForegroundColor Gray
    Write-Host "- Verificar conexão: ssh $user@$host_ip 'echo OK'" -ForegroundColor Gray
    Write-Host ""
    exit 1
}
