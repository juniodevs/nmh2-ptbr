# -*- coding: utf-8 -*-

import os
import sys
import struct
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

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

ALL_PORTUGUESE_CHARS = (
    " !\"#$%&'()*+,-./0123456789:;<=>?@"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`"
    "abcdefghijklmnopqrstuvwxyz{|}~"
    "áàâãéêíóôõúüçÁÀÂÃÉÊÍÓÔÕÚÜÇ"
    "ªº¡¿①"
)

def build_strimag_from_ttf(ttf_path: str, font_name="DFUDMaruGothic-W4", pt_size=38, aspect_scale=0.65, extra_chars=None) -> bytes:
    font = ImageFont.truetype(ttf_path, pt_size)
    ascent, descent = font.getmetrics()
    baseline_2x = ascent
    BASELINE_1X = 17

    char_set = set(ALL_PORTUGUESE_CHARS)
    if extra_chars:
        for c in extra_chars:
            if ord(c) >= 32 and c not in ('\r', '\n', '\t'):
                char_set.add(c)

    rendered_glyphs = []
    for ch in sorted(char_set):
        code = ord(ch)
        if ch == ' ':
            space_adv = 12 if "VCR" in Path(ttf_path).name.upper() else 10
            rendered_glyphs.append({
                'code': code, 'ch': ch, 'w_1x': space_adv, 'h_1x': 17,
                'xoff': 0, 'yoff': 0, 'xadv': space_adv, 'bmp2x': None
            })
            continue

        bbox = font.getbbox(ch)
        raw_w = max(1, bbox[2] - bbox[0])
        raw_h = max(1, bbox[3] - bbox[1])
        top_2x = bbox[1]
        bot_2x = bbox[3]

        pad_x = 4
        pad_y = 4
        img_temp = Image.new('L', (raw_w + pad_x * 2, raw_h + pad_y * 2), 0)
        draw_temp = ImageDraw.Draw(img_temp)
        draw_temp.text((pad_x - bbox[0], pad_y - bbox[1]), ch, font=font, fill=255)

        scaled_w = max(2, int(img_temp.width * aspect_scale))
        img_scaled = img_temp.resize((scaled_w, img_temp.height), Image.Resampling.LANCZOS)

        s_bbox = img_scaled.getbbox()
        if not s_bbox:
            s_bbox = (0, 0, 4, 4)
        cropped = img_scaled.crop(s_bbox)

        w_2x = cropped.width
        h_2x = cropped.height
        w_1x = max(1, (w_2x + 1) // 2)
        h_1x = max(1, (h_2x + 1) // 2)

        desc_2x = max(0, bot_2x - baseline_2x)
        desc_1x = (desc_2x + 1) // 2

        if desc_1x > 0:
            yoff = max(0, BASELINE_1X + desc_1x - h_1x)
        else:
            yoff = max(0, BASELINE_1X - h_1x)

        if ch in ('M', 'W', 'm', 'w'):
            xadv = max(10, w_1x)
        elif ch in ('!', ':', '.', ',', ';', '|', 'i', 'l', "'"):
            xadv = max(6, w_1x + 2)
        else:
            xadv = max(10, w_1x + 1)

        xoff = max(0, (xadv - w_1x) // 2)

        arr = list(cropped.getdata())
        bmp2x = [arr[r * w_2x : (r + 1) * w_2x] for r in range(h_2x)]

        rendered_glyphs.append({
            'code': code, 'ch': ch, 'w_1x': w_1x, 'h_1x': h_1x,
            'xoff': xoff, 'yoff': yoff, 'xadv': xadv,
            'w_2x': w_2x, 'h_2x': h_2x, 'bmp2x': bmp2x
        })

    tex_w = 128
    tex_w_2x = tex_w * 2

    cur_x_2x = 4
    cur_y_2x = 4
    row_h_2x = 0

    for g in rendered_glyphs:
        if not g['bmp2x']:
            g['x_1x'] = 0
            g['y_1x'] = 0
            continue

        gw_2x = g['w_2x']
        gh_2x = g['h_2x']

        if cur_x_2x + gw_2x + 4 >= tex_w_2x:
            cur_x_2x = 4
            cur_y_2x += row_h_2x + 4
            row_h_2x = 0

        g['x_1x'] = cur_x_2x // 2
        g['y_1x'] = cur_y_2x // 2
        g['x_2x'] = cur_x_2x
        g['y_2x'] = cur_y_2x

        cur_x_2x += gw_2x + 4
        row_h_2x = max(row_h_2x, gh_2x)

    total_h_2x = cur_y_2x + row_h_2x + 8
    tex_h = ((total_h_2x + 1) // 2 + 3) & ~3
    tex_h_2x = tex_h * 2

    canvas = [[0 for _ in range(tex_w_2x)] for _ in range(tex_h_2x)]
    for g in rendered_glyphs:
        bmp = g['bmp2x']
        if not bmp:
            continue
        gx = g['x_2x']
        gy = g['y_2x']
        for r in range(len(bmp)):
            for c in range(len(bmp[r])):
                if gy + r < tex_h_2x and gx + c < tex_w_2x:
                    canvas[gy + r][gx + c] = bmp[r][c]

    char_cnt = len(rendered_glyphs)
    hdr = bytearray(0xA0)
    hdr[0:8] = b'STRIMAG2'
    struct.pack_into('>IIIIII', hdr, 8, 0, 0x1C, 0, 0, char_cnt, 1)
    name_bytes = font_name.encode('latin-1')[:31]
    hdr[0x20 : 0x20 + len(name_bytes)] = name_bytes
    struct.pack_into('>I', hdr, 0x60, 20)

    rendered_glyphs.sort(key=lambda item: item['code'])
    tbl = bytearray()
    for g in rendered_glyphs:
        code = g['code']
        page = 0x0100
        id2 = (code & 0xFF) << 8
        tbl.extend(struct.pack('>10H',
            code, g['x_1x'], g['y_1x'], g['w_1x'], g['h_1x'],
            g['xoff'], g['yoff'], g['xadv'], page, id2
        ))

    pad_len = ((len(hdr) + len(tbl) + 31) & ~31) - (len(hdr) + len(tbl))
    tbl_padding = b'\x00' * pad_len

    tex_hdr = bytearray(64)
    tex_hdr[0:8] = b'\x01\x00\x00\x00\x00\x00\x00\x01'
    struct.pack_into('>HH', tex_hdr, 8, tex_w, tex_h)
    struct.pack_into('>I', tex_hdr, 12, 0)
    struct.pack_into('>I', tex_hdr, 16, 0x40)
    struct.pack_into('>I', tex_hdr, 32, tex_h_2x)

    pix_data = encode_i8(canvas, tex_w, tex_h)
    return bytes(hdr) + bytes(tbl) + tbl_padding + bytes(tex_hdr) + bytes(pix_data)

def create_extended_strimag(ee_data: bytes, es_data=None, fr_data=None, needed_chars=None, extra_fonts=None) -> bytes:
    font_name = "DFUDMaruGothic-W4"
    if ee_data and len(ee_data) >= 0x40 and ee_data[:8] == b'STRIMAG2':
        raw_name = ee_data[32:64].split(b'\x00')[0].decode('latin-1', 'replace')
        if raw_name:
            font_name = raw_name

    search_dirs = [
        PROJECT_ROOT / "data" / "fonts",
        PROJECT_ROOT / "tools" / "fonts",
        PROJECT_ROOT,
        Path("C:/Windows/Fonts")
    ]

    ttf_candidates = [
        ("VCR_OSD_MONO_1.001.ttf", 44, 1.0),
        ("vcr_osd_mono.ttf", 44, 1.0),
        ("DFUDMaruGothic-W4.ttf", 38, 0.70),
        ("DFPUDMaruGothic-W4.ttf", 38, 0.70),
        ("DFUDMaruGothic.ttf", 38, 0.70),
        ("ZenMaruGothic-Bold.ttf", 42, 0.70),
        ("MPLUSRounded1c-Bold.ttf", 42, 0.70),
        ("segoeuib.ttf", 38, 0.65),
        ("arialbd.ttf", 38, 0.65),
        ("tahomabd.ttf", 38, 0.65)
    ]
    ttf_path = "C:/Windows/Fonts/arialbd.ttf"
    pt_size = 38
    aspect_scale = 0.65
    found = False
    for fname, pt, scale in ttf_candidates:
        for sdir in search_dirs:
            candidate = sdir / fname
            if candidate.exists():
                ttf_path = str(candidate)
                pt_size = pt
                aspect_scale = scale
                found = True
                break
        if found:
            break

    return build_strimag_from_ttf(ttf_path, font_name=font_name, pt_size=pt_size, aspect_scale=aspect_scale, extra_chars=needed_chars)
