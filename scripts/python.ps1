# Prepara o Python portatil da pasta .\python (sem instalar nada no Windows).
# Uso: powershell -ExecutionPolicy Bypass -File scripts\python.ps1 [preparar|dependencias]
#   preparar      baixa o Python (se faltar) e instala as dependencias (se faltarem)
#   dependencias  reinstala as dependencias de backend\requirements.txt
param([ValidateSet("preparar", "dependencias")][string]$acao = "preparar")

$ErrorActionPreference = "Stop"
$raiz   = Split-Path -Parent $PSScriptRoot
$pasta  = Join-Path $raiz "python"
$exe    = Join-Path $pasta "python.exe"
$reqs   = Join-Path $raiz "backend\requirements.txt"
$versao = "3.13.17"

function Instalar-Python {
    # Pacote oficial "embeddable" do python.org: um Python completo que roda de uma pasta
    $url = "https://www.python.org/ftp/python/$versao/python-$versao-embed-amd64.zip"
    $zip = Join-Path $env:TEMP "python-$versao-embed-amd64.zip"
    Write-Host "Python portatil nao encontrado. Baixando Python $versao (~11 MB)..."
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $ProgressPreference = "SilentlyContinue"
    Invoke-WebRequest $url -OutFile $zip
    Expand-Archive $zip -DestinationPath $pasta -Force
    Remove-Item $zip -Force

    # Por padrao o Python "embeddable" ignora site-packages; liga para aceitar bibliotecas
    $pth = Get-ChildItem $pasta -Filter "python*._pth" | Select-Object -First 1
    $linhas = (Get-Content $pth.FullName) -replace "^#\s*import site", "import site"
    if ($linhas -notcontains "Lib\site-packages") { $linhas = @($linhas[0], "Lib\site-packages") + $linhas[1..($linhas.Count - 1)] }
    Set-Content $pth.FullName $linhas -Encoding ASCII

    Write-Host "Instalando o pip..."
    $ErrorActionPreference = "Continue"
    $getpip = Join-Path $env:TEMP "get-pip.py"
    Invoke-WebRequest "https://bootstrap.pypa.io/get-pip.py" -OutFile $getpip
    & $exe $getpip --no-warn-script-location --disable-pip-version-check
    if ($LASTEXITCODE -ne 0) { throw "Falha ao instalar o pip" }
    Remove-Item $getpip -Force
}

function Dependencias-Ok {
    $ErrorActionPreference = "Continue"  # erro aqui so significa "falta instalar"
    & $exe -c "import fastapi, sqlalchemy, pymysql, PIL, bcrypt, uvicorn" 2>$null
    return ($LASTEXITCODE -eq 0)
}

function Instalar-Dependencias {
    $ErrorActionPreference = "Continue"  # avisos do pip vao para stderr e nao sao erro
    Write-Host "Instalando as bibliotecas do back-end..."
    & $exe -m pip install -r $reqs --no-warn-script-location --disable-pip-version-check
    if ($LASTEXITCODE -ne 0) { throw "Falha ao instalar as dependencias" }
}

if (-not (Test-Path $exe)) { Instalar-Python }
if ($acao -eq "dependencias" -or -not (Dependencias-Ok)) { Instalar-Dependencias }
& $exe -c "import sys; print('Python portatil OK:', sys.version.split()[0])"
