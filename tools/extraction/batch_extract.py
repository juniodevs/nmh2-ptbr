# -*- coding: utf-8 -*-

import os
import sys
import json
import shutil
import struct
import argparse
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "tools" / "external" / "No-More-RSL"))

from tools.extraction.ghm_lz import decompress_ghm_lz
from tools.utilities.gdl_tool import parse_gdl


def is_ghm_lz(data: bytes) -> bool:
    if len(data) < 9:
        return False
    uncomp_sz, comp_sz = struct.unpack('<II', data[:8])
    return comp_sz == len(data) and uncomp_sz > comp_sz


def extract_archive(archive_path: Path, temp_work_dir: Path) -> Path:
    with open(archive_path, 'rb') as f:
        data = f.read()

    if is_ghm_lz(data):
        decomp_data = decompress_ghm_lz(data)
    else:
        decomp_data = data

    if not decomp_data.startswith(b'RMHG'):
        raise ValueError(f"Arquivo {archive_path.name} não é um contêiner RMHG válido.")

    temp_rsl = temp_work_dir / f"{archive_path.stem}.RSL"
    with open(temp_rsl, 'wb') as f:
        f.write(decomp_data)

    unpack_dir = temp_work_dir / archive_path.stem
    if unpack_dir.exists():
        shutil.rmtree(unpack_dir)

    rsl_extract_script = PROJECT_ROOT / "tools" / "external" / "No-More-RSL" / "rslExtract.py"
    subprocess.run([sys.executable, str(rsl_extract_script), str(temp_rsl)], check=True, stdout=subprocess.DEVNULL)

    return unpack_dir


def process_gdl_file(gdl_path: Path, rel_category: str, archive_name: str, manifest: list):
    with open(gdl_path, 'rb') as f:
        gdl_data = f.read()

    strings = parse_gdl(gdl_data)
    if not strings:
        return

    out_orig_dir = PROJECT_ROOT / "data" / "extracted" / "texts" / rel_category / archive_name
    out_orig_dir.mkdir(parents=True, exist_ok=True)
    orig_json_path = out_orig_dir / f"{gdl_path.stem}.json"

    orig_list = [{"id": i, "text": s} for i, s in enumerate(strings)]
    with open(orig_json_path, 'w', encoding='utf-8') as f:
        json.dump(orig_list, f, ensure_ascii=False, indent=2)

    out_trans_dir = PROJECT_ROOT / "translation" / "pt-BR" / rel_category / archive_name
    out_trans_dir.mkdir(parents=True, exist_ok=True)
    trans_json_path = out_trans_dir / f"{gdl_path.stem}.json"

    existing_trans = {}
    if trans_json_path.exists():
        try:
            with open(trans_json_path, 'r', encoding='utf-8') as f:
                old_data = json.load(f)
                for item in old_data:
                    existing_trans[item["id"]] = item.get("translation", "")
        except:
            pass

    trans_list = []
    for i, s in enumerate(strings):
        trans_list.append({
            "id": i,
            "original": s,
            "translation": existing_trans.get(i, "")
        })

    with open(trans_json_path, 'w', encoding='utf-8') as f:
        json.dump(trans_list, f, ensure_ascii=False, indent=2)

    manifest.append({
        "category": rel_category,
        "archive": archive_name,
        "gdl_name": gdl_path.name,
        "string_count": len(strings),
        "orig_json": str(orig_json_path.relative_to(PROJECT_ROOT)),
        "trans_json": str(trans_json_path.relative_to(PROJECT_ROOT)),
    })


def main():
    parser = argparse.ArgumentParser(description="Extração em lote de textos de No More Heroes 2")
    parser.add_argument("--game-dir", "-g", default=r"E:\SteamLibrary\steamapps\common\No More Heroes 2 Desperate Struggle",
                        help="Diretório de instalação do jogo")
    parser.add_argument("--filter", "-f", default=None,
                        help="Filtro opcional de categoria (ex: 'PJTutorial', 'Demo', 'PJSimplMes')")
    parser.add_argument("--limit", "-l", type=int, default=0,
                        help="Limite de arquivos a processar (0 para ilimitado)")
    args = parser.parse_args()

    game_dir = Path(args.game_dir)
    if not game_dir.exists():
        print(f"Erro: Diretório do jogo não encontrado: {game_dir}")
        sys.exit(1)

    temp_dir = PROJECT_ROOT / "data" / "extracted" / "_temp_batch"
    temp_dir.mkdir(parents=True, exist_ok=True)

    manifest = []
    processed_count = 0

    print("=== INICIANDO EXTRAÇÃO EM LOTE DE TEXTOS ===")
    print(f"Diretório do Jogo: {game_dir}")
    if args.filter:
        print(f"Filtro ativo: {args.filter}")

    all_files = []
    for root, dirs, files in os.walk(game_dir):
        for file in sorted(files):
            p = Path(root) / file
            rel = p.relative_to(game_dir)
            if args.filter and not str(rel).lower().startswith(args.filter.lower()):
                continue
            all_files.append(p)

    for p in all_files:
        try:
            with open(p, 'rb') as f:
                header = f.read(16)
        except:
            continue

        try:
            with open(p, 'rb') as f:
                content = f.read()
            if b'GDLG' not in content:
                continue
        except:
            continue

        rel = p.relative_to(game_dir)
        category = rel.parts[0] if len(rel.parts) > 1 else "Root"
        archive_name = p.name

        print(f"\n[+] Processando: {rel} ({len(content)} bytes)...")
        try:
            unpacked_dir = extract_archive(p, temp_dir)
        except Exception as e:
            print(f"    [-] Falha ao desempacotar {p.name}: {e}")
            continue

        gdl_files = list(unpacked_dir.rglob("*.GDL"))
        english_gdls = [g for g in gdl_files if "EE" in g.stem.upper() or "EEN" in g.stem.upper() or "MESSAGE_US" in str(g).upper()]
        selected_gdls = english_gdls if english_gdls else gdl_files

        print(f"    Encontrados {len(selected_gdls)} arquivos GDL de interesse.")
        for gdl in selected_gdls:
            process_gdl_file(gdl, category, p.stem, manifest)
            print(f"    -> Exportado: {gdl.name}")

        processed_count += 1
        if unpacked_dir.exists():
            shutil.rmtree(unpacked_dir, ignore_errors=True)
        temp_rsl = temp_dir / f"{p.stem}.RSL"
        if temp_rsl.exists():
            temp_rsl.unlink(missing_ok=True)

        if args.limit > 0 and processed_count >= args.limit:
            print(f"\nLimite de {args.limit} arquivos atingido.")
            break

    manifest_path = PROJECT_ROOT / "data" / "extracted" / "texts" / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    total_strings = sum(m["string_count"] for m in manifest)
    print("\n=== RESUMO DA EXTRAÇÃO EM LOTE ===")
    print(f"Arquivos processados: {processed_count}")
    print(f"Arquivos GDL exportados: {len(manifest)}")
    print(f"Total de strings extraídas: {total_strings}")
    print(f"Manifesto salvo em: {manifest_path}")


if __name__ == "__main__":
    main()
