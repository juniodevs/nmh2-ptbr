# -*- coding: utf-8 -*-
import os
import sys
import struct
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools.extraction.ghm_lz import decompress_ghm_lz
from tools.utilities.gdl_tool import parse_gdl

GAME_DIR = Path(r"E:\SteamLibrary\steamapps\common\No More Heroes 2 Desperate Struggle")

def is_ghm_lz(data: bytes) -> bool:
    if len(data) < 9:
        return False
    uncomp_sz, comp_sz = struct.unpack('<II', data[:8])
    return comp_sz == len(data) and uncomp_sz > comp_sz

def scan_all_game_files():
    print("=" * 70)
    print("VARREDURA COMPLETA DE ARQUIVOS COM GDLG NO JOGO (STEAM)")
    print("=" * 70)
    
    found_gdls = []
    errors = []
    
    # Check all files
    for root, dirs, files in os.walk(GAME_DIR):
        for f in files:
            p = Path(root) / f
            rel = p.relative_to(GAME_DIR)
            
            # Skip backup and audio
            if rel.parts[0] in [".backup", "Sound", "Shaders"]:
                continue
            if p.suffix.lower() in [".brstm", ".brsar", ".webm", ".exe", ".dll", ".dds"]:
                continue
                
            try:
                data = p.read_bytes()
            except Exception as e:
                errors.append((str(rel), str(e)))
                continue
                
            # If compressed, decompress
            decomp = None
            if is_ghm_lz(data):
                try:
                    decomp = decompress_ghm_lz(data)
                except Exception as e:
                    errors.append((str(rel), f"ghm_lz error: {e}"))
                    continue
            else:
                decomp = data
                
            if b'GDLG' in decomp:
                # Count occurrences of GDLG magic
                count_gdlg = decomp.count(b'GDLG')
                found_gdls.append({
                    "rel_path": str(rel),
                    "size": len(data),
                    "decomp_size": len(decomp),
                    "gdlg_count": count_gdlg,
                    "is_compressed": is_ghm_lz(data)
                })

    print(f"Total de arquivos contendo GDLG encontrados: {len(found_gdls)}")
    
    # Group by category
    by_category = {}
    for item in found_gdls:
        cat = Path(item["rel_path"]).parts[0]
        by_category.setdefault(cat, []).append(item)
        
    for cat, items in sorted(by_category.items()):
        print(f"\n[{cat}] ({len(items)} arquivos):")
        for it in items:
            comp_str = "COMPACTADO" if it["is_compressed"] else "RAW"
            print(f"  {it['rel_path']} ({comp_str}, {it['gdlg_count']} GDLG magic)")

if __name__ == "__main__":
    scan_all_game_files()
