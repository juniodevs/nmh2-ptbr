# -*- coding: utf-8 -*-

import sys
import struct
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def decode_i8(data: bytes, tex_w: int, tex_h: int):
    w = tex_w * 2
    h = tex_h * 2
    tiles_x = (w + 7) // 8
    tiles_y = (h + 3) // 4
    canvas = [[0 for _ in range(tiles_x * 8)] for _ in range(tiles_y * 4)]
    for ty in range(tiles_y):
        for tx in range(tiles_x):
            off = (ty * tiles_x + tx) * 32
            if off + 32 <= len(data):
                for in_y in range(4):
                    for in_x in range(8):
                        canvas[ty * 4 + in_y][tx * 8 + in_x] = data[off + in_y * 8 + in_x]
    return canvas


def encode_i8(canvas, tex_w: int, tex_h: int) -> bytearray:
    w = tex_w * 2
    h = tex_h * 2
    tiles_x = (w + 7) // 8
    tiles_y = (h + 3) // 4
    out = bytearray(tiles_x * tiles_y * 32)
    for ty in range(tiles_y):
        for tx in range(tiles_x):
            off = (ty * tiles_x + tx) * 32
            for in_y in range(4):
                for in_x in range(8):
                    y = ty * 4 + in_y
                    x = tx * 8 + in_x
                    if y < len(canvas) and x < len(canvas[y]):
                        out[off + in_y * 8 + in_x] = canvas[y][x]
    return out


class StrimagGlyph:
    def __init__(self, code, x, y, w, h, xoff, yoff, xadv, page=0x0100, id2=None, bitmap2x=None):
        self.code = code
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.xoff = xoff
        self.yoff = yoff
        self.xadv = xadv
        self.page = page
        self.id2 = id2 if id2 is not None else ((code & 0xFF) << 8)
        self.bitmap2x = bitmap2x


class StrimagFont:
    def __init__(self, data: bytes):
        if len(data) < 0xA0 or data[:8] != b'STRIMAG2':
            raise ValueError("Não é um arquivo STRIMAG2 válido.")
        self.raw_data = data
        self.unk1, self.hdr_sz, self.unk2, self.unk3, self.char_cnt, self.num_tex = struct.unpack(
            '>IIIIII', data[8:32]
        )
        self.font_name = data[32:64].split(b'\x00')[0].decode('latin-1')
        self.entry_sz = struct.unpack('>I', data[0x60:0x64])[0]
        if self.entry_sz != 20:
            self.entry_sz = 20

        self.glyphs = {}
        for i in range(self.char_cnt):
            entry = data[0xA0 + i*20 : 0xA0 + (i+1)*20]
            code, x, y, w, h, xoff, yoff, xadv, page, id2 = struct.unpack('>10H', entry)
            self.glyphs[code] = StrimagGlyph(code, x, y, w, h, xoff, yoff, xadv, page, id2)

        raw_tbl_end = 0xA0 + self.char_cnt * 20
        self.tex_hdr_offset = (raw_tbl_end + 31) & ~31
        tex_hdr = data[self.tex_hdr_offset : self.tex_hdr_offset + 64]
        self.tex_w, self.tex_h = struct.unpack('>HH', tex_hdr[8:12])
        self.pix_offset = self.tex_hdr_offset + 64

        pix_data = data[self.pix_offset :]
        self.canvas = decode_i8(pix_data, self.tex_w, self.tex_h)

        for g in self.glyphs.values():
            bmp = []
            for r in range(g.h * 2):
                row_pixels = []
                for c in range(g.w * 2):
                    target_y = g.y * 2 + r
                    target_x = g.x * 2 + c
                    if target_y < len(self.canvas) and target_x < len(self.canvas[target_y]):
                        row_pixels.append(self.canvas[target_y][target_x])
                    else:
                        row_pixels.append(0)
                bmp.append(row_pixels)
            g.bitmap2x = bmp

    def get_char(self, ch: str):
        return self.glyphs.get(ord(ch))


_FONT_CACHE = {}


def get_cached_fallback_fonts(font_name: str):
    if font_name in _FONT_CACHE:
        return _FONT_CACHE[font_name]

    fonts = []
    extracted_dir = PROJECT_ROOT / "data" / "extracted"
    if extracted_dir.exists():
        for p in extracted_dir.rglob("*_GC.BIN"):
            try:
                b = p.read_bytes()
                if b[:8] == b'STRIMAG2':
                    fn = b[32:64].split(b'\x00')[0].decode('latin-1')
                    if fn == font_name:
                        fonts.append(StrimagFont(b))
            except Exception:
                pass

    _FONT_CACHE[font_name] = fonts
    return fonts


def create_extended_strimag(ee_data: bytes, es_data: bytes, fr_data: bytes, needed_chars: set, extra_fonts=None) -> bytes:
    font_ee = StrimagFont(ee_data)
    font_es = StrimagFont(es_data) if es_data else None
    font_fr = StrimagFont(fr_data) if fr_data else None

    fallback_fonts = get_cached_fallback_fonts(font_ee.font_name)
    search_fonts = []
    if font_es: search_fonts.append(font_es)
    if font_fr: search_fonts.append(font_fr)
    if extra_fonts: search_fonts.extend(extra_fonts)
    search_fonts.extend(fallback_fonts)

    current_chars = set(chr(c) for c in font_ee.glyphs.keys())
    missing = needed_chars - current_chars
    print(f"Fonte '{font_ee.font_name}': {len(current_chars)} glifos existentes, faltantes: {len(missing)} -> {sorted(missing)}")

    new_glyphs = {}
    for ch in sorted(missing):
        code = ord(ch)
        src_glyph = None

        for f in search_fonts:
            if code in f.glyphs:
                src_glyph = f.glyphs[code]
                break

        if not src_glyph:
            if ch == 'X':
                w_x, h_x = 10, 17
                bmp_x = [[0 for _ in range(w_x * 2)] for _ in range(h_x * 2)]
                for r in range(h_x * 2):
                    c1 = int(r * (w_x * 2 - 3) / (h_x * 2 - 1))
                    c2 = (w_x * 2 - 3) - c1
                    for dc in range(3):
                        if 0 <= c1 + dc < w_x * 2: bmp_x[r][c1 + dc] = 255
                        if 0 <= c2 + dc < w_x * 2: bmp_x[r][c2 + dc] = 255
                src_glyph = StrimagGlyph(code, 0, 0, w_x, h_x, 1, 2, w_x + 2, bitmap2x=bmp_x)
            elif ch == '(':
                w_p, h_p = 5, 17
                bmp_p = [[0 for _ in range(w_p * 2)] for _ in range(h_p * 2)]
                for r in range(h_p * 2):
                    c = int((h_p - abs(r - h_p)) * 4 / h_p)
                    for dc in range(2):
                        if 0 <= 4 - c + dc < w_p * 2: bmp_p[r][4 - c + dc] = 255
                src_glyph = StrimagGlyph(code, 0, 0, w_p, h_p, 1, 2, w_p + 2, bitmap2x=bmp_p)
            elif ch == ')':
                w_p, h_p = 5, 17
                bmp_p = [[0 for _ in range(w_p * 2)] for _ in range(h_p * 2)]
                for r in range(h_p * 2):
                    c = int((h_p - abs(r - h_p)) * 4 / h_p)
                    for dc in range(2):
                        if 0 <= c + dc < w_p * 2: bmp_p[r][c + dc] = 255
                src_glyph = StrimagGlyph(code, 0, 0, w_p, h_p, 1, 2, w_p + 2, bitmap2x=bmp_p)
            elif ch == '_':
                w_u, h_u = 8, 17
                bmp_u = [[0 for _ in range(w_u * 2)] for _ in range(h_u * 2)]
                for r in range(h_u * 2 - 3, h_u * 2):
                    for c in range(w_u * 2):
                        bmp_u[r][c] = 255
                src_glyph = StrimagGlyph(code, 0, 0, w_u, h_u, 0, 2, w_u + 1, bitmap2x=bmp_u)
            elif ch == '|':
                w_v, h_v = 3, 17
                bmp_v = [[0 for _ in range(w_v * 2)] for _ in range(h_v * 2)]
                for r in range(h_v * 2):
                    for c in range(min(2, w_v * 2)):
                        bmp_v[r][c] = 255
                src_glyph = StrimagGlyph(code, 0, 0, w_v, h_v, 1, 2, w_v + 3, bitmap2x=bmp_v)
            elif ch == ':':
                w_cl, h_cl = 4, 17
                bmp_cl = [[0 for _ in range(w_cl * 2)] for _ in range(h_cl * 2)]
                for r in range(10, 14):
                    for c in range(2, 6):
                        bmp_cl[r][c] = 255
                for r in range(20, 24):
                    for c in range(2, 6):
                        bmp_cl[r][c] = 255
                src_glyph = StrimagGlyph(code, 0, 0, w_cl, h_cl, 1, 2, w_cl + 2, bitmap2x=bmp_cl)
            else:
                accent_patterns = {
                    'tilde': [
                        "  ######    ",
                        " ###### ##  ",
                        "###  #####  ",
                        "##   ####   ",
                        "       ##   ",
                    ],
                    'acute': [
                        "      ###   ",
                        "    ####    ",
                        "   ####     ",
                        "  ####      ",
                    ],
                    'grave': [
                        "  ###       ",
                        "   ####     ",
                        "    ####    ",
                        "     ####   ",
                    ],
                    'circ': [
                        "    ####    ",
                        "  ########  ",
                        " ###    ### ",
                        "##        ##",
                    ],
                    'cedilla': [
                        "  ### ",
                        "   ###",
                        "  ### ",
                        " ###  ",
                    ]
                }

                base_char_map = {
                    'õ': ('o', 'tilde'),
                    'ã': ('a', 'tilde'),
                    'Õ': ('O', 'tilde'),
                    'Ã': ('A', 'tilde'),
                    'ô': ('o', 'circ'),
                    'ê': ('e', 'circ'),
                    'â': ('a', 'circ'),
                    'Ô': ('O', 'circ'),
                    'Ê': ('E', 'circ'),
                    'Â': ('A', 'circ'),
                    'é': ('e', 'acute'),
                    'á': ('a', 'acute'),
                    'í': ('i', 'acute'),
                    'ó': ('o', 'acute'),
                    'ú': ('u', 'acute'),
                    'É': ('E', 'acute'),
                    'Á': ('A', 'acute'),
                    'Í': ('I', 'acute'),
                    'Ó': ('O', 'acute'),
                    'Ú': ('U', 'acute'),
                    'à': ('a', 'grave'),
                    'À': ('A', 'grave'),
                    'Ç': ('C', 'cedilla'),
                    'ç': ('c', 'cedilla'),
                }

                if ch in base_char_map:
                    base_c, acc_type = base_char_map[ch]
                    g_base = font_ee.get_char(base_c)
                    if not g_base:
                        for f in search_fonts:
                            g_base = f.get_char(base_c)
                            if g_base:
                                break
                    if g_base:
                        if acc_type == 'cedilla':
                            new_w = max(g_base.w, 8)
                            new_h = g_base.h + 4
                            new_bmp = [[0 for _ in range(new_w * 2)] for _ in range(new_h * 2)]
                            for r in range(len(g_base.bitmap2x)):
                                for c in range(min(len(g_base.bitmap2x[r]), new_w * 2)):
                                    new_bmp[r][c] = g_base.bitmap2x[r][c]
                            pat = accent_patterns['cedilla']
                            base_bottom = len(g_base.bitmap2x)
                            c_offset = max(2, (new_w * 2 - 6) // 2)
                            for pr, prow in enumerate(pat):
                                for pc, pch in enumerate(prow):
                                    if pch == '#' and base_bottom - 2 + pr < new_h * 2 and c_offset + pc < new_w * 2:
                                        new_bmp[base_bottom - 2 + pr][c_offset + pc] = 255
                            src_glyph = StrimagGlyph(code, 0, 0, new_w, new_h, g_base.xoff, g_base.yoff, g_base.xadv, bitmap2x=new_bmp)
                        else:
                            new_w = max(g_base.w, 9)
                            new_h = g_base.h + 5
                            new_bmp = [[0 for _ in range(new_w * 2)] for _ in range(new_h * 2)]
                            for r in range(len(g_base.bitmap2x)):
                                target_r = 10 + r
                                if target_r < new_h * 2:
                                    for c in range(min(len(g_base.bitmap2x[r]), new_w * 2)):
                                        new_bmp[target_r][c] = g_base.bitmap2x[r][c]
                            pat = accent_patterns[acc_type]
                            for pr, prow in enumerate(pat):
                                for pc, pch in enumerate(prow):
                                    if pch == '#' and 2 + pr < new_h * 2 and pc < new_w * 2:
                                        new_bmp[2 + pr][pc] = 255
                            src_glyph = StrimagGlyph(code, 0, 0, new_w, new_h, g_base.xoff, 2, g_base.xadv, bitmap2x=new_bmp)

        if not src_glyph:
            try:
                from PIL import Image, ImageDraw, ImageFont
                font_pil = ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf', 24)
                bbox = font_pil.getbbox(ch)
                bw = max(1, bbox[2] - bbox[0])
                bh = max(1, bbox[3] - bbox[1])
                gw = max(8, (bw + 1) // 2 + 1)
                gh = max(16, (bh + 1) // 2 + 2)
                img = Image.new('L', (gw * 2, gh * 2), 0)
                draw = ImageDraw.Draw(img)
                draw.text((1 - bbox[0], 2 - bbox[1]), ch, font=font_pil, fill=255)
                arr = list(img.getdata())
                bmp2x = [arr[r*(gw*2) : (r+1)*(gw*2)] for r in range(gh*2)]
                src_glyph = StrimagGlyph(code, 0, 0, gw, gh, 0, 2, gw, bitmap2x=bmp2x)
            except Exception as e:
                pass

        if src_glyph:
            new_glyphs[code] = StrimagGlyph(
                code=code, x=0, y=0, w=src_glyph.w, h=src_glyph.h,
                xoff=src_glyph.xoff, yoff=src_glyph.yoff, xadv=src_glyph.xadv,
                page=src_glyph.page, id2=((code & 0xFF) << 8), bitmap2x=src_glyph.bitmap2x
            )
            print(f"  [+] Injetado glifo: {repr(ch)} (U+{code:04X}) tamanho {src_glyph.w}x{src_glyph.h}")
        else:
            print(f"  [!] AVISO: Não foi possível obter o glifo: {repr(ch)} (U+{code:04X})")

    cur_x = 48
    cur_y = 84
    max_w_1x = 126

    for g in new_glyphs.values():
        if cur_x + g.w >= max_w_1x:
            cur_x = 0
            cur_y = 112
        g.x = cur_x
        g.y = cur_y
        cur_x += g.w + 1

    tex_w = 126
    tex_h = 130 if cur_y >= 112 else max(font_ee.tex_h, 102)

    tiles_x = (tex_w * 2 + 7) // 8
    tiles_y = (tex_h * 2 + 3) // 4
    new_canvas = [[0 for _ in range(tiles_x * 8)] for _ in range(tiles_y * 4)]

    for g in font_ee.glyphs.values():
        if g.bitmap2x:
            for r in range(len(g.bitmap2x)):
                for c in range(len(g.bitmap2x[r])):
                    ty = g.y * 2 + r
                    tx = g.x * 2 + c
                    if ty < len(new_canvas) and tx < len(new_canvas[ty]):
                        new_canvas[ty][tx] = g.bitmap2x[r][c]

    for g in new_glyphs.values():
        if g.bitmap2x:
            for r in range(len(g.bitmap2x)):
                for c in range(len(g.bitmap2x[r])):
                    ty = g.y * 2 + r
                    tx = g.x * 2 + c
                    if ty < len(new_canvas) and tx < len(new_canvas[ty]):
                        new_canvas[ty][tx] = g.bitmap2x[r][c]

    all_glyphs = list(font_ee.glyphs.values()) + list(new_glyphs.values())

    new_pixels = encode_i8(new_canvas, tex_w, tex_h)

    out = bytearray()
    out.extend(b'STRIMAG2')
    out.extend(struct.pack('>IIIIII', 0, 28, 0, 0, len(all_glyphs), 1))
    fn_bytes = font_ee.font_name.encode('latin-1').ljust(32, b'\x00')
    out.extend(fn_bytes)
    out.extend(b'\x00' * 32)
    out.extend(struct.pack('>I', 20))
    out.extend(b'\x00' * 60)

    for g in all_glyphs:
        out.extend(struct.pack('>10H', g.code, g.x, g.y, g.w, g.h, g.xoff, g.yoff, g.xadv, g.page, g.id2))

    while len(out) % 32 != 0:
        out.append(0)

    tex_hdr = bytearray(64)
    struct.pack_into('>II', tex_hdr, 0, 0x01000000, 1)
    struct.pack_into('>HH', tex_hdr, 8, tex_w, tex_h)
    struct.pack_into('>I', tex_hdr, 12, 0)
    struct.pack_into('>I', tex_hdr, 16, 64)
    struct.pack_into('>I', tex_hdr, 32, 0xCA)
    out.extend(tex_hdr)

    out.extend(new_pixels)

    while len(out) % 32 != 0:
        out.append(0)

    print(f"[OK] STRIMAG2 reconstruído com {len(all_glyphs)} glifos! Textura Wii GX_TF_I8: {tex_w}x{tex_h} ({len(out)} bytes)")
    return bytes(out)


if __name__ == "__main__":
    print("Módulo patch_strimag carregado com codec oficial Nintendo Wii GX_TF_I8 e fallback global.")
