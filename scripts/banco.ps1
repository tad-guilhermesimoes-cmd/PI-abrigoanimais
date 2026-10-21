# Controla a instância portátil do MySQL que fica em .\mysql
# Uso: powershell -ExecutionPolicy Bypass -File scripts\banco.ps1 iniciar|parar|status|console
param([ValidateSet("iniciar", "parar", "status", "console")][string]$acao = "status")

$ErrorActionPreference = "Stop"
$raiz    = Split-Path -Parent $PSScriptRoot
$mysql   = Join-Path $raiz "mysql"
$server  = Join-Path $mysql "server"
$dados   = Join-Path $mysql "data"
$ini     = Join-Path $mysql "my.ini"
$porta   = 3307
$bin     = Join-Path $server "bin"

$versao  = "8.4.13"

function Baixar-MySQL {
    # Baixa o ZIP oficial (sem instalador) e remove os simbolos de debug (~800 MB a menos)
    $url = "https://cdn.mysql.com/Downloads/MySQL-8.4/mysql-$versao-winx64.zip"
    $zip = Join-Path $env:TEMP "mysql-$versao-winx64.zip"
    Write-Host "MySQL portatil nao encontrado. Baixando MySQL $versao (~270 MB)..."
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $ProgressPreference = "SilentlyContinue"
    Invoke-WebRequest $url -OutFile $zip
    $md5 = (Invoke-WebRequest "$url.md5" -UseBasicParsing).Content.ToString().Split(" ")[0].Trim()
    if ((Get-FileHash $zip -Algorithm MD5).Hash -ne $md5.ToUpper()) { throw "Download corrompido, tente de novo." }
    Write-Host "Extraindo..."
    $tmp = Join-Path $mysql "_extraindo"
    Expand-Archive $zip -DestinationPath $tmp -Force
    Move-Item (Join-Path $tmp "mysql-$versao-winx64") $server
    Remove-Item $tmp, $zip -Recurse -Force
    Get-ChildItem $server -Recurse -Include *.pdb, *.lib | Remove-Item -Force
    Remove-Item (Join-Path $server "lib\plugin\debug") -Recurse -Force -ErrorAction SilentlyContinue
}

if (-not (Test-Path (Join-Path $bin "mysqld.exe"))) {
    New-Item -ItemType Directory -Force $mysql | Out-Null
    Baixar-MySQL
}

# O mysqld precisa das bibliotecas do Visual C++. A pasta ja traz uma copia delas em bin\
# (permitido pela Microsoft); se faltarem la e no Windows, o MySQL nao abre.
foreach ($dll in "msvcp140.dll", "vcruntime140.dll", "vcruntime140_1.dll") {
    if (-not (Test-Path (Join-Path $bin $dll))) {
        $doSistema = Join-Path $env:SystemRoot "System32\$dll"
        if (Test-Path $doSistema) { Copy-Item $doSistema $bin }
        else {
            Write-Host "Falta $dll (Visual C++ Redistributable)." -ForegroundColor Red
            Write-Host "Instale o 'Microsoft Visual C++ Redistributable x64' (gratuito) e tente de novo:"
            Write-Host "  https://aka.ms/vs/17/release/vc_redist.x64.exe"
            exit 1
        }
    }
}

function Escrever-Ini {
    # Os caminhos absolutos sao gerados a cada execucao, entao a pasta pode ser movida.
    $b = $server.Replace("\", "/"); $d = $dados.Replace("\", "/"); $m = $mysql.Replace("\", "/")
    $conteudo = @"
[mysqld]
basedir=$b
datadir=$d
port=$porta
bind-address=127.0.0.1
mysqlx=OFF
character-set-server=utf8mb4
collation-server=utf8mb4_0900_ai_ci
log-error=$m/mysql.log
max_allowed_packet=16M

[client]
host=127.0.0.1
port=$porta
default-character-set=utf8mb4
"@
    # O mysqld do Windows le o my.ini na codificacao ANSI do sistema (nao UTF-8).
    # Gravar em ANSI faz caminhos com acento (ex.: "Documentos\Ação") funcionarem.
    [IO.File]::WriteAllText($ini, $conteudo, [Text.Encoding]::Default)
}

function Esta-Rodando {
    # Tentativa curta (300 ms): com a porta fechada, o Connect normal demora ~2 s
    $c = New-Object Net.Sockets.TcpClient
    try {
        $ok = $c.BeginConnect("127.0.0.1", $porta, $null, $null).AsyncWaitHandle.WaitOne(300)
        return ($ok -and $c.Connected)
    } catch { return $false } finally { $c.Close() }
}

function Sql([string]$comando) {
    & (Join-Path $bin "mysql.exe") "--defaults-file=$ini" -uroot -e $comando
    if ($LASTEXITCODE -ne 0) { throw "Falha ao executar SQL: $comando" }
}

switch ($acao) {
    "iniciar" {
        if (Esta-Rodando) { Write-Host "MySQL ja esta rodando na porta $porta."; break }
        Escrever-Ini
        $primeiraVez = -not (Test-Path $dados)
        if ($primeiraVez) {
            Write-Host "Inicializando o banco pela primeira vez..."
            & (Join-Path $bin "mysqld.exe") "--defaults-file=$ini" --initialize-insecure
            if ($LASTEXITCODE -ne 0) { Write-Host "Erro ao inicializar. Veja mysql\mysql.log" -ForegroundColor Red; exit 1 }
        }
        Start-Process -FilePath (Join-Path $bin "mysqld.exe") -ArgumentList "--defaults-file=`"$ini`"" -WindowStyle Hidden
        for ($i = 0; $i -lt 60 -and -not (Esta-Rodando); $i++) { Start-Sleep -Milliseconds 500 }
        if (-not (Esta-Rodando)) { Write-Host "MySQL nao subiu. Veja mysql\mysql.log" -ForegroundColor Red; exit 1 }
        if ($primeiraVez) {
            Write-Host "Criando bancos 'amparapet' e 'amparapet_teste' e o usuario 'amparapet'..."
            Sql "CREATE DATABASE IF NOT EXISTS amparapet CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
                 CREATE DATABASE IF NOT EXISTS amparapet_teste CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
                 CREATE USER IF NOT EXISTS 'amparapet'@'localhost' IDENTIFIED BY 'amparapet';
                 CREATE USER IF NOT EXISTS 'amparapet'@'127.0.0.1' IDENTIFIED BY 'amparapet';
                 GRANT ALL ON amparapet.* TO 'amparapet'@'localhost';
                 GRANT ALL ON amparapet.* TO 'amparapet'@'127.0.0.1';
                 GRANT ALL ON amparapet_teste.* TO 'amparapet'@'localhost';
                 GRANT ALL ON amparapet_teste.* TO 'amparapet'@'127.0.0.1';
                 FLUSH PRIVILEGES;"
        }
        Write-Host "MySQL rodando em 127.0.0.1:$porta" -ForegroundColor Green
    }
    "parar" {
        if (-not (Esta-Rodando)) { Write-Host "MySQL nao esta rodando."; break }
        Escrever-Ini
        & (Join-Path $bin "mysqladmin.exe") "--defaults-file=$ini" -uroot shutdown
        Write-Host "MySQL parado."
    }
    "status" {
        if (Esta-Rodando) { Write-Host "MySQL rodando na porta $porta." } else { Write-Host "MySQL parado." }
    }
    "console" {
        Escrever-Ini
        & (Join-Path $bin "mysql.exe") "--defaults-file=$ini" -uamparapet -pamparapet amparapet
    }
}
