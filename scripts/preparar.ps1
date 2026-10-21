# Checagens feitas pelo iniciar.bat antes de subir o sistema.
# Uso: powershell -ExecutionPolicy Bypass -File scripts\preparar.ps1
$ErrorActionPreference = "Stop"
$raiz = Split-Path -Parent $PSScriptRoot

# 1. Windows 64 bits (MySQL e Python portateis sao x64; Windows ARM roda por emulacao)
if (-not [Environment]::Is64BitOperatingSystem) {
    Write-Host "Este sistema precisa de Windows 64 bits." -ForegroundColor Red; exit 1
}

# 2. Caminho da pasta: o Windows limita caminhos a 260 caracteres e o arquivo mais
#    fundo do projeto tem ~110 a partir da raiz
if ($raiz.Length -gt 140) {
    Write-Host "O caminho da pasta e muito longo ($($raiz.Length) caracteres):" -ForegroundColor Red
    Write-Host "  $raiz"
    Write-Host "Mova a pasta AMPARAPET para um lugar mais curto, ex.: C:\AMPARAPET ou Documentos."
    exit 1
}

# 3. Pasta extraida de um ZIP baixado da internet: o Windows marca os arquivos como
#    "bloqueados" e pode travar os programas pedindo confirmacao. Desbloqueia tudo.
foreach ($sub in "python", "mysql\server", "scripts") {
    $p = Join-Path $raiz $sub
    if (Test-Path $p) { Get-ChildItem $p -Recurse -File | Unblock-File }
}
Get-ChildItem $raiz -File -Filter *.bat | Unblock-File

# 4. Porta da API livre?
$conexao = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
if ($conexao) {
    $proc = Get-CimInstance Win32_Process -Filter "ProcessId = $($conexao.OwningProcess)"
    $nossa = Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" | Where-Object { $_.CommandLine -like "*app.main:app*" }
    if ($nossa) {
        Write-Host "A API ja esta rodando (talvez em outra janela). Abra http://localhost:8000/teste/" -ForegroundColor Yellow
        Write-Host "Para reiniciar, rode o parar.bat e depois o iniciar.bat."
    } else {
        Write-Host "A porta 8000 esta sendo usada por outro programa: $($proc.Name)" -ForegroundColor Red
        Write-Host "Feche esse programa e rode o iniciar.bat de novo."
    }
    exit 1
}
