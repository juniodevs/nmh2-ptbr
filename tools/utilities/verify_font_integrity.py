# -*- coding: utf-8 -*-
import os
import sys
import hashlib
import struct
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools.utilities.fast_scanner import decompress_fast

DATA_TRANS = PROJECT_ROOT / "data" / "translated"
STEAM_DIR = Path(r"E:\SteamLibrary\steamapps\common\No More Heroes 2 Desperate Struggle")
PROJECT_BAK = PROJECT_ROOT / "backups"
STEAM_BAK = STEAM_DIR / ".backup"

def md5(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()

def inspect_strimag(data: bytes):
    if len(data) < 0xA0 or data[:8] != b'STRIMAG2':
        return None
    char_cnt = struct.unpack('>I', data[24:28])[0]
    font_name = data[32:64].split(b'\x00')[0].decode('latin-1', 'replace')
    tex_hdr_off = ((0xA0 + char_cnt * 20) + 31) & ~31
    if tex_hdr_off + 12 <= len(data):
        tex_w, tex_h = struct.unpack('>HH', data[tex_hdr_off+8 : tex_hdr_off+12])
    else:
        tex_w, tex_h = (0, 0)
    return {
        'char_cnt': char_cnt,
        'font_name': font_name,
        'tex_size': (tex_w, tex_h)
    }

def find_strimag_fonts(data: bytes):
    fonts = []
    pos = 0
    while True:
        idx = data.find(b'STRIMAG2', pos)
        if idx == -1:
            break
        info = inspect_strimag(data[idx:idx+0x50000]) # at most 300KB
        if info:
            fonts.append(info)
        pos = idx + 8
    return fonts

def verify_all():
    print("=" * 70)
    print("VERIFICAÇÃO DE INTEGRIDADE: FONTES, GLIFOS E COMPILAÇÃO")
    print("=" * 70)
    
    trans_files = []
    for root, dirs, files in os.walk(DATA_TRANS):
        for f in files:
            p = Path(root) / f
            if any(part.startswith("_") for part in p.parts):
                continue
            rel = p.relative_to(DATA_TRANS)
            trans_files.append(rel)
            
    print(f"Total de arquivos traduzidos em data/translated/: {len(trans_files)}")
    
    steam_match_count = 0
    steam_mismatch_count = 0
    steam_missing_count = 0
    
    backup_exists_count = 0
    backup_missing_count = 0
    
    font_ok_count = 0
    font_old_count = 0
    no_font_count = 0
    
    report_items = []
    
    for rel in sorted(trans_files):
        trans_p = DATA_TRANS / rel
        steam_p = STEAM_DIR / rel
        
        # Check backup
        bak1 = PROJECT_BAK / f"{rel}.bak"
        bak2 = PROJECT_BAK / rel
        bak3 = STEAM_BAK / rel
        
        has_bak = bak1.exists() or bak2.exists() or bak3.exists()
        if has_bak:
            backup_exists_count += 1
        else:
            backup_missing_count += 1
            
        trans_bytes = trans_p.read_bytes()
        trans_md5 = md5(trans_bytes)
        
        steam_status = "OK"
        if not steam_p.exists():
            steam_status = "NÃO INSTALADO NA STEAM"
            steam_missing_count += 1
        else:
            steam_bytes = steam_p.read_bytes()
            if md5(steam_bytes) == trans_md5:
                steam_match_count += 1
            else:
                steam_status = "DIVERGENTE DA STEAM"
                steam_mismatch_count += 1
                
        # Decompress to check font
        decomp = decompress_fast(trans_bytes)
        fonts = find_strimag_fonts(decomp)
        
        font_status = "SEM FONTES STRIMAG2 (PROVAVEL TEXTURA)"
        if fonts:
            # Check if all or any have char_cnt >= 120
            new_fonts = [f for f in fonts if f['char_cnt'] >= 120]
            if new_fonts:
                font_status = f"NOVA FONTE OK ({len(new_fonts)}/{len(fonts)} com {new_fonts[0]['char_cnt']} glifos)"
                font_ok_count += 1
            else:
                font_status = f"FONTE ANTIGA/ORIGINAL ({fonts[0]['char_cnt']} glifos, {fonts[0]['font_name']})"
                font_old_count += 1
        else:
            no_font_count += 1
            
        report_items.append({
            "file": str(rel),
            "size": len(trans_bytes),
            "steam_status": steam_status,
            "has_backup": has_bak,
            "font_status": font_status,
            "fonts": fonts
        })

    print(f"\n--- STATUS DA INSTALAÇÃO NA STEAM ---")
    print(f"Arquivos 100% idênticos na Steam: {steam_match_count}/{len(trans_files)}")
    print(f"Arquivos divergentes na Steam:     {steam_mismatch_count}")
    print(f"Arquivos não instalados na Steam: {steam_missing_count}")
    
    print(f"\n--- STATUS DOS BACKUPS ORIGINAIS ---")
    print(f"Arquivos com backup preservado: {backup_exists_count}/{len(trans_files)}")
    print(f"Arquivos sem backup encontrado:  {backup_missing_count}")

    print(f"\n--- STATUS DAS FONTES (STRIMAG2) ---")
    print(f"Arquivos com nova fonte TrueType (>120 glifos): {font_ok_count}")
    print(f"Arquivos com fonte original antiga:             {font_old_count}")
    print(f"Arquivos sem STRIMAG2 (apenas texturas/etc):    {no_font_count}")

    if steam_mismatch_count > 0 or steam_missing_count > 0:
        print("\n[!] ARQUIVOS COM PROBLEMA DE SINCRONIA NA STEAM:")
        for it in report_items:
            if it["steam_status"] != "OK":
                print(f"  - {it['file']}: {it['steam_status']}")

    if font_old_count > 0:
        print("\n[!] ARQUIVOS COM FONTE ANTIGA (NÃO ATUALIZADOS):")
        for it in report_items:
            if "FONTE ANTIGA" in it["font_status"]:
                print(f"  - {it['file']}: {it['font_status']}")

    # Save detailed report
    out_rep = PROJECT_ROOT / "docs" / "research" / "integrity_report.json"
    out_rep.write_text(json.dumps(report_items, indent=2), encoding='utf-8')
    print(f"\nRelatório completo salvo em: {out_rep}")

if __name__ == "__main__":
    verify_all()
