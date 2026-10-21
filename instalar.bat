@echo off
rem Reinstala as bibliotecas Python (use depois de mudar backend\requirements.txt).
rem Nao e preciso rodar no dia a dia: o iniciar.bat ja confere tudo sozinho.
pushd "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\python.ps1 dependencias || (pause & popd & exit /b 1)
echo Instalacao concluida.
popd
