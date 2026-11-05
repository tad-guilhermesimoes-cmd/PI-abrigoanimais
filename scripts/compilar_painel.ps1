# Compila o painel de controle (scripts\painel\Painel.cs) e gera o AmparaPet.exe na raiz do projeto.
# Usa o compilador C# que ja vem no Windows (.NET Framework 4.x); nao precisa instalar nada.
# Uso: powershell -ExecutionPolicy Bypass -File scripts\compilar_painel.ps1
$ErrorActionPreference = "Stop"
$raiz  = Split-Path -Parent $PSScriptRoot
$fonte = Join-Path $PSScriptRoot "painel\Painel.cs"
$icone = Join-Path $PSScriptRoot "painel\amparapet.ico"
$saida = Join-Path $raiz "AmparaPet.exe"
$csc   = Join-Path $env:WINDIR "Microsoft.NET\Framework64\v4.0.30319\csc.exe"
if (-not (Test-Path $csc)) { $csc = Join-Path $env:WINDIR "Microsoft.NET\Framework\v4.0.30319\csc.exe" }
if (-not (Test-Path $csc)) { Write-Host "Compilador C# do .NET Framework 4 nao encontrado." -ForegroundColor Red; exit 1 }

if (-not (Test-Path $icone)) {
    & (Join-Path $raiz "python\python.exe") (Join-Path $PSScriptRoot "painel\gerar_icone.py") $icone
}

$ErrorActionPreference = "Continue"
& $csc /nologo /target:winexe /optimize+ /platform:anycpu "/out:$saida" "/win32icon:$icone" `
    /reference:System.Windows.Forms.dll /reference:System.Drawing.dll $fonte
if ($LASTEXITCODE -ne 0) { Write-Host "Falha ao compilar o painel." -ForegroundColor Red; exit 1 }
Write-Host "Painel gerado: $saida" -ForegroundColor Green
