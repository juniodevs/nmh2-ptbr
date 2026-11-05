# -*- coding: utf-8 -*-

import os
import sys
import time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools.reinsertion.batch_repack import repack_archive

GAME_DIR = Path(r"E:\SteamLibrary\steamapps\common\No More Heroes 2 Desperate Struggle")

def process_one(rel_path: str):
    try:
        t0 = time.time()
        repack_archive(rel_path, GAME_DIR, install=True)
        return rel_path, True, time.time() - t0, None
    except Exception as e:
        return rel_path, False, 0, str(e)

def main():
    demo_dirs = sorted([d.name for d in (PROJECT_ROOT / "translation" / "pt-BR" / "Demo").iterdir() if d.is_dir()])
    tasks = [f"Demo/{name}.BIN" for name in demo_dirs]
    
    # Also add tutorials and movies
    tasks.append("PJTutorial/PJTuto_ETC.RSL")
    tasks.append("PJTutorial/PJTuto_GYN.RSL")
    tasks.append("PJTutorial/PJTuto_SKE.RSL")
    tasks.append("PJSimplMes/PJSimplMes.RSL")
    for m in ["mv0000", "mv0001", "mv0004", "mv0007"]:
        tasks.append(f"Movie/{m}.RSL")

    print(f"Iniciando reconstrução de {len(tasks)} arquivos com a nova fonte TrueType...")
    start_time = time.time()

    completed = 0
    failed = 0

    with ProcessPoolExecutor(max_workers=6) as executor:
        futures = {executor.submit(process_one, t): t for t in tasks}
        for future in as_completed(futures):
            target = futures[future]
            rel_path, ok, duration, err = future.result()
            completed += 1
            if ok:
                print(f"[{completed}/{len(tasks)}] OK ({duration:.1f}s): {rel_path}")
            else:
                failed += 1
                print(f"[{completed}/{len(tasks)}] ERRO: {rel_path} -> {err}")

    total_time = time.time() - start_time
    print(f"\nFinalizado em {total_time:.1f}s! Sucesso: {completed - failed}, Falhas: {failed}")

if __name__ == "__main__":
    main()

