@echo off
rem Roda os testes automatizados (usa o banco amparapet_teste, que e apagado e recriado).
pushd "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\python.ps1 preparar || (pause & popd & exit /b 1)
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\banco.ps1 iniciar || (pause & popd & exit /b 1)
cd backend
"..\python\python.exe" -m pytest -q %*
popd
