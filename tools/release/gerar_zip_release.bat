@echo off
chcp 65001 >nul
title Gerar Pacote ZIP de Release
python "%~dp0gerar_zip_release.py"
echo.
pause
