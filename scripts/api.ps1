# Desliga a API do AmparaPet (uvicorn), se estiver rodando.
# Uso: powershell -ExecutionPolicy Bypass -File scripts\api.ps1 parar
param([ValidateSet("parar", "status")][string]$acao = "status")

# Processos Python rodando "app.main:app" (o uvicorn e, com --reload, o processo vigia)
$processos = Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" |
    Where-Object { $_.CommandLine -like "*app.main:app*" }

if (-not $processos) { Write-Host "API nao esta rodando."; exit 0 }

if ($acao -eq "status") { Write-Host "API rodando em http://localhost:8000"; exit 0 }

foreach ($p in $processos) {
    # /T derruba tambem os processos filhos (o servidor de verdade, quando usa --reload)
    & taskkill.exe /PID $p.ProcessId /T /F 2>&1 | Out-Null
}
Write-Host "API parada."
