# -*- coding: utf-8 -*-

import os
import sys
import json
import shutil
import struct
import argparse
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools.extraction.ghm_lz import decompress_ghm_lz, compress_ghm_lz
from tools.utilities.gdl_tool import rebuild_gdl, parse_gdl
from tools.utilities.patch_strimag import create_extended_strimag


def is_ghm_lz(data: bytes) -> bool:
    if len(data) < 9:
        return False
    uncomp_sz, comp_sz = struct.unpack('<II', data[:8])
    return comp_sz == len(data) and uncomp_sz > comp_sz


def repack_archive(archive_rel_path: str, game_dir: Path, install: bool = False):
    backup_file = PROJECT_ROOT / "backups" / f"{archive_rel_path}.bak"
    if not backup_file.exists():
        backup_file = PROJECT_ROOT / "backups" / archive_rel_path

    if backup_file.exists() and backup_file.stat().st_size == 6636392:
        src_file = backup_file
        print(f"[+] Usando arquivo original preservado do backup: {src_file.name}")
    elif backup_file.exists():
        src_file = backup_file
        print(f"[+] Usando backup existente: {src_file.name}")
    else:
        src_file = game_dir / archive_rel_path

    if not src_file.exists():
        raise FileNotFoundError(f"Arquivo de origem não encontrado: {src_file}")

    temp_dir = PROJECT_ROOT / "data" / "translated" / "_temp_repack"
    temp_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n[+] Iniciando reempacotamento de: {archive_rel_path}")
    with open(src_file, 'rb') as f:
        data = f.read()

    was_compressed = is_ghm_lz(data)
    if was_compressed:
        print("    Arquivo compactado detectado (ghmGcLz). Descompactando para RMHG...")
        rsl_data = decompress_ghm_lz(data)
    else:
        rsl_data = data

    temp_rsl = temp_dir / f"{src_file.stem}.RSL"
    with open(temp_rsl, 'wb') as f:
        f.write(rsl_data)

    unpack_dir = temp_dir / src_file.stem
    if unpack_dir.exists():
        shutil.rmtree(unpack_dir)

    rsl_extract = PROJECT_ROOT / "tools" / "external" / "No-More-RSL" / "rslExtract.py"
    subprocess.run([sys.executable, str(rsl_extract), str(temp_rsl)], check=True, stdout=subprocess.DEVNULL)

    gdl_files = list(unpack_dir.rglob("*.GDL"))
    modified_count = 0

    for gdl in gdl_files:
        matches = list((PROJECT_ROOT / "translation" / "pt-BR").rglob(f"{gdl.stem}.json"))
        if not matches:
            continue

        trans_json_path = matches[0]
        with open(trans_json_path, 'r', encoding='utf-8') as f:
            trans_items = json.load(f)

        with open(gdl, 'rb') as f:
            orig_gdl_data = f.read()

        orig_strings = parse_gdl(orig_gdl_data)
        new_strings = []
        has_changes = False

        for item in trans_items:
            idx = item["id"]
            trans_text = item.get("translation", "").strip()
            if not trans_text and "text" in item:
                trans_text = item["text"].strip()

            if trans_text:
                new_strings.append(trans_text)
                has_changes = True
            else:
                new_strings.append(item.get("original", orig_strings[idx] if idx < len(orig_strings) else ""))

        if has_changes:
            print(f"    [->] Injetando {len(new_strings)} strings em: {gdl.name}")
            rebuilt_gdl = rebuild_gdl(orig_gdl_data, new_strings)
            with open(gdl, 'wb') as f:
                f.write(rebuilt_gdl)
            modified_count += 1

            gc_file = gdl.parent / f"{gdl.stem}_GC.BIN"
            if gc_file.exists():
                stem_base = gdl.stem[:-2] if len(gdl.stem) > 2 else gdl.stem
                es_matches = list(unpack_dir.rglob(f"*{stem_base}ES_GC.BIN"))
                fr_matches = list(unpack_dir.rglob(f"*{stem_base}EF_GC.BIN"))
                if es_matches and fr_matches:
                    try:
                        with open(gc_file, 'rb') as f1, open(es_matches[0], 'rb') as f2, open(fr_matches[0], 'rb') as f3:
                            patched_gc = create_extended_strimag(
                                f1.read(), f2.read(), f3.read(), set(''.join(new_strings))
                            )
                        with open(gc_file, 'wb') as f_out:
                            f_out.write(patched_gc)
                        print(f"    [->] Glifos estendidos STRIMAG2 injetados em: {gc_file.name}")
                    except Exception as e:
                        print(f"    [!] Erro ao injetar glifos em {gc_file.name}: {e}")

    if modified_count == 0:
        print("    [!] Nenhuma string traduzida encontrada para este arquivo. Operação abortada.")
        shutil.rmtree(unpack_dir, ignore_errors=True)
        temp_rsl.unlink(missing_ok=True)
        return

    print("    Reempacotando contêiner RMHG...")
    rsl_pack = PROJECT_ROOT / "tools" / "external" / "No-More-RSL" / "rslPack.py"
    subprocess.run([sys.executable, str(rsl_pack), str(unpack_dir), "--overwrite"], check=True, stdout=subprocess.DEVNULL)

    repacked_rsl = temp_dir / f"{src_file.stem}.rsl"
    if not repacked_rsl.exists():
        repacked_rsl = temp_dir / f"{src_file.stem}.RSL"

    with open(repacked_rsl, 'rb') as f:
        repacked_data = f.read()

    out_dir = PROJECT_ROOT / "data" / "translated" / Path(archive_rel_path).parent
    out_dir.mkdir(parents=True, exist_ok=True)
    archive_name = Path(archive_rel_path).name
    final_output = out_dir / archive_name

    if was_compressed:
        print(f"    Recompactando com ghmGcLz ({len(repacked_data)} bytes)...")
        comp_data = compress_ghm_lz(repacked_data)
        with open(final_output, 'wb') as f:
            f.write(comp_data)
        ratio = len(comp_data) / len(repacked_data) * 100
        print(f"    Arquivo final pronto: {final_output} ({len(comp_data)} bytes, {ratio:.1f}%)")
    else:
        with open(final_output, 'wb') as f:
            f.write(repacked_data)
        print(f"    Arquivo final pronto: {final_output} ({len(repacked_data)} bytes)")

    shutil.rmtree(unpack_dir, ignore_errors=True)
    if temp_rsl.exists(): temp_rsl.unlink()
    if repacked_rsl.exists(): repacked_rsl.unlink()

    if install:
        dest_game_file = game_dir / archive_rel_path
        permanent_backup = PROJECT_ROOT / "backups" / f"{archive_rel_path}.bak"
        permanent_backup.parent.mkdir(parents=True, exist_ok=True)
        if not permanent_backup.exists() and dest_game_file.exists():
            shutil.copy2(dest_game_file, permanent_backup)
            print(f"    [Backup] Salvo backup original em: {permanent_backup}")
        shutil.copy2(final_output, dest_game_file)
        print(f"    [Instalação] Arquivo traduzido copiado com sucesso para a Steam:\n      -> {dest_game_file}")


def main():
    parser = argparse.ArgumentParser(description="Reinserção e reempacotamento de arquivos traduzidos de NMH2")
    parser.add_argument("archive", help="Caminho relativo do arquivo no jogo (ex: 'PJTutorial/PJTuto_ETC.RSL' ou 'Demo/P0100.BIN')")
    parser.add_argument("--game-dir", "-g", default=r"E:\SteamLibrary\steamapps\common\No More Heroes 2 Desperate Struggle",
                        help="Diretório de instalação do jogo")
    parser.add_argument("--install", "-i", action="store_true",
                        help="Cria backup e instala diretamente na pasta da Steam para teste imediato")
    args = parser.parse_args()

    repack_archive(args.archive, Path(args.game_dir), install=args.install)


if __name__ == "__main__":
    main()
