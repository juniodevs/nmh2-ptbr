@echo off
chcp 65001 >nul
title No More Heroes 2 - Traducao PT-BR [Instalador Beta]
color 0B

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0installer.ps1"
if %errorlevel% neq 0 (
    echo.
    echo Pressione qualquer tecla para fechar...
    pause >nul
)
