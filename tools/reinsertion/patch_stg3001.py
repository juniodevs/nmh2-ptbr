# -*- coding: utf-8 -*-
"""
patch_stg3001.py - Patch para STG3001 (Motel NMH / Quarto do Travis)

Aplica:
1. Texturas traduzidas dos balões de interação em BALLOON_TEXTURE/US:
   - m_closet.BIN     -> ARMÁRIO (56x16)
   - m_shelf.BIN      -> ESTANTE (56x16)
   - m_television.BIN -> TELEVISÃO (80x16)
   - m_toilet.BIN     -> BANHEIRO (72x16)
   - m_exit.BIN       -> SAIR (32x16)
2. Textos do fax (FAXEE.GDL)
3. Textos do minigame da Jeane / suplexes (STG3001EE.GDL)
4. Textos de troca de arma (WEAPONCHANGEEE.GDL)
5. Fonte Ninepin Bold nativa com caracteres PT-BR (á, é, ê, í, ó, ú, ã, õ, ç, É, Ó)
   preservando estritamente flag 202 e dimensões nativas.
6. Alinhamento de todos os GDLs para múltiplos de 16 bytes.
"""

import os
import sys
import json
import shutil
import struct
import subprocess
from pathlib import Path
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools.extraction.ghm_lz import decompress_ghm_lz, compress_ghm_lz
from tools.utilities.gdl_tool import rebuild_gdl, parse_gdl
from tools.utilities.patch_strimag import StrimagFont, StrimagGlyph, encode_i8


def build_balloon_bin(img: Image.Image) -> bytes:
    w, h = img.size
    assert h == 16, f"Height must be 16, got {h}"
    assert w % 4 == 0, f"Width must be multiple of 4, got {w}"

    # 1. DDS header (128 bytes)
    dds_hdr = bytearray(128)
    dds_hdr[0:4] = b'DDS '
    struct.pack_into('<IIIIII', dds_hdr, 4, 124, 0x1007, h, w, 0, 0)
    struct.pack_into('<II4sIIIII', dds_hdr, 76, 32, 0x41, b'\x00\x00\x00\x00', 32, 0x00FF0000, 0x0000FF00, 0x000000FF, 0xFF000000)
    struct.pack_into('<I', dds_hdr, 108, 0x1002) # DDSCAPS_ALPHA | DDSCAPS_TEXTURE

    # 2. Pixel data (BGRA)
    raw = bytearray()
    img_rgba = img.convert('RGBA')
    for y in range(h):
        for x in range(w):
            r, g, b, a = img_rgba.getpixel((x, y))
            raw.extend((b, g, r, a))

    dds_total = bytes(dds_hdr) + bytes(raw)
    dds_sz = len(dds_total)

    # 3. K7TX header (72 bytes)
    k7_hdr = bytearray(72)
    struct.pack_into('<IIHHII', k7_hdr, 0, 0, 6, w, h, 0, 64)
    k7_hdr[64:68] = b'K7TX'
    struct.pack_into('<I', k7_hdr, 68, dds_sz)

    return bytes(k7_hdr) + dds_total


def generate_pt_balloon_textures(balloon_dir: Path):
    """Gera texturas pixel-art autênticas em PT-BR usando fontes nativas do jogo."""
    sp_dir = balloon_dir / "SP"
    us_dir = balloon_dir / "US"

    def read_dds_image(bin_path: Path) -> Image.Image:
        data = bin_path.read_bytes()
        dds_idx = data.find(b'DDS ')
        dds = data[dds_idx:]
        h, w = struct.unpack('<II', dds[12:20])
        pixels = dds[128 : 128 + w * h * 4]
        return Image.frombytes('RGBA', (w, h), pixels, 'raw', 'BGRA')

    us_tv = read_dds_image(us_dir / "m_television.BIN")
    sp_closet = read_dds_image(sp_dir / "m_closet.BIN")
    sp_shelf = read_dds_image(sp_dir / "m_shelf.BIN")
    sp_toilet = read_dds_image(sp_dir / "m_toilet.BIN")
    us_shelf = read_dds_image(us_dir / "m_shelf.BIN")

    # 1. ARMÁRIO (56x16)
    img_armario = sp_closet.copy()
    img_armario.putpixel((29, 1), (0, 0, 0, 255))
    img_armario.putpixel((30, 1), (0, 0, 0, 255))
    img_armario.putpixel((28, 2), (0, 0, 0, 255))
    bin_armario = build_balloon_bin(img_armario)

    # 2. ESTANTE (56x16)
    img_estante = sp_shelf.crop((0, 0, 56, 16))
    bin_estante = build_balloon_bin(img_estante)

    # 3. TELEVISÃO (80x16)
    tilde = sp_toilet.crop((18, 1, 24, 4))
    g_T = us_tv.crop((0, 0, 8, 16))
    g_E = us_tv.crop((9, 0, 16, 16))
    g_L = us_tv.crop((17, 0, 24, 16))
    g_V = us_tv.crop((33, 0, 40, 16))
    g_I = us_tv.crop((41, 0, 47, 16))
    g_S = us_tv.crop((48, 0, 55, 16))
    g_O = us_tv.crop((63, 0, 70, 16))
    g_A = sp_closet.crop((2, 0, 9, 16))

    img_tv = Image.new('RGBA', (80, 16), (255, 255, 255, 255))
    x = 4
    for g in [g_T, g_E, g_L, g_E, g_V, g_I, g_S, g_A, g_O]:
        img_tv.paste(g, (x, 0))
        x += g.width + 1
    img_tv.paste(tilde, (61, 0))
    bin_tv = build_balloon_bin(img_tv)

    # 4. BANHEIRO (72x16)
    g_B_raw = sp_toilet.crop((1, 0, 8, 16))
    g_B = Image.new('RGBA', (7, 16), (255, 255, 255, 255))
    g_B.paste(g_B_raw, (0, -1))
    g_N = us_tv.crop((71, 0, 78, 16))
    g_H = us_shelf.crop((8, 0, 15, 16))
    g_R = sp_closet.crop((10, 0, 17, 16))

    img_banheiro = Image.new('RGBA', (72, 16), (255, 255, 255, 255))
    x = 3
    for g in [g_B, g_A, g_N, g_H, g_E, g_I, g_R, g_O]:
        img_banheiro.paste(g, (x, 0))
        x += g.width + 1
    bin_banheiro = build_balloon_bin(img_banheiro)

    # 5. SAIR (32x16)
    img_sair = Image.new('RGBA', (32, 16), (255, 255, 255, 255))
    x = 1
    for g in [g_S, g_A, g_I, g_R]:
        img_sair.paste(g, (x, 0))
        x += g.width + 1
    bin_sair = build_balloon_bin(img_sair)

    return {
        "m_closet.BIN": bin_armario,
        "m_shelf.BIN": bin_estante,
        "m_television.BIN": bin_tv,
        "m_toilet.BIN": bin_banheiro,
        "m_exit.BIN": bin_sair,
    }


def build_ninepin_bold_pt(us_gc_path: Path, es_gc_path: Path, fr_gc_path: Path, ref_3004_es_path: Path = None) -> bytes:
    fo_ee = StrimagFont(us_gc_path.read_bytes())
    fo_es = StrimagFont(es_gc_path.read_bytes())
    fo_fr = StrimagFont(fr_gc_path.read_bytes())

    glyphs = dict(fo_ee.glyphs)
    for c in ['E', 'F', 'Q', 'V', 'q', 'z', 'á', 'é', 'ê', 'í', 'ó', 'ô', 'ú', 'à', 'â']:
        if ord(c) in fo_es.glyphs:
            glyphs[ord(c)] = fo_es.glyphs[ord(c)]
        elif ord(c) in fo_fr.glyphs:
            glyphs[ord(c)] = fo_fr.glyphs[ord(c)]

    # Til para ã e õ
    g_n_tilde = None
    if ord('ñ') in fo_es.glyphs:
        g_n_tilde = fo_es.glyphs[ord('ñ')]
    elif ref_3004_es_path and ref_3004_es_path.exists():
        f_ref = StrimagFont(ref_3004_es_path.read_bytes())
        if ord('ñ') in f_ref.glyphs:
            g_n_tilde = f_ref.glyphs[ord('ñ')]

    if g_n_tilde:
        g_a = glyphs[ord('a')]
        bmp_atilde = g_n_tilde.bitmap2x[:10] + g_a.bitmap2x
        glyphs[ord('ã')] = StrimagGlyph(ord('ã'), 0, 0, 10, 13, 1, 2, 10, bitmap2x=bmp_atilde)

        g_o = glyphs[ord('o')]
        bmp_otilde = g_n_tilde.bitmap2x[:10] + g_o.bitmap2x
        glyphs[ord('õ')] = StrimagGlyph(ord('õ'), 0, 0, 10, 13, 2, 2, 10, bitmap2x=bmp_otilde)

    # É e Ó
    g_acute = fo_es.glyphs.get(ord('é'))
    if g_acute:
        g_E = glyphs[ord('E')]
        bmp_Eacute = g_acute.bitmap2x[:10] + g_E.bitmap2x
        glyphs[ord('É')] = StrimagGlyph(ord('É'), 0, 0, 10, 16, 1, 0, 10, bitmap2x=bmp_Eacute)

        g_O = glyphs[ord('O')]
        bmp_Oacute = g_acute.bitmap2x[:10] + g_O.bitmap2x
        glyphs[ord('Ó')] = StrimagGlyph(ord('Ó'), 0, 0, 10, 16, 1, 0, 10, bitmap2x=bmp_Oacute)

    # ç (c + cedilha)
    g_c = glyphs.get(ord('c'))
    g_comma = glyphs.get(ord(','))
    if g_c and g_comma:
        w_c = max(len(row) for row in g_c.bitmap2x)
        bmp_cedil = [list(row) for row in g_c.bitmap2x]
        for r in g_comma.bitmap2x[-6:]:
            row_pad = [0] * (w_c // 2) + list(r)
            bmp_cedil.append(row_pad[:w_c])
        glyphs[ord('ç')] = StrimagGlyph(ord('ç'), 0, 0, 10, 16, 1, 2, 10, bitmap2x=bmp_cedil)

    tex_w = 128
    tex_h = 112
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


def patch_stg3001(game_dir: Path):
    backup_file = PROJECT_ROOT / "backups" / "STG" / "STG3001" / "STG3001.bin.bak"
    if not backup_file.exists():
        raise FileNotFoundError(f"Backup original não encontrado em: {backup_file}")

    temp_dir = PROJECT_ROOT / "data" / "translated" / "_temp_stg3001_build"
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)

    print("[+] Descompactando STG3001.bin.bak (ghmGcLz)...")
    raw_data = backup_file.read_bytes()
    rsl_data = decompress_ghm_lz(raw_data)

    temp_rsl = temp_dir / "STG3001.RSL"
    temp_rsl.write_bytes(rsl_data)
    print(f"    RSL descompactado: {len(rsl_data):,} bytes")

    print("[+] Extraindo contêiner STG3001.RSL...")
    rsl_extract = PROJECT_ROOT / "tools" / "external" / "No-More-RSL" / "rslExtract.py"
    subprocess.run([sys.executable, str(rsl_extract), str(temp_rsl)], check=True, stdout=subprocess.DEVNULL)

    unpack_dir = temp_dir / "STG3001"

    # 1. Injetar texturas traduzidas dos balões de interação
    print("[+] Injetando balões de interação traduzidos (BALLOON_TEXTURE)...")
    balloon_dir = unpack_dir / "BALLOON_TEXTURE"
    pt_balloons = generate_pt_balloon_textures(balloon_dir)

    for lang in ["US", "CS", "CT"]:
        lang_target = balloon_dir / lang
        if lang_target.exists():
            for fname, bdata in pt_balloons.items():
                target_f = lang_target / fname
                target_f.write_bytes(bdata)
                print(f"    [->] Injetado {fname} ({len(bdata)} bytes) em BALLOON_TEXTURE/{lang}")

    # 2. Reconstruir GDLs traduzidos
    print("[+] Reconstruindo arquivos de texto GDL (alinhamento estrito % 16 == 0)...")
    gdl_mappings = [
        (
            unpack_dir / "LETTER" / "MESSAGE_US" / "FAXEE.GDL",
            PROJECT_ROOT / "translation" / "pt-BR" / "STG" / "STG3001" / "FAXEE.json",
            [unpack_dir / "LETTER" / "MESSAGE_CS" / "FAXEC.GDL", unpack_dir / "LETTER" / "MESSAGE_CT" / "FAXET.GDL"]
        ),
        (
            unpack_dir / "SYS_MESSAGE" / "DEBUNEKO" / "MESSAGE_US" / "STG3001EE.GDL",
            PROJECT_ROOT / "translation" / "pt-BR" / "STG" / "STG3001" / "STG3001EE.json",
            [unpack_dir / "SYS_MESSAGE" / "DEBUNEKO" / "MESSAGE_CS" / "STG3001EC.GDL", unpack_dir / "SYS_MESSAGE" / "DEBUNEKO" / "MESSAGE_CT" / "STG3001ET.GDL"]
        ),
        (
            unpack_dir / "SYS_MESSAGE" / "STG3001" / "MESSAGE_US" / "WEAPONCHANGEEE.GDL",
            PROJECT_ROOT / "translation" / "pt-BR" / "STG" / "STG3001" / "WEAPONCHANGEEE.json",
            [unpack_dir / "SYS_MESSAGE" / "STG3001" / "MESSAGE_CS" / "WEAPONCHANGEEC.GDL", unpack_dir / "SYS_MESSAGE" / "STG3001" / "MESSAGE_CT" / "WEAPONCHANGEET.GDL"]
        ),
    ]

    for target_gdl, json_path, mirrors in gdl_mappings:
        orig_data = target_gdl.read_bytes()
        with open(json_path, "r", encoding="utf-8") as f:
            trans_items = json.load(f)
        orig_strings = parse_gdl(orig_data)
        new_strings = []
        for i, item in enumerate(trans_items):
            t = item.get("translation", "")
            if not t and "text" in item:
                t = item["text"]
            if not t:
                t = orig_strings[i] if i < len(orig_strings) else ""
            new_strings.append(t)

        rebuilt = rebuild_gdl(orig_data, new_strings)
        pad = (16 - (len(rebuilt) % 16)) % 16
        rebuilt += b'\x00' * pad
        target_gdl.write_bytes(rebuilt)
        print(f"    [+] {target_gdl.name} reconstruído ({len(rebuilt)} bytes, %16={len(rebuilt)%16})")

        for m in mirrors:
            if m.parent.exists():
                m.write_bytes(rebuilt)
                print(f"        [->] Propagado para {m.name}")

    # 3. Construir fonte Ninepin Bold estendida para Jeane / DEBUNEKO
    print("[+] Construindo fonte Ninepin Bold nativa com caracteres PT-BR para STG3001EE_GC.BIN...")
    debuneko_dir = unpack_dir / "SYS_MESSAGE" / "DEBUNEKO"
    us_gc = debuneko_dir / "MESSAGE_US" / "STG3001EE_GC.BIN"
    es_gc = debuneko_dir / "MESSAGE_SP" / "STG3001ES_GC.BIN"
    fr_gc = debuneko_dir / "MESSAGE_FR" / "STG3001EF_GC.BIN"

    ref_3004 = PROJECT_ROOT / "_temp_balloon" / "SYS_MESSAGE" / "TALK" / "MESSAGE_SP" / "STG3004ES_GC.BIN"
    native_gc = build_ninepin_bold_pt(us_gc, es_gc, fr_gc, ref_3004)
    us_gc.write_bytes(native_gc)
    print(f"    [+] STG3001EE_GC.BIN Ninepin Bold nativo construído ({len(native_gc)} bytes, 128x112, flag 202)")

    for sub in ["MESSAGE_CS", "MESSAGE_CT"]:
        dest_f = debuneko_dir / sub / (us_gc.name[:7] + ("C" if "CS" in sub else "T") + "_GC.BIN")
        if dest_f.parent.exists():
            dest_f.write_bytes(native_gc)
            print(f"        [->] Propagado para {dest_f.name}")

    # 4. Reempacotar contêiner RMHG
    print("[+] Reempacotando contêiner RMHG (STG3001.RSL)...")
    rsl_pack = PROJECT_ROOT / "tools" / "external" / "No-More-RSL" / "rslPack.py"
    subprocess.run([sys.executable, str(rsl_pack), str(unpack_dir), "--overwrite"], check=True, stdout=subprocess.DEVNULL)

    # 5. Recompactar STG3001.bin com ghmGcLz
    print("[+] Recompactando STG3001.bin com ghmGcLz...")
    new_rsl_data = temp_rsl.read_bytes()
    compressed_data = compress_ghm_lz(new_rsl_data)

    out_bin = PROJECT_ROOT / "data" / "translated" / "STG" / "STG3001" / "STG3001.bin"
    out_bin.parent.mkdir(parents=True, exist_ok=True)
    out_bin.write_bytes(compressed_data)
    print(f"[+] Arquivo compilado com sucesso: {out_bin} ({len(compressed_data):,} bytes)")

    steam_bin = game_dir / "STG" / "STG3001" / "STG3001.bin"
    if steam_bin.parent.exists():
        shutil.copy2(out_bin, steam_bin)
        print(f"[+] Instalado na Steam para teste imediato: {steam_bin}")

    # Limpar pasta temporária
    shutil.rmtree(temp_dir, ignore_errors=True)
    print("[OK] STG3001 traduzido e instalado com sucesso!")


if __name__ == "__main__":
    game_dir = Path(r"E:\SteamLibrary\steamapps\common\No More Heroes 2 Desperate Struggle")
    patch_stg3001(game_dir)

