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

def create_dds_from_image(img: Image.Image) -> bytes:
    width, height = img.size

    arr = np.array(img.convert('RGBA'))
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
    struct.pack_into('<I', dds_hdr, 20, 0)
    struct.pack_into('<I', dds_hdr, 28, 0)

    struct.pack_into('<I', dds_hdr, 76, 32)
    struct.pack_into('<I', dds_hdr, 80, 0x41)
    struct.pack_into('<I', dds_hdr, 88, 32)
    struct.pack_into('<I', dds_hdr, 92, 0x00FF0000)
    struct.pack_into('<I', dds_hdr, 96, 0x0000FF00)
    struct.pack_into('<I', dds_hdr, 100, 0x000000FF)
    struct.pack_into('<I', dds_hdr, 104, 0xFF000000)

    struct.pack_into('<I', dds_hdr, 108, 0x1002)

    return bytes(dds_hdr) + bgra.tobytes()

def make_k7tx_bin(dds_bytes: bytes, magic_val: int) -> bytes:
    hdr = bytearray(72)
    struct.pack_into('<I', hdr, 0, 0)
    struct.pack_into('<I', hdr, 4, 6)
    struct.pack_into('<I', hdr, 8, magic_val)
    struct.pack_into('<I', hdr, 12, 0)
    struct.pack_into('<I', hdr, 16, 64)
    hdr[64:68] = b'K7TX'
    struct.pack_into('<I', hdr, 68, len(dds_bytes))
    return bytes(hdr) + dds_bytes

def patch_container(container_name: str, replacements: dict, game_dir: Path):
    rsl_extract = PROJECT_ROOT / "tools" / "external" / "No-More-RSL" / "rslExtract.py"
    rsl_pack = PROJECT_ROOT / "tools" / "external" / "No-More-RSL" / "rslPack.py"

    bak_file = PROJECT_ROOT / "backups" / "Hide" / "RankingUp" / f"{container_name}.bak"
    steam_rsl = game_dir / "Hide" / "RankingUp" / container_name

    temp_dir = PROJECT_ROOT / "data" / "translated" / f"_temp_{container_name.split('.')[0]}"
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)

    temp_rsl = temp_dir / container_name
    shutil.copy2(bak_file, temp_rsl)

    print(f"[+] Extraindo contêiner {container_name}...")
    subprocess.run([sys.executable, str(rsl_extract), str(temp_rsl)], cwd=str(temp_dir), check=True, stdout=subprocess.DEVNULL)

    unpack_folder = temp_dir / container_name.split('.')[0]
    obj_dir = unpack_folder / "OBJECT"

    for target_bin_name, (img_path, magic_val) in replacements.items():
        img = Image.open(img_path)
        print(f"    [->] Convertendo {img_path.name} ({img.size[0]}x{img.size[1]}) para {target_bin_name}...")
        dds_bytes = create_dds_from_image(img)
        k7tx_bytes = make_k7tx_bin(dds_bytes, magic_val)
        target_path = obj_dir / target_bin_name
        target_path.write_bytes(k7tx_bytes)
        print(f"         Gravado: {len(k7tx_bytes)} bytes")

    print(f"[+] Reempacotando contêiner {container_name}...")
    subprocess.run([sys.executable, str(rsl_pack), str(unpack_folder), "--overwrite"], cwd=str(temp_dir), check=True, stdout=subprocess.DEVNULL)

    out_rsl = PROJECT_ROOT / "data" / "translated" / "Hide" / "RankingUp" / container_name
    out_rsl.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(temp_rsl, out_rsl)
    print(f"[+] Contêiner compilado: {out_rsl} ({out_rsl.stat().st_size} bytes)")

    print(f"[+] Instalando na Steam: {steam_rsl}...")
    shutil.copy2(out_rsl, steam_rsl)

    base_prefix = container_name.split('.')[0][:-2]
    for variant in [f"{base_prefix}EC.RSL", f"{base_prefix}ET.RSL"]:
        var_path = game_dir / "Hide" / "RankingUp" / variant
        if var_path.exists():
            shutil.copy2(out_rsl, var_path)
            print(f"    [+] Variante sincronizada: {variant}")

    shutil.rmtree(temp_dir, ignore_errors=True)

def main():
    game_dir = Path(r"E:\SteamLibrary\steamapps\common\No More Heroes 2 Desperate Struggle")
    png_dir = PROJECT_ROOT / "data" / "temp_ranking" / "pngs"

    print("=================================================================")
    print("  INJETANDO BANNERS GRÁFICOS DE RANK UP / SUBMISSION (PT-BR)     ")
    print("=================================================================\n")

    patch_container("FaildEE.RSL", {
        "E_HY_IF_FAILED.BIN": (png_dir / "pt_FALHA.png", 5243296),
        "hy_timeup.BIN": (png_dir / "pt_TEMPO_ESGOTADO.png", 6291904),
    }, game_dir)

    print()

    patch_container("sm_startEE.RSL", {
        "HY_SUB_GO.BIN": (png_dir / "pt_VAI_perfect.png", 16777570),
    }, game_dir)

    print()

    patch_container("ResultEE.RSL", {
        "HY_FINISHTIME.BIN": (png_dir / "pt_TEMPO_FINAL.png", 12583456),
    }, game_dir)

    print("\n=================================================================")
    print("  TODOS OS 4 BANNERS GRÁFICOS FORAM INSTALADOS COM SUCESSO!       ")
    print("=================================================================")

if __name__ == "__main__":
    main()

