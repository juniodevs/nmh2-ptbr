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
from tools.utilities.patch_strimag import StrimagFont, StrimagGlyph, encode_i8

def build_ninepin_bold_pt(us_gc_path: Path, es_gc_path: Path, fr_gc_path: Path) -> bytes:
    fo_ee = StrimagFont(us_gc_path.read_bytes())
    fo_es = StrimagFont(es_gc_path.read_bytes())
    fo_fr = StrimagFont(fr_gc_path.read_bytes())

    glyphs = dict(fo_ee.glyphs)
    for c in ['E', 'F', 'Q', 'V', 'q', 'z', 'á', 'é', 'ê', 'í', 'ó', 'ô', 'ú']:
        if ord(c) in fo_es.glyphs:
            glyphs[ord(c)] = fo_es.glyphs[ord(c)]
        elif ord(c) in fo_fr.glyphs:
            glyphs[ord(c)] = fo_fr.glyphs[ord(c)]

    # Sintetizar 'ã' (a + til do ñ)
    g_a = glyphs[ord('a')]
    g_n_tilde = fo_es.glyphs[ord('ñ')]
    bmp_atilde = g_n_tilde.bitmap2x[:10] + g_a.bitmap2x
    glyphs[ord('ã')] = StrimagGlyph(ord('ã'), 0, 0, 10, 13, 1, 2, 10, bitmap2x=bmp_atilde)

    # Sintetizar 'õ' (o + til do ñ)
    g_o = glyphs[ord('o')]
    bmp_otilde = g_n_tilde.bitmap2x[:10] + g_o.bitmap2x
    glyphs[ord('õ')] = StrimagGlyph(ord('õ'), 0, 0, 10, 13, 2, 2, 10, bitmap2x=bmp_otilde)

    # Sintetizar 'É' (E + acento agudo do é)
    g_E = glyphs[ord('E')]
    g_acute = fo_es.glyphs[ord('é')]
    bmp_Eacute = g_acute.bitmap2x[:10] + g_E.bitmap2x
    glyphs[ord('É')] = StrimagGlyph(ord('É'), 0, 0, 10, 16, 1, 0, 10, bitmap2x=bmp_Eacute)

    tex_w = 128
    tex_h = 76
    tex_w_2x = tex_w * 2
    tex_h_2x = tex_h * 2

    canvas = [[0 for _ in range(tex_w_2x)] for _ in range(tex_h_2x)]

    cur_x = 0
    cur_y = 0
    row_h = 0
    for g in sorted(glyphs.values(), key=lambda g: (-g.h, g.code)):
        gw = g.w * 2
        gh = g.h * 2
        if cur_x + gw > tex_w_2x:
            cur_x = 0
            cur_y += row_h
            row_h = 0
        g.x = cur_x // 2
        g.y = cur_y // 2
        bmp = g.bitmap2x
        if bmp:
            for r in range(len(bmp)):
                for c in range(len(bmp[r])):
                    if cur_y + r < tex_h_2x and cur_x + c < tex_w_2x:
                        canvas[cur_y + r][cur_x + c] = bmp[r][c]
        cur_x += gw + 2
        row_h = max(row_h, gh)

    char_cnt = len(glyphs)
    hdr = bytearray(0xA0)
    hdr[0:8] = b'STRIMAG2'
    struct.pack_into('>IIIIII', hdr, 8, 0, 0x1C, 0, 0, char_cnt, 1)
    name_bytes = b'Ninepin Bold'
    hdr[0x20 : 0x20 + len(name_bytes)] = name_bytes
    struct.pack_into('>I', hdr, 0x60, 20)

    tbl = bytearray()
    for code in sorted(glyphs.keys()):
        g = glyphs[code]
        tbl.extend(struct.pack('>10H',
            g.code, g.x, g.y, g.w, g.h,
            g.xoff, g.yoff, g.xadv, g.page, g.id2
        ))

    pad_len = ((len(hdr) + len(tbl) + 31) & ~31) - (len(hdr) + len(tbl))
    tbl_padding = b'\x00' * pad_len

    tex_hdr = bytearray(64)
    tex_hdr[0:8] = b'\x01\x00\x00\x00\x00\x00\x00\x01'
    struct.pack_into('>HH', tex_hdr, 8, tex_w, tex_h)
    struct.pack_into('>I', tex_hdr, 12, 0)
    struct.pack_into('>I', tex_hdr, 16, 0x40)
    struct.pack_into('>I', tex_hdr, 32, 202) # Flag original inviolada

    pix_data = encode_i8(canvas, tex_w, tex_h)
    return bytes(hdr) + bytes(tbl) + tbl_padding + bytes(tex_hdr) + bytes(pix_data)

def patch_stg3004(game_dir: Path):
    backup_file = PROJECT_ROOT / "backups" / "STG" / "STG3004" / "STG3004.bin.bak"
    if not backup_file.exists():
        raise FileNotFoundError(f"Backup original não encontrado em: {backup_file}")

    temp_dir = PROJECT_ROOT / "data" / "translated" / "_temp_stg3004"
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)

    print("[+] Descompactando STG3004.bin.bak (ghmGcLz)...")
    raw_data = backup_file.read_bytes()
    rsl_data = decompress_ghm_lz(raw_data)

    temp_rsl = temp_dir / "STG3004.RSL"
    temp_rsl.write_bytes(rsl_data)
    print(f"    RSL descompactado: {len(rsl_data)} bytes")

    print("[+] Extraindo contêiner STG3004.RSL...")
    rsl_extract = PROJECT_ROOT / "tools" / "external" / "No-More-RSL" / "rslExtract.py"
    subprocess.run([sys.executable, str(rsl_extract), str(temp_rsl)], check=True, stdout=subprocess.DEVNULL)

    unpack_dir = temp_dir / "STG3004"

    # Carregar textos traduzidos
    trans_json = PROJECT_ROOT / "translation" / "pt-BR" / "STG" / "STG3004" / "STG3004EE.json"
    with open(trans_json, "r", encoding="utf-8") as f:
        trans_data = json.load(f)

    sys_msg_dir = unpack_dir / "SYS_MESSAGE" / "TALK"
    msg_us_dir = sys_msg_dir / "MESSAGE_US"
    gdl_us = msg_us_dir / "STG3004EE.GDL"
    gc_us = msg_us_dir / "STG3004EE_GC.BIN"
    gc_es = sys_msg_dir / "MESSAGE_SP" / "STG3004ES_GC.BIN"
    gc_fr = sys_msg_dir / "MESSAGE_FR" / "STG3004EF_GC.BIN"

    orig_gdl_data = gdl_us.read_bytes()
    orig_strings = parse_gdl(orig_gdl_data)
    new_strings = []
    for i, item in enumerate(trans_data):
        t = item.get("translation", "")
        if not t and "text" in item:
            t = item["text"]
        if not t:
            t = orig_strings[i] if i < len(orig_strings) else ""
        new_strings.append(t)

    # Reconstruir GDL com alinhamento estrito de 16 bytes
    rebuilt_gdl = rebuild_gdl(orig_gdl_data, new_strings)
    pad = (16 - (len(rebuilt_gdl) % 16)) % 16
    rebuilt_gdl += b'\x00' * pad
    gdl_us.write_bytes(rebuilt_gdl)
    print(f"[+] STG3004EE.GDL reconstruído e alinhado ({len(rebuilt_gdl)} bytes, %16={len(rebuilt_gdl)%16})")

    # Construir fonte Ninepin Bold nativa estendida (128x76, flag 202)
    native_gc = build_ninepin_bold_pt(gc_us, gc_es, gc_fr)
    gc_us.write_bytes(native_gc)
    print(f"[+] STG3004EE_GC.BIN Ninepin Bold nativo construído ({len(native_gc)} bytes, 128x76)")

    # Propagar para CS e CT por segurança
    for sub in ["MESSAGE_CS", "MESSAGE_CT"]:
        dest_folder = sys_msg_dir / sub
        if dest_folder.exists():
            for g in dest_folder.glob("*.GDL"):
                g.write_bytes(rebuilt_gdl)
            for b in dest_folder.glob("*_GC.BIN"):
                b.write_bytes(native_gc)
            print(f"    [->] Propagado para {sub}")

    print("[+] Reempacotando contêiner RMHG (STG3004.RSL)...")
    rsl_pack = PROJECT_ROOT / "tools" / "external" / "No-More-RSL" / "rslPack.py"
    subprocess.run([sys.executable, str(rsl_pack), str(unpack_dir), "--overwrite"], check=True, stdout=subprocess.DEVNULL)

    print("[+] Recompactando STG3004.bin com ghmGcLz...")
    new_rsl_data = temp_rsl.read_bytes()
    compressed_data = compress_ghm_lz(new_rsl_data)

    out_bin = PROJECT_ROOT / "data" / "translated" / "STG" / "STG3004" / "STG3004.bin"
    out_bin.parent.mkdir(parents=True, exist_ok=True)
    out_bin.write_bytes(compressed_data)
    print(f"[+] Arquivo compilado com sucesso: {out_bin} ({len(compressed_data)} bytes)")

    steam_bin = game_dir / "STG" / "STG3004" / "STG3004.bin"
    if steam_bin.parent.exists():
        shutil.copy2(out_bin, steam_bin)
        print(f"[+] Instalado na Steam para teste imediato: {steam_bin}")

    shutil.rmtree(temp_dir, ignore_errors=True)
    print("\n[SUCESSO] STG3004.bin (Ryan's Gym) compilado com perfeição!")

if __name__ == "__main__":
    game_path = Path(r"E:\SteamLibrary\steamapps\common\No More Heroes 2 Desperate Struggle")
    patch_stg3004(game_path)
