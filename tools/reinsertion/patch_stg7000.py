# -*- coding: utf-8 -*-

import os
import sys
import json
import shutil
import struct
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools.extraction.ghm_lz import decompress_ghm_lz, compress_ghm_lz
from tools.utilities.gdl_tool import rebuild_gdl, parse_gdl
from tools.utilities.patch_strimag import create_extended_strimag

def patch_stg7000(game_dir: Path):
    stg_bin = game_dir / "STG" / "STG7000" / "STG7000.bin"
    backup_file = PROJECT_ROOT / "backups" / "STG" / "STG7000.bin.bak"
    backup_file.parent.mkdir(parents=True, exist_ok=True)

    if not backup_file.exists():
        print(f"[+] Criando backup original de {stg_bin.name}...")
        shutil.copy2(stg_bin, backup_file)
        src_bin = stg_bin
    else:
        print(f"[+] Usando backup preservado: {backup_file.name}")
        src_bin = backup_file

    temp_dir = PROJECT_ROOT / "data" / "translated" / "_temp_stg7000"
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)

    print("[+] Descompactando STG7000.bin (ghmGcLz)...")
    raw_data = src_bin.read_bytes()
    rsl_data = decompress_ghm_lz(raw_data)

    temp_rsl = temp_dir / "STG7000.RSL"
    temp_rsl.write_bytes(rsl_data)
    print(f"    RSL descompactado: {len(rsl_data)} bytes")

    print("[+] Extraindo contêiner STG7000.RSL...")
    rsl_extract = PROJECT_ROOT / "tools" / "external" / "No-More-RSL" / "rslExtract.py"
    subprocess.run([sys.executable, str(rsl_extract), str(temp_rsl)], check=True, stdout=subprocess.DEVNULL)

    unpack_dir = temp_dir / "STG7000"

    trans_json = PROJECT_ROOT / "translation" / "pt-BR" / "STG" / "STG7000" / "STG7000EE.json"
    with open(trans_json, "r", encoding="utf-8") as f:
        trans_data = json.load(f)
    new_strings = [item["translation"] for item in trans_data]
    print(f"[+] Carregadas {len(new_strings)} frases traduzidas de {trans_json.name}")

    sys_msg_dir = unpack_dir / "SYS_MESSAGE" / "STG7000"
    msg_us_dir = sys_msg_dir / "MESSAGE_US"
    gdl_us = msg_us_dir / "STG7000EE.GDL"
    gc_us = msg_us_dir / "STG7000EE_GC.BIN"

    orig_gdl_data = gdl_us.read_bytes()
    rebuilt_gdl = rebuild_gdl(orig_gdl_data, new_strings)
    gdl_us.write_bytes(rebuilt_gdl)
    print(f"[+] STG7000EE.GDL reconstruído ({len(rebuilt_gdl)} bytes)")

    orig_gc_data = gc_us.read_bytes()
    all_chars = set("".join(new_strings))
    patched_gc = create_extended_strimag(orig_gc_data, orig_gc_data, orig_gc_data, all_chars)
    gc_us.write_bytes(patched_gc)
    print(f"[+] STG7000EE_GC.BIN reconstruído com glifos acentuados ({len(patched_gc)} bytes)")

    for sub in ["MESSAGE_CS", "MESSAGE_CT"]:
        dest_folder = sys_msg_dir / sub
        if dest_folder.exists():
            for g in dest_folder.glob("*.GDL"):
                g.write_bytes(rebuilt_gdl)
            for b in dest_folder.glob("*_GC.BIN"):
                b.write_bytes(patched_gc)
            print(f"    [->] Propagado para {sub}")

    print("[+] Reempacotando contêiner RMHG (STG7000.RSL)...")
    rsl_pack = PROJECT_ROOT / "tools" / "external" / "No-More-RSL" / "rslPack.py"
    subprocess.run([sys.executable, str(rsl_pack), str(unpack_dir), "--overwrite"], check=True, stdout=subprocess.DEVNULL)

    print("[+] Recompactando STG7000.bin com ghmGcLz...")
    new_rsl_data = temp_rsl.read_bytes()
    compressed_data = compress_ghm_lz(new_rsl_data)

    out_bin = PROJECT_ROOT / "data" / "translated" / "STG" / "STG7000" / "STG7000.bin"
    out_bin.parent.mkdir(parents=True, exist_ok=True)
    out_bin.write_bytes(compressed_data)
    print(f"[+] Arquivo compilado: {out_bin} ({len(compressed_data)} bytes)")

    print(f"[+] Instalando na Steam: {stg_bin}...")
    shutil.copy2(out_bin, stg_bin)

    shutil.rmtree(temp_dir, ignore_errors=True)

    print("\n[SUCESSO] STG7000.bin (Santa Destroy e Minigames) traduzido e instalado na Steam com sucesso!")

if __name__ == "__main__":
    game_dir = Path(r"E:\SteamLibrary\steamapps\common\No More Heroes 2 Desperate Struggle")
    patch_stg7000(game_dir)

