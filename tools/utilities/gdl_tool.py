# -*- coding: utf-8 -*-

import os
import sys
import json
import struct
import argparse
from pathlib import Path


def parse_gdl(data: bytes):
    if len(data) < 0x34 or data[:4] != b'GDLG':
        raise ValueError("Arquivo inválido: assinatura mágica GDLG não encontrada.")

    str_count = struct.unpack('<H', data[0x22:0x24])[0]
    table_start = struct.unpack('<I', data[0x30:0x34])[0]
    pool_start = struct.unpack('<I', data[0x2C:0x30])[0]

    strings = []
    for i in range(str_count):
        rel_off = struct.unpack('<I', data[table_start + i*4 : table_start + (i+1)*4])[0]
        abs_off = pool_start + rel_off
        if abs_off >= len(data):
            strings.append("")
            continue

        end = abs_off
        while end + 1 < len(data) and not (data[end] == 0 and data[end+1] == 0):
            end += 2

        s = data[abs_off:end].decode('utf-16le', errors='replace')
        strings.append(s)

    return strings


def rebuild_gdl(orig_data: bytes, new_strings: list):
    if len(orig_data) < 0x34 or orig_data[:4] != b'GDLG':
        raise ValueError("Template inválido: assinatura mágica GDLG não encontrada.")

    str_count = struct.unpack('<H', orig_data[0x22:0x24])[0]
    table_start = struct.unpack('<I', orig_data[0x30:0x34])[0]
    pool_start = struct.unpack('<I', orig_data[0x2C:0x30])[0]

    if len(new_strings) != str_count:
        raise ValueError(f"Contagem incorreta de strings: recebido {len(new_strings)}, esperado {str_count}.")

    new_pool = bytearray()
    new_offsets = []
    for s in new_strings:
        off = len(new_pool)
        new_offsets.append(off)
        new_pool.extend(s.encode('utf-16le') + b'\x00\x00')

    out = bytearray(orig_data[:pool_start])

    for i, off in enumerate(new_offsets):
        struct.pack_into('<I', out, table_start + i*4, off)

    out.extend(new_pool)
    return bytes(out)


def export_file(gdl_path: str, json_path: str):
    with open(gdl_path, 'rb') as f:
        data = f.read()

    strings = parse_gdl(data)
    items = [{"id": i, "text": s} for i, s in enumerate(strings)]

    Path(json_path).parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

    print(f"Exportadas {len(strings)} strings de {gdl_path} -> {json_path}")


def import_file(template_gdl_path: str, json_path: str, output_gdl_path: str):
    with open(template_gdl_path, 'rb') as f:
        orig_data = f.read()

    with open(json_path, 'r', encoding='utf-8') as f:
        items = json.load(f)

    if items and isinstance(items[0], dict):
        new_strings = [item["text"] for item in sorted(items, key=lambda x: x["id"])]
    else:
        new_strings = items

    mod_data = rebuild_gdl(orig_data, new_strings)

    Path(output_gdl_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_gdl_path, 'wb') as f:
        f.write(mod_data)

    print(f"Injetadas {len(new_strings)} strings de {json_path} -> {output_gdl_path}")


def main():
    parser = argparse.ArgumentParser(description="GDL Tool — Extração e Injeção de textos de No More Heroes")
    subparsers = parser.add_subparsers(dest="command", required=True)

    exp_parser = subparsers.add_parser("export", help="Exporta strings de um arquivo .GDL para .JSON")
    exp_parser.add_argument("input_gdl", help="Caminho do arquivo .GDL original")
    exp_parser.add_argument("output_json", help="Caminho do arquivo .JSON de saída")

    imp_parser = subparsers.add_parser("import", help="Injeta strings traduzidas de .JSON em um .GDL")
    imp_parser.add_argument("template_gdl", help="Caminho do arquivo .GDL template original")
    imp_parser.add_argument("input_json", help="Caminho do arquivo .JSON com as traduções")
    imp_parser.add_argument("output_gdl", help="Caminho do novo arquivo .GDL de saída")

    args = parser.parse_args()

    if args.command == "export":
        export_file(args.input_gdl, args.output_json)
    elif args.command == "import":
        import_file(args.template_gdl, args.input_json, args.output_gdl)


if __name__ == "__main__":
    main()

