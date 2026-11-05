# -*- coding: utf-8 -*-
import os
import sys
import time
import struct
import json
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

GAME_DIR = Path(r"E:\SteamLibrary\steamapps\common\No More Heroes 2 Desperate Struggle")

def decompress_fast(data: bytes) -> bytes:
    if len(data) < 9:
        return data
    uncomp_sz, comp_sz = struct.unpack('<II', data[:8])
    if comp_sz != len(data) or uncomp_sz <= comp_sz:
        return data
        
    escape_byte = data[8]
    esc_b = bytes([escape_byte])
    
    src = 9
    src_end = min(len(data), comp_sz)
    out = bytearray(uncomp_sz)
    dst = 0
    
    while src < src_end and dst < uncomp_sz:
        next_esc = data.find(esc_b, src, src_end)
        if next_esc == -1:
            chunk_len = src_end - src
            out[dst : dst + chunk_len] = data[src : src_end]
            dst += chunk_len
            break
        elif next_esc > src:
            chunk_len = next_esc - src
            out[dst : dst + chunk_len] = data[src : next_esc]
            dst += chunk_len
            src = next_esc
            
        src += 1
        if src >= src_end:
            break
        nxt = data[src]
        src += 1
        if nxt == escape_byte:
            out[dst] = escape_byte
            dst += 1
        else:
            code = (nxt - 1) if nxt > escape_byte else nxt
            length = (code >> 3)
            if (code & 4) != 0:
                length |= (data[src] << 5)
                src += 1
            length += 4
            
            offset_bytes = (code & 3)
            dist = data[src]
            src += 1
            if offset_bytes != 0:
                dist |= (data[src] << 8)
                src += 1
                if offset_bytes == 2:
                    dist |= (data[src] << 16)
                    src += 1
            dist += 1
            
            ref = dst - dist
            for _ in range(length):
                out[dst] = out[ref]
                dst += 1
                ref += 1

    return bytes(out[:dst])

def extract_strings_from_rmhg(data: bytes):
    """Extrai nomes de arquivos de contêineres RMHG"""
    names = []
    # Find all .GDL occurrences
    pos = 0
    while True:
        idx = data.find(b'.GDL', pos)
        if idx == -1:
            break
        # trace back to find filename
        start = idx
        while start > 0 and data[start-1] >= 0x20 and data[start-1] <= 0x7E:
            start -= 1
        name = data[start:idx+4].decode('ascii', errors='ignore')
        if name and name not in names:
            names.append(name)
        pos = idx + 4
        
    # Also find graphic subtitle textures (EA0... or SUB0...)
    sub_textures = []
    pos = 0
    while True:
        idx = data.find(b'SUB', pos)
        if idx == -1:
            break
        # check if it's SUBxxxx.RSL
        chunk = data[idx:idx+12]
        if b'.RSL' in chunk:
            end = chunk.find(b'.RSL') + 4
            name = chunk[:end].decode('ascii', errors='ignore')
            if name not in sub_textures:
                sub_textures.append(name)
        pos = idx + 3

    return names, sub_textures

def check_file(rel_path_str: str):
    file_path = GAME_DIR / rel_path_str
    try:
        raw_data = file_path.read_bytes()
    except Exception as e:
        return {"path": rel_path_str, "error": str(e)}
        
    decomp_data = decompress_fast(raw_data)
    gdlg_count = decomp_data.count(b'GDLG')
    gdl_names, sub_textures = extract_strings_from_rmhg(decomp_data)
    
    return {
        "path": rel_path_str,
        "is_compressed": len(decomp_data) != len(raw_data),
        "raw_size": len(raw_data),
        "decomp_size": len(decomp_data),
        "gdlg_count": gdlg_count,
        "gdl_names": gdl_names,
        "sub_textures": sub_textures
    }

def main():
    print("=" * 70)
    print("AUDITORIA COMPLETA DE RECURSOS E DIÁLOGOS (NMH2 STEAM)")
    print("=" * 70)
    
    all_files = []
    ignore_dirs = {".backup", "Sound", "Shaders"}
    ignore_exts = {".brstm", ".brsar", ".webm", ".exe", ".dll", ".dds", ".fnt", ".cache", ".txt"}
    
    for root, dirs, files in os.walk(GAME_DIR):
        for f in files:
            p = Path(root) / f
            rel = p.relative_to(GAME_DIR)
            if rel.parts[0] in ignore_dirs:
                continue
            if p.suffix.lower() in ignore_exts:
                continue
            all_files.append(str(rel))
            
    print(f"Total de arquivos de dados do jogo a auditar: {len(all_files)}")
    
    start_t = time.time()
    results = []
    
    # Run with 6 workers
    with ProcessPoolExecutor(max_workers=6) as executor:
        futures = {executor.submit(check_file, f): f for f in all_files}
        for future in as_completed(futures):
            res = future.result()
            results.append(res)
            
    total_time = time.time() - start_t
    print(f"Auditoria concluída em {total_time:.2f} segundos!\n")
    
    # Save raw json report
    out_json = PROJECT_ROOT / "docs" / "research" / "game_dialog_audit.json"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(results, indent=2), encoding='utf-8')
    
    # Filter files with dialogue / GDL / sub_textures
    dialog_files = [r for r in results if r.get("gdlg_count", 0) > 0 or r.get("gdl_names") or r.get("sub_textures")]
    
    print("=" * 70)
    print(f"ARQUIVOS COM DIÁLOGOS / GDL / LEGENDAS ({len(dialog_files)} arquivos):")
    print("=" * 70)
    
    by_category = {}
    for it in dialog_files:
        cat = Path(it["path"]).parts[0]
        by_category.setdefault(cat, []).append(it)
        
    for cat, items in sorted(by_category.items()):
        print(f"\n[{cat}] ({len(items)} arquivos)")
        for it in sorted(items, key=lambda x: x["path"]):
            gdlg_c = it["gdlg_count"]
            gdls = it["gdl_names"]
            subs = it["sub_textures"]
            details = []
            if gdlg_c > 0:
                details.append(f"GDLG magic: {gdlg_c}")
            if gdls:
                details.append(f"GDLs: {', '.join(gdls)}")
            if subs:
                details.append(f"Subs: {', '.join(subs)}")
            print(f"  - {it['path']}: {' | '.join(details)}")

if __name__ == "__main__":
    main()
