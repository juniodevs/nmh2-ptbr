# -*- coding: utf-8 -*-
import os
import sys
import shutil
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools.utilities.fast_scanner import decompress_fast
from tools.utilities.gdl_tool import parse_gdl

GAME_DIR = Path(r"E:\SteamLibrary\steamapps\common\No More Heroes 2 Desperate Struggle")

unmapped_files = [
    "STG/STG0202/STG0202.bin",
    "STG/STG0601/STG0601.bin",
    "STG/STG1301/STG1301.bin",
    "STG/STG4000/STG4000.bin",
    "STG/STG4001/STG4001.bin",
    "STG/STG4002/STG4002.bin",
    "STG/STG4003/STG4003.bin",
    "STG/STG4004/STG4004.bin",
    "STG/STG7001/STG7001.bin",
    "StaffRoll/StaffRoll_EU.RSL",
]

def inspect_unmapped():
    temp_dir = PROJECT_ROOT / "data" / "extracted" / "_temp_inspect_unmapped"
    temp_dir.mkdir(parents=True, exist_ok=True)
    rsl_extract = PROJECT_ROOT / "tools" / "external" / "No-More-RSL" / "rslExtract.py"
    
    print("=" * 70)
    print("INSPEÇÃO DETALHADA DE ARQUIVOS NÃO MAPEADOS COM GDL")
    print("=" * 70)
    
    for rel_path in unmapped_files:
        src = GAME_DIR / rel_path
        if not src.exists():
            print(f"[!] Não encontrado: {src}")
            continue
            
        print(f"\n[+] Analisando: {rel_path} ({src.stat().st_size} bytes)")
        raw_data = src.read_bytes()
        decomp_data = decompress_fast(raw_data)
        
        target_rsl = temp_dir / f"{src.stem}.RSL"
        target_rsl.write_bytes(decomp_data)
        
        unpack_folder = temp_dir / src.stem
        if unpack_folder.exists():
            shutil.rmtree(unpack_folder)
            
        try:
            subprocess.run([sys.executable, str(rsl_extract), str(target_rsl)], 
                           cwd=str(temp_dir), check=True, stdout=subprocess.DEVNULL)
        except Exception as e:
            print(f"    [-] Falha ao extrair com rslExtract: {e}")
            target_rsl.unlink(missing_ok=True)
            continue
            
        gdls = list(unpack_folder.rglob("*.GDL"))
        print(f"    Encontrados {len(gdls)} arquivos .GDL:")
        for gdl in gdls:
            try:
                strings = parse_gdl(gdl.read_bytes())
                rel_gdl = gdl.relative_to(unpack_folder)
                print(f"      - {rel_gdl}: {len(strings)} strings")
                # Show first 3 non-empty strings
                non_empty = [s for s in strings if s.strip()][:3]
                for s in non_empty:
                    preview = s.replace('\n', ' ').replace('\r', '')[:60]
                    print(f"          sample: \"{preview}\"")
            except Exception as e:
                print(f"      - {gdl.name}: erro ao parsear: {e}")
                
        shutil.rmtree(unpack_folder, ignore_errors=True)
        target_rsl.unlink(missing_ok=True)
        
    shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    inspect_unmapped()
