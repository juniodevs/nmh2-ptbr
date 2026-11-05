# -*- coding: utf-8 -*-

import os
import sys
import shutil
import zipfile
import hashlib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DIST_DIR = PROJECT_ROOT / "release" / "No_More_Heroes_2_Traducao_PTBR_Beta"
ZIP_OUTPUT = PROJECT_ROOT / "release" / "No_More_Heroes_2_Traducao_PTBR_Beta.zip"

def create_zip():
    print(f"[+] Gerando arquivo ZIP em: {ZIP_OUTPUT}")
    if ZIP_OUTPUT.exists():
        ZIP_OUTPUT.unlink()

    with zipfile.ZipFile(ZIP_OUTPUT, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(DIST_DIR):
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(DIST_DIR)
                zf.write(file_path, arcname)

    size_mb = ZIP_OUTPUT.stat().st_size / (1024 * 1024)
    sha256 = hashlib.sha256(ZIP_OUTPUT.read_bytes()).hexdigest()
    print(f"[OK] ZIP gerado com sucesso ({size_mb:.1f} MB)")
    print(f"[OK] SHA256: {sha256}")

def main():
    if not DIST_DIR.exists():
        import build_release_package
        build_release_package.main()
    create_zip()

if __name__ == "__main__":
    main()
