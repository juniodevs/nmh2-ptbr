# -*- coding: utf-8 -*-

import os
import sys
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DIST_DIR = PROJECT_ROOT / "release" / "No_More_Heroes_2_Traducao_PTBR_Beta"
PAYLOAD_DIR = DIST_DIR / "traducao_arquivos"
UPDATE_DIR = PROJECT_ROOT / "release" / "No_More_Heroes_2_Traducao_PTBR_Update"
SRC_TRANS = PROJECT_ROOT / "data" / "translated"

def copy_payload():
    print(f"[+] Preparando pasta de destino completa: {DIST_DIR}...")
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

    print(f"[+] {copied_count} arquivos copiados para o payload completo ({total_bytes / (1024*1024):.1f} MB).")

def create_readme(dest_dir: Path):
    readme_path = dest_dir / "LEIA-ME.txt"
    content = """NO MORE HEROES 2: DESPERATE STRUGGLE - TRADUCAO PT-BR (BETA v1.0.3)

Versao Beta de testes da traducao em Portugues do Brasil para a versao de PC (Steam).

AVISO:
Esta versao esta em fase de testes abertos. E possivel encontrar falhas pontuais, travamentos ou pequenas inconsistencias em algumas cenas. Caso encontre qualquer erro ou crash, abra uma Issue no repositorio do GitHub informando o nome da missao ou o momento exato em que ocorreu.

CREDITOS:
- juniodevs: traducao e engenharia reversa (https://junio.is-a.dev/)
- Vickz_Joga: testes e validacao em gameplay (https://www.youtube.com/@Vickz_Joga)
- Timo654: ferramenta No-More-RSL

NOVIDADES DA VERSAO BETA v1.0.3:
- Baloes de interacao do Motel traduzidos em pixel-art autentico: TELEVISAO, ESTANTE, ARMARIO, BANHEIRO e SAIR (texturas DDS nativas em BALLOON_TEXTURE/US dentro de STG3001.bin).
- Interface completa da tela de salvamento (Privada / Banheiro) e carregamento traduzida diretamente no nmh2.exe: SALVAR, CARREGAR, SALVANDO..., VAZIO, SLOT.01, SLOT.02..., SALVAR?, CARREGAR?.
- Academia do Ryan (STG3004): corrigido em definitivo o travamento/softlock que deixava o Ryan sem HUD apos perder o minigame, restaurando a fonte nativa Ninepin Bold e alinhando os dados a 16 bytes.
- Minigame de canos ajustado para "LIMPA-BOSTA", sem estouro visual de texto na tela.
- Boss 2 (Nathan Copeland): crash ao derrotar o chefe resolvido atraves da restauracao do grapple Jacob's Ladder.
- Pacote leve de update otimizado (~75 MB) com atualizacao automatica via Atualizar_Traducao.bat.

DESTAQUES DA VERSAO BETA GERAL:
- Nova fonte retro VCR OSD Mono calibrada pixel a pixel, combinando com a estetica do jogo.
- Alinhamento vertical fixo na linha de base, evitando que acentos empurrem a legenda para baixo.
- Correcao dos caracteres corrompidos em letras maiusculas (como C e L).
- Traducao completa do motel do Travis (armario, revistas de wrestling, minigame da Jeane, baloes e TV).
- Traducao das lojas e instalacoes de Santa Destroy (Airport 51, Laboratorio da Naomi e Academia do Ryan).
- Menus e prompts de interacao traduzidos diretamente no executavel nmh2.exe (Trocar, Comprar, Estante, Revistas, Brincar, Escolher, Girar).

COMO INSTALAR (PRIMEIRA VEZ):
1. Feche o jogo caso ele esteja aberto.
2. De um duplo-clique no arquivo Instalar_Traducao.bat.
3. O instalador tentara localizar a pasta do jogo na Steam automaticamente. Caso seu jogo esteja instalado em outro lugar, digite ou arraste o caminho da pasta onde fica o nmh2.exe.
4. Escolha a opcao 1 para instalar.
   O instalador cria automaticamente uma pasta chamada .backup dentro da pasta do jogo com os arquivos originais em ingles.

COMO ATUALIZAR CASO JA TENHA UMA VERSAO ANTERIOR:
1. De um duplo-clique no arquivo Atualizar_Traducao.bat.
2. O script consulta o GitHub e atualiza apenas os arquivos necessarios em poucos segundos.

COMO DESINSTALAR OU RESTAURAR O JOGO ORIGINAL:
1. Abra o arquivo Instalar_Traducao.bat novamente.
2. Escolha a opcao 2 (Restaurar jogo original).
   Ele copia de volta todos os arquivos salvos na pasta .backup, voltando o jogo ao estado original sem precisar baixar nada novamente na Steam.
"""
    readme_path.write_text(content, encoding="utf-8")
    print(f"[+] Criado {readme_path.name} em {dest_dir.name}")

def create_bats_and_scripts(dest_dir: Path):
    bat_install = dest_dir / "Instalar_Traducao.bat"
    bat_install.write_text("""@echo off
chcp 65001 >nul
title No More Heroes 2 - Traducao PT-BR [Instalador Beta]
color 0B

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0installer.ps1"
if %errorlevel% neq 0 (
    echo.
    echo Pressione qualquer tecla para fechar...
    pause >nul
)
""", encoding="utf-8")

    bat_update = dest_dir / "Atualizar_Traducao.bat"
    bat_update.write_text("""@echo off
chcp 65001 >nul
title No More Heroes 2 - Traducao PT-BR [Atualizador]
color 0A

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0updater.ps1"
if %errorlevel% neq 0 (
    echo.
    echo Pressione qualquer tecla para fechar...
    pause >nul
)
""", encoding="utf-8")

    for f_name in ["installer.ps1", "updater.ps1", "version.txt"]:
        src = PROJECT_ROOT / f_name
        if src.exists():
            shutil.copy2(src, dest_dir / f_name)

    patch_exe = PROJECT_ROOT / "tools" / "reinsertion" / "patch_exe.py"
    if patch_exe.exists():
        shutil.copy2(patch_exe, dest_dir / "patch_exe.py")

def build_update_package():
    print(f"\n[+] Preparando pacote leve de UPDATE em: {UPDATE_DIR}...")
    if UPDATE_DIR.exists():
        shutil.rmtree(UPDATE_DIR)
    UPDATE_DIR.mkdir(parents=True, exist_ok=True)

    up_payload = UPDATE_DIR / "traducao_arquivos"
    up_payload.mkdir(parents=True, exist_ok=True)

    # Arquivos atualizados nesta versao
    updated_files = [
        "STG/STG3000/STG3000.bin",
        "STG/STG3001/STG3001.bin",
        "STG/STG3003/STG3003.bin",
        "STG/STG3004/STG3004.bin",
        "STG/STG7000/STG7000.bin",
        "Hide/RankingUp/ResultEE.RSL",
        "Hide/RankingUp/FaildEE.RSL",
        "Hide/RankingUp/sm_startEE.RSL",
    ]

    total_bytes = 0
    for rel in updated_files:
        src = SRC_TRANS / rel
        dst = up_payload / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        total_bytes += src.stat().st_size

    create_readme(UPDATE_DIR)
    create_bats_and_scripts(UPDATE_DIR)

    print(f"[+] Pacote de UPDATE montado: {len(updated_files)} fases modificadas ({total_bytes / (1024*1024):.1f} MB).")

def main():
    print("=" * 65)
    print("  CONSTRUINDO PACOTES DE RELEASE E UPDATE (GITHUB)               ")
    print("=" * 65 + "\n")

    # 1. Pacote completo
    copy_payload()
    create_readme(DIST_DIR)
    create_bats_and_scripts(DIST_DIR)

    # 2. Pacote leve de update
    build_update_package()

    print("\n[OK] Pacotes preparados com sucesso:")
    print(f"     Completo: {DIST_DIR}")
    print(f"     Update:   {UPDATE_DIR}\n")

if __name__ == "__main__":
    main()
