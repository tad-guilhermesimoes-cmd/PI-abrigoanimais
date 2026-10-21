@echo off
rem Desliga a API do AmparaPet e o MySQL portatil.
pushd "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\api.ps1 parar
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\banco.ps1 parar
popd
