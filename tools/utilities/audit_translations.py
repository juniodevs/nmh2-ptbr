# -*- coding: utf-8 -*-
import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
TRANS_DIR = PROJECT_ROOT / "translation" / "pt-BR"

def run_translation_audit():
    print("=" * 60)
    print("1. AUDITORIA DE TRANSLATION/PT-BR")
    print("=" * 60)
    
    empty_strings = []
    identical_strings = []
    english_heuristics = []
    doublexxp_mentions = []
    total_strings = 0
    total_files = 0
    
    # Common English words that shouldn't appear frequently in Portuguese unless proper nouns
    common_en_words = set([
        "the", "and", "is", "are", "was", "were", "this", "that", "these", "those",
        "you", "your", "they", "their", "we", "our", "he", "she", "his", "her",
        "what", "when", "where", "why", "how", "who", "which",
        "with", "from", "have", "has", "had", "been", "will", "would", "could", "should",
        "kill", "death", "fight", "assassin", "ranking", "match", "mission", "ready",
        "press", "button", "attack", "slash", "charge", "target", "enemy", "boss"
    ])
    
    json_files = sorted(TRANS_DIR.rglob("*.json"))
    total_files = len(json_files)
    
    for f in json_files:
        rel_path = f.relative_to(PROJECT_ROOT)
        try:
            data = json.loads(f.read_text(encoding='utf-8'))
        except Exception as e:
            print(f"[ERRO JSON] {rel_path}: {e}")
            continue
            
        for item in data:
            total_strings += 1
            item_id = item.get("id")
            orig = item.get("original", "")
            trans = item.get("translation", "")
            
            # Check for doublexxp
            all_text = f"{orig} {trans}".lower()
            if "doublexxp" in all_text or "double" in all_text and "xxp" in all_text:
                doublexxp_mentions.append({
                    "file": str(rel_path),
                    "id": item_id,
                    "original": orig,
                    "translation": trans
                })
                
            # Check empty translation
            if not trans or not trans.strip():
                empty_strings.append({
                    "file": str(rel_path),
                    "id": item_id,
                    "original": orig,
                    "translation": trans
                })
                continue
                
            # Check translation == original
            if trans.strip() == orig.strip():
                identical_strings.append({
                    "file": str(rel_path),
                    "id": item_id,
                    "original": orig,
                    "translation": trans
                })
                continue
                
            # English heuristic: check if translation looks untranslated or has high ratio of English words
            words = re.findall(r'[a-zA-Z]+', trans.lower())
            if len(words) >= 3:
                en_matches = [w for w in words if w in common_en_words]
                if len(en_matches) >= 2 and (len(en_matches) / len(words) >= 0.4):
                    english_heuristics.append({
                        "file": str(rel_path),
                        "id": item_id,
                        "original": orig,
                        "translation": trans,
                        "en_words": en_matches
                    })

    print(f"Total de arquivos JSON analisados: {total_files}")
    print(f"Total de strings: {total_strings}")
    print(f"Strings Vazias: {len(empty_strings)}")
    print(f"Strings Idênticas (original == translation): {len(identical_strings)}")
    print(f"Suspeitas de Inglês por heurística: {len(english_heuristics)}")
    print(f"Menções a DoubleXXP: {len(doublexxp_mentions)}")
    
    print("\n--- DETALHAMENTO DE STRINGS VAZIAS ---")
    for s in empty_strings:
        print(f"[{s['file']} | ID {s['id']}] Orig: '{s['original']}'")

    print("\n--- DETALHAMENTO DE STRINGS IDÊNTICAS ---")
    for s in identical_strings:
        print(f"[{s['file']} | ID {s['id']}] Orig/Trans: '{s['original']}'")

    print("\n--- DETALHAMENTO DE SUSPEITAS DE INGLÊS ---")
    for s in english_heuristics:
        print(f"[{s['file']} | ID {s['id']}] Palavras: {s['en_words']}\n   Orig:  {s['original']}\n   Trans: {s['translation']}")

if __name__ == "__main__":
    run_translation_audit()
