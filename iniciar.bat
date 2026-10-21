@echo off
rem Inicia o AmparaPet: MySQL portatil + API. Nao precisa instalar nada no Windows.
rem Ctrl+C (ou fechar a janela) para so a API; o parar.bat desliga tudo.
title AmparaPet - API (feche esta janela ou use o parar.bat para desligar)
pushd "%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\preparar.ps1 || goto erro
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\python.ps1 preparar || goto erro
if not exist ".env" copy ".env.example" ".env" >nul
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\banco.ps1 iniciar || goto erro

echo.
echo  Interface de teste:  http://localhost:8000/teste/
echo  Documentacao da API: http://localhost:8000/docs
echo.
rem Abre o navegador alguns segundos depois, quando a API ja estiver no ar
if not defined AMPARAPET_SEM_NAVEGADOR start "" /b powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep 4; Start-Process 'http://localhost:8000/teste/'"

cd backend
"..\python\python.exe" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
popd
exit /b

:erro
echo.
echo  Nao foi possivel iniciar. Leia a mensagem acima.
pause
popd
exit /b 1
