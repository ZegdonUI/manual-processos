@echo off
title Manual de Processos - compartilhando
cd /d "%~dp0"
chcp 65001 >nul
echo.
echo  Manual no ar. Envie um destes links para o time:
echo.
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do for /f "tokens=*" %%b in ("%%a") do echo    http://%%b:8080
echo.
echo  Quem abrir o link pode enviar, trocar e remover imagens.
echo  Removidas/trocadas ficam guardadas em img\_lixeira.
echo  Feche esta janela para parar de compartilhar.
echo.
python servidor.py 8080 --rede
pause
