# -*- coding: utf-8 -*-

import os
import sys
import shutil
import struct
import subprocess
from pathlib import Path
from PIL import Image
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def create_dds_from_image(img_path: Path) -> bytes:
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
    struct.pack_into('<I', hdr, 8, 31064376)
    struct.pack_into('<I', hdr, 12, 0)
    struct.pack_into('<I', hdr, 16, 64)
    hdr[64:68] = b'K7TX'
    struct.pack_into('<I', hdr, 68, len(dds_bytes))
    return bytes(hdr) + dds_bytes

def patch_fax(game_dir: Path):
    fax_rsl = game_dir / "PJFaxMes" / "PJFax_Mess_EE.RSL"
    backup_file = PROJECT_ROOT / "backups" / "PJFaxMes" / "PJFax_Mess_EE.RSL.bak"
    backup_file.parent.mkdir(parents=True, exist_ok=True)

    if not backup_file.exists():
        print(f"[+] Criando backup de {fax_rsl.name}...")
        shutil.copy2(fax_rsl, backup_file)
        src_rsl = fax_rsl
    else:
        print(f"[+] Usando backup preservado: {backup_file.name}")
        src_rsl = backup_file

    temp_dir = PROJECT_ROOT / "data" / "translated" / "_temp_fax"
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)

    temp_rsl = temp_dir / "PJFax_Mess_EE.RSL"
    shutil.copy2(src_rsl, temp_rsl)

    print("[+] Extraindo contêiner PJFax_Mess_EE.RSL...")
    rsl_extract = PROJECT_ROOT / "tools" / "external" / "No-More-RSL" / "rslExtract.py"
    subprocess.run([sys.executable, str(rsl_extract), str(temp_rsl)], check=True, stdout=subprocess.DEVNULL)

    unpack_dir = temp_dir / "PJFax_Mess_EE"
    obj_dir = unpack_dir / "OBJECT"

    img_pt = PROJECT_ROOT / "data" / "temp_fax" / "faxpaper_pt_perfect.png"
    print(f"[+] Convertendo imagem do Fax ({img_pt.name}) para textura DDS/K7TX...")
    dds_bytes = create_dds_from_image(img_pt)
    new_bin = make_k7tx_bin(dds_bytes)

    target_bin = obj_dir / "2x_faxpaper01.BIN"
    target_bin.write_bytes(new_bin)
    print(f"    [->] Injetado em {target_bin.name} ({len(new_bin)} bytes)")

    print("[+] Reempacotando contêiner RMHG...")
    rsl_pack = PROJECT_ROOT / "tools" / "external" / "No-More-RSL" / "rslPack.py"
    subprocess.run([sys.executable, str(rsl_pack), str(unpack_dir), "--overwrite"], check=True, stdout=subprocess.DEVNULL)

    out_rsl = PROJECT_ROOT / "data" / "translated" / "PJFaxMes" / "PJFax_Mess_EE.RSL"
    out_rsl.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(temp_rsl, out_rsl)
    print(f"[+] Arquivo compilado: {out_rsl} ({out_rsl.stat().st_size} bytes)")

    print(f"[+] Instalando na Steam: {fax_rsl}...")
    shutil.copy2(out_rsl, fax_rsl)

    fax_es = game_dir / "PJFaxMes" / "PJFax_Mess_ES.RSL"
    if fax_es.exists():
        pass

    shutil.rmtree(temp_dir, ignore_errors=True)

    print("\n[SUCESSO] Folha do Fax da UAA traduzida e instalada na Steam com sucesso!")

if __name__ == "__main__":
    game_dir = Path(r"E:\SteamLibrary\steamapps\common\No More Heroes 2 Desperate Struggle")
    patch_fax(game_dir)

