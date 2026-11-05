# -*- coding: utf-8 -*-

import sys
import struct
import argparse
from pathlib import Path
from collections import Counter


def decompress_ghm_lz(data: bytes) -> bytes:
    if len(data) < 9:
        return data

    uncomp_sz, comp_sz = struct.unpack('<II', data[:8])
    escape_byte = data[8]

    src = 9
    src_end = min(len(data), comp_sz)
    out = bytearray()

    while src < src_end and len(out) < uncomp_sz:
        b = data[src]
        src += 1
        if b != escape_byte:
            out.append(b)
        else:
            if src >= src_end:
                break
            nxt = data[src]
            src += 1
            if nxt == escape_byte:
                out.append(escape_byte)
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

                for _ in range(length):
                    if len(out) < uncomp_sz:
                        match_pos = len(out) - dist
                        out.append(out[match_pos] if match_pos >= 0 else 0)

    return bytes(out)


def compress_ghm_lz(data: bytes) -> bytes:
    uncomp_sz = len(data)
    if uncomp_sz == 0:
        return b''

    counts = Counter(data[:min(uncomp_sz, 100000)])
    escape_byte = min(range(256), key=lambda b: counts.get(b, 0))

    out = bytearray(struct.pack('<IIB', uncomp_sz, 0, escape_byte))
    table = [-1] * 65536
    pos = 0

    while pos < uncomp_sz:
        if pos + 4 <= uncomp_sz:
            b0, b1, b2 = data[pos], data[pos+1], data[pos+2]
            h = ((b0 << 10) ^ (b1 << 5) ^ b2) & 0xFFFF
            c = table[h]
            table[h] = pos

            if c != -1:
                dist = pos - c
                if 0 < dist < 65536:
                    m = 0
                    max_m = min(uncomp_sz - pos, 1024)
                    while m < max_m and data[pos + m] == data[c + m]:
                        m += 1
                    if m >= 4:
                        out.append(escape_byte)
                        dist_val = dist - 1
                        if dist_val < 256:
                            offset_code = 0
                            dist_bytes = bytes([dist_val])
                        else:
                            offset_code = 1
                            dist_bytes = bytes([dist_val & 0xFF, (dist_val >> 8) & 0xFF])

                        len_val = m - 4
                        if len_val < 32:
                            code = (len_val << 3) | offset_code
                            extra = None
                        else:
                            code = ((len_val & 0x1F) << 3) | 4 | offset_code
                            extra = (len_val >> 5) & 0xFF

                        nxt = (code + 1) if code >= escape_byte else code
                        out.append(nxt)
                        if extra is not None:
                            out.append(extra)
                        out.extend(dist_bytes)

                        for p in range(pos + 1, min(pos + m, uncomp_sz - 2)):
                            th = ((data[p] << 10) ^ (data[p+1] << 5) ^ data[p+2]) & 0xFFFF
                            table[th] = p
                        pos += m
                        continue

        b = data[pos]
        if b == escape_byte:
            out.append(escape_byte)
            out.append(escape_byte)
        else:
            out.append(b)
        pos += 1

    comp_sz = len(out)
    struct.pack_into('<I', out, 4, comp_sz)
    return bytes(out)


def main():
    parser = argparse.ArgumentParser(description="ghm_lz — Suíte de Compressão/Descompressão ghmGcLz")
    subparsers = parser.add_subparsers(dest="command", required=True)

    dec_parser = subparsers.add_parser("decompress", help="Descompacta arquivo binário ghmGcLz")
    dec_parser.add_argument("input_file", help="Arquivo compactado de entrada")
    dec_parser.add_argument("output_file", help="Arquivo descompactado de saída")

    cmp_parser = subparsers.add_parser("compress", help="Compacta arquivo binário no formato ghmGcLz")
    cmp_parser.add_argument("input_file", help="Arquivo original de entrada")
    cmp_parser.add_argument("output_file", help="Arquivo compactado de saída")

    tst_parser = subparsers.add_parser("test", help="Testa integridade roundtrip de compressão/descompressão")
    tst_parser.add_argument("input_file", help="Arquivo original a testar")

    args = parser.parse_args()

    if args.command == "decompress":
        with open(args.input_file, 'rb') as f:
            data = f.read()
        decomp = decompress_ghm_lz(data)
        Path(args.output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(args.output_file, 'wb') as f:
            f.write(decomp)
        print(f"Descompactado: {args.input_file} ({len(data)}B) -> {args.output_file} ({len(decomp)}B)")

    elif args.command == "compress":
        with open(args.input_file, 'rb') as f:
            data = f.read()
        comp = compress_ghm_lz(data)
        Path(args.output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(args.output_file, 'wb') as f:
            f.write(comp)
        ratio = len(comp) / len(data) * 100 if len(data) > 0 else 0
        print(f"Compactado: {args.input_file} ({len(data)}B) -> {args.output_file} ({len(comp)}B, {ratio:.1f}%)")

    elif args.command == "test":
        with open(args.input_file, 'rb') as f:
            orig = f.read()
        comp = compress_ghm_lz(orig)
        decomp = decompress_ghm_lz(comp)
        match = (orig == decomp)
        print(f"Teste Roundtrip: {args.input_file}")
        print(f"  Tamanho Original:      {len(orig)} bytes")
        print(f"  Tamanho Compactado:    {len(comp)} bytes ({len(comp)/len(orig)*100:.1f}%)")
        print(f"  Tamanho Descompactado: {len(decomp)} bytes")
        print(f"  Integridade Bit-Exact: {'SUCESSO' if match else 'FALHA'}")
        if not match:
            sys.exit(1)


if __name__ == "__main__":
    main()

