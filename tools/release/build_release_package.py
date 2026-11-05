# -*- coding: utf-8 -*-

import os
import sys
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DIST_DIR = PROJECT_ROOT / "release" / "No_More_Heroes_2_Traducao_PTBR_Beta"
PAYLOAD_DIR = DIST_DIR / "traducao_arquivos"
SRC_TRANS = PROJECT_ROOT / "data" / "translated"

def copy_payload():
    print(f"[+] Preparando pasta de destino: {DIST_DIR}...")
    if PAYLOAD_DIR.exists():
        shutil.rmtree(PAYLOAD_DIR)
    PAYLOAD_DIR.mkdir(parents=True, exist_ok=True)

    targets = [
        "Demo",
        "Hide",
        "Movie",
        "PJFaxMes",
        "PJSimplMes",
        "PJTutorial",
        "STG"
    ]

    copied_count = 0
    total_bytes = 0

    for target in targets:
        src_path = SRC_TRANS / target
        if not src_path.exists():
            continue

        for p in src_path.rglob("*"):
            if p.is_file() and not any(part.startswith("_") for part in p.parts):
                if "PJTuto_ETC_" in str(p) or p.name.endswith(".bak"):
                    continue
                rel = p.relative_to(SRC_TRANS)
                dst = PAYLOAD_DIR / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, dst)
                copied_count += 1
                total_bytes += p.stat().st_size

    print(f"[+] {copied_count} arquivos copiados para o payload ({total_bytes / (1024*1024):.1f} MB).")

def create_readme():
    readme_path = DIST_DIR / "LEIA-ME.txt"
    content = """NO MORE HEROES 2: DESPERATE STRUGGLE - TRADUCAO PT-BR (BETA)

Versao Beta de testes da traducao em Portugues do Brasil para a versao de PC (Steam).

AVISO IMPORTANTE:
Esta versao esta em fase de testes abertos. E possivel encontrar falhas de formatacao, travamentos ou pequenas inconsistencias em algumas cutscenes ou missoes. Caso encontre qualquer erro ou crash, abra uma Issue no repositorio do GitHub informando o nome da missao ou a cena onde ocorreu.

CREDITOS:
- juniodevs (DoubleXXP): Traducao e engenharia reversa
- Vickz_Joga: Testes e validacao
- Timo654: Ferramenta No-More-RSL

COMO INSTALAR:
1. Feche o jogo caso ele esteja aberto.
2. De um duplo-clique no arquivo Instalar_Traducao.bat.
3. O instalador tentara localizar a pasta do jogo na Steam automaticamente. Caso seu jogo esteja instalado em outro lugar, digite ou arraste o caminho da pasta onde fica o nmh2.exe.
4. Escolha a opcao 1 para instalar.
   O instalador copia os arquivos necessarios e cria automaticamente uma pasta chamada .backup dentro da pasta do jogo com os arquivos originais em ingles.

COMO DESINSTALAR OU RESTAURAR O JOGO ORIGINAL:
1. Abra o arquivo Instalar_Traducao.bat novamente.
2. Escolha a opcao 2 (Restaurar jogo original).
   Ele copia de volta todos os arquivos salvos na pasta .backup, voltando o jogo ao estado original sem precisar baixar nada novamente na Steam.

CONTEUDO DESTA VERSAO:
- 75 cutscenes legendadas em Portugues Brasileiro.
- Dialogos de combate e tutoriais adaptados.
- Bicos CLT de Santa Destroy (minigames 8-bit).
- Texturas de combate traduzidas (FALHA, TEMPO ESGOTADO, VAI!, TEMPO FINAL).
- Legenda grafica da batalha contra Skelter Helter.
- Textura da folha de fax da UAA traduzida.
- Menus, opcoes e telas de salvamento no executavel.
- Fonte do jogo com acentos completos da lingua portuguesa.
"""
    readme_path.write_text(content, encoding="utf-8")
    print(f"[+] Criado {readme_path.name}")

def create_installer_bat():
    bat_path = DIST_DIR / "Instalar_Traducao.bat"
    content = """@echo off
chcp 65001 >nul
title No More Heroes 2 - Traducao PT-BR [Instalador Beta]
color 0B

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0installer.ps1"
if %errorlevel% neq 0 (
    echo.
    echo Pressione qualquer tecla para fechar...
    pause >nul
)
"""
    bat_path.write_text(content, encoding="utf-8")
    print(f"[+] Criado {bat_path.name}")

def copy_installer_scripts():
    ps1_src = PROJECT_ROOT / "installer.ps1"
    ps1_dst = DIST_DIR / "installer.ps1"
    shutil.copy2(ps1_src, ps1_dst)
    print(f"[+] Copiado {ps1_dst.name} para a pasta da release")

    patch_exe_src = PROJECT_ROOT / "tools" / "reinsertion" / "patch_exe.py"
    patch_exe_dst = DIST_DIR / "patch_exe.py"
    if patch_exe_src.exists():
        shutil.copy2(patch_exe_src, patch_exe_dst)
        print(f"[+] Copiado {patch_exe_dst.name} para a pasta da release")

def main():
    print("=" * 65)
    print("  CONSTRUINDO PACOTE BETA RELEASE (GITHUB)                       ")
    print("=" * 65 + "\n")

    copy_payload()
    create_readme()
    create_installer_bat()
    copy_installer_scripts()

    print("\n[OK] Estrutura da release beta preparada com sucesso em:")
    print(f"     {DIST_DIR}\n")

if __name__ == "__main__":
    main()
