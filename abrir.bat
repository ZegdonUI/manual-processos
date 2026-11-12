@echo off
title Manual de Processos - so neste PC
cd /d "%~dp0"
chcp 65001 >nul
start "" /min cmd /c "timeout /t 2 >nul & start http://localhost:8080"
echo.
echo  Manual em http://localhost:8080 (so neste PC).
echo  Se o compartilhar.bat ja estiver aberto, o navegador usa ele e esta janela pode ser fechada.
echo.
python servidor.py 8080
pause
