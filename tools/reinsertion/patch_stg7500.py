# -*- coding: utf-8 -*-

import os
import sys
import shutil
import struct
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from tools.extraction.ghm_lz import decompress_ghm_lz, compress_ghm_lz

def create_sub_dds_from_image(img_path: Path) -> bytes:
    img = Image.open(img_path).convert('RGBA')
    width, height = img.size

    arr = np.array(img)
    bgra = np.zeros_like(arr)
    bgra[:, :, 0] = arr[:, :, 2]
    bgra[:, :, 1] = arr[:, :, 1]
    bgra[:, :, 2] = arr[:, :, 0]
    bgra[:, :, 3] = arr[:, :, 3]

    dds_hdr = bytearray(128)
    dds_hdr[:4] = b'DDS '
    struct.pack_into('<I', dds_hdr, 4, 124)
    struct.pack_into('<I', dds_hdr, 8, 0x1007)
    struct.pack_into('<I', dds_hdr, 12, height)
    struct.pack_into('<I', dds_hdr, 16, width)
    struct.pack_into('<I', dds_hdr, 20, width*4)
    struct.pack_into('<I', dds_hdr, 28, 0)

    struct.pack_into('<I', dds_hdr, 76, 32)
    struct.pack_into('<I', dds_hdr, 80, 0x41)
    struct.pack_into('<I', dds_hdr, 88, 32)
    struct.pack_into('<I', dds_hdr, 92, 0x00FF0000)
    struct.pack_into('<I', dds_hdr, 96, 0x0000FF00)
    struct.pack_into('<I', dds_hdr, 100, 0x000000FF)
    struct.pack_into('<I', dds_hdr, 104, 0xFF000000)

    struct.pack_into('<I', dds_hdr, 108, 0x1000)

    return bytes(dds_hdr) + bgra.tobytes()

def make_k7tx_bin(dds_bytes: bytes) -> bytes:
    hdr = bytearray(72)
    struct.pack_into('<I', hdr, 0, 0)
    struct.pack_into('<I', hdr, 4, 6)
    struct.pack_into('<I', hdr, 8, 2097525)
    struct.pack_into('<I', hdr, 12, 0)
    struct.pack_into('<I', hdr, 16, 64)
    hdr[64:68] = b'K7TX'
    struct.pack_into('<I', hdr, 68, len(dds_bytes))
    return bytes(hdr) + dds_bytes

def patch_stg7500(game_dir: Path):
    stg_bin = game_dir / "STG" / "STG7500" / "STG7500.bin"
    backup_file = PROJECT_ROOT / "backups" / "STG" / "STG7500.bin.bak"
    backup_file.parent.mkdir(parents=True, exist_ok=True)

    if not backup_file.exists():
        print(f"[+] Criando backup de {stg_bin.name}...")
        shutil.copy(stg_bin, backup_file)
        src_bin = stg_bin
    else:
        print(f"[+] Usando backup preservado: {backup_file.name}")
        src_bin = backup_file

    temp_dir = PROJECT_ROOT / "data" / "translated" / "_temp_stg7500"
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)

    print("[+] Descompactando STG7500.bin...")
    raw = src_bin.read_bytes()
    rsl_data = decompress_ghm_lz(raw)

    temp_rsl = temp_dir / "STG7500.RSL"
    temp_rsl.write_bytes(rsl_data)

    print("[+] Extraindo contêiner STG7500.RSL...")
    rsl_extract = PROJECT_ROOT / "tools" / "external" / "No-More-RSL" / "rslExtract.py"
    subprocess.run([sys.executable, str(rsl_extract), str(temp_rsl)], check=True, stdout=subprocess.DEVNULL)

    unpack_dir = temp_dir / "STG7500"
    sub_rsl_dir = unpack_dir / "EVENT" / "MINIDEMO" / "EFFECT" / "SUB75000.RSL"

    img_pt = PROJECT_ROOT / "data" / "temp_stg7500" / "ea7500_pt.png"
    print(f"[+] Gerando textura da legenda de Sylvia: 'Sylvia... Isso sim é o paraíso.'...")
    dds_bytes = create_sub_dds_from_image(img_pt)
    new_bin = make_k7tx_bin(dds_bytes)

    for target_name in ["2x_EA7500_EN.BIN", "2x_EA7500_SP_EU.BIN", "2x_EA7500_CS.BIN", "2x_EA7500_CT.BIN", "2x_EA7500_FR.BIN", "2x_EA7500_GE.BIN", "2x_EA7500_IT.BIN"]:
        target_path = sub_rsl_dir / target_name
        if target_path.exists():
            target_path.write_bytes(new_bin)
            print(f"    [->] Injetado em: {target_name} ({len(new_bin)} bytes)")

    rsl_pack = PROJECT_ROOT / "tools" / "external" / "No-More-RSL" / "rslPack.py"
    print("[+] Reempacotando contêineres RSL...")
    subprocess.run([sys.executable, str(rsl_pack), str(sub_rsl_dir), "--overwrite"], check=True, stdout=subprocess.DEVNULL)

    subprocess.run([sys.executable, str(rsl_pack), str(unpack_dir), "--overwrite"], check=True, stdout=subprocess.DEVNULL)

    print("[+] Recompactando STG7500.bin com ghmGcLz...")
    new_rsl_data = temp_rsl.read_bytes()
    compressed_data = compress_ghm_lz(new_rsl_data)

    out_bin = PROJECT_ROOT / "data" / "translated" / "STG" / "STG7500" / "STG7500.bin"
    out_bin.parent.mkdir(parents=True, exist_ok=True)
    out_bin.write_bytes(compressed_data)
    print(f"[+] Arquivo compilado: {out_bin} ({len(compressed_data)} bytes)")

    print(f"[+] Instalando na Steam: {stg_bin}...")
    shutil.copy(out_bin, stg_bin)

    print("\n[SUCESSO] Legenda de Sylvia 'Sylvia... Isso sim é o paraíso.' instalada com sucesso!")

if __name__ == "__main__":
    game_dir = Path(r"E:\SteamLibrary\steamapps\common\No More Heroes 2 Desperate Struggle")
    patch_stg7500(game_dir)

