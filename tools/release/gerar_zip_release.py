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
UPDATE_DIR = PROJECT_ROOT / "release" / "No_More_Heroes_2_Traducao_PTBR_Update"
UPDATE_ZIP_OUTPUT = PROJECT_ROOT / "release" / "No_More_Heroes_2_Traducao_PTBR_Update.zip"

def create_zip(src_dir: Path, zip_file: Path):
    print(f"[+] Gerando arquivo ZIP em: {zip_file}")
    if zip_file.exists():
        zip_file.unlink()

    with zipfile.ZipFile(zip_file, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(src_dir):
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(src_dir)
                zf.write(file_path, arcname)

    size_mb = zip_file.stat().st_size / (1024 * 1024)
    sha256 = hashlib.sha256(zip_file.read_bytes()).hexdigest()
    print(f"[OK] ZIP gerado com sucesso ({size_mb:.1f} MB)")
    print(f"[OK] SHA256: {sha256}")

def main():
    if not DIST_DIR.exists():
        import build_release_package
        build_release_package.main()
    create_zip(DIST_DIR, ZIP_OUTPUT)
    if UPDATE_DIR.exists():
        create_zip(UPDATE_DIR, UPDATE_ZIP_OUTPUT)

if __name__ == "__main__":
    main()

