# -*- coding: utf-8 -*-

import sys
import shutil
from pathlib import Path

import os

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_env_exe = os.environ.get("GAME_EXE_OVERRIDE")
if _env_exe:
    GAME_EXE = Path(_env_exe)
    BACKUP_EXE = GAME_EXE.parent / ".backup" / "nmh2.exe"
else:
    GAME_EXE = Path(r"E:\SteamLibrary\steamapps\common\No More Heroes 2 Desperate Struggle\nmh2.exe")
    BACKUP_EXE = PROJECT_ROOT / "backups" / "nmh2.exe.bak"

STRING_PATCHES = [
    (b'SELECT DIFFICULTY\x00\x00\x00', b'ESCOLHA O NIVEL\x00\x00\x00\x00\x00'),
    (b'SWEET\x00\x00\x00', b'SUAVE\x00\x00\x00'),
    (b'MILD\x00\x00\x00\x00', b'NORMAL\x00\x00'),
    (b'BITTER\x00\x00', b'DIFICIL\x00'),
    (b'PERFECT FOR BEGINNERS.\x00\x00', b'IDEAL PARA INICIANTES.\x00\x00'),
    (b'MANY STRONG MEN AWAIT YOU.\x00\x00', b'MUITOS INIMIGOS TE ESPERAM.\x00'),
    (b'EXTREMELY DIFFICULT.\x00\x00\x00\x00', b'EXTREMAMENTE DIFICIL.\x00\x00\x00'),
    (b'FOR BEGINNER PLAYERS.\x00\x00\x00', b'PROS INICIANTES.\x00\x00\x00\x00\x00\x00\x00\x00'),
    (b'FOR NORMAL PLAYERS.\x00', b'PROS JOGADORES RAIZ\x00'),
    (b'FOR EXPERT PLAYERS.\x00', b'PROS MAIS INSANOS.\x00\x00'),
    (b'NEW GAME\x00\x00\x00\x00', b'NOVO JOGO\x00\x00\x00'),
    (b'LOAD GAME\x00\x00\x00', b'CARREGAR\x00\x00\x00\x00'),
    (b'DEATH MATCH\x00', b'MATA-MATA\x00\x00\x00'),
    (b'OPTION\x00\x00', b'OPCOES\x00\x00'),
    (b'QUIT\x00\x00\x00\x00', b'SAIR\x00\x00\x00\x00'),
    (b'RETRY\x00\x00\x00', b'TENTAR\x00\x00'),
    (b'PRESS\x00\x00\x00', b'APERTE\x00\x00'),

    (b'JOB MISSION\x00', b'BICOS CLT\x00\x00\x00'),
    (b'REVENGE MISSION\x00', b'MISSAO VINGANCA\x00'),
    (b'SIDE JOB\x00\x00\x00\x00', b'BICOS CLT\x00\x00\x00'),
    (b'SIDE JOB 01\x00', b'BICO CLT 01\x00'),
    (b'SIDE JOB 02\x00', b'BICO CLT 02\x00'),
    (b'SIDE JOB 03\x00', b'BICO CLT 03\x00'),
    (b'SIDE JOB 04\x00', b'BICO CLT 04\x00'),
    (b'SIDE JOB 05\x00', b'BICO CLT 05\x00'),
    (b'SIDE JOB 06\x00', b'BICO CLT 06\x00'),
    (b'SIDE JOB 07\x00', b'BICO CLT 07\x00'),
    (b'SIDE JOB 08\x00', b'BICO CLT 08\x00'),
    (b'JOB MISSION 01\x00\x00', b'BICO CLT 01\x00\x00\x00\x00\x00'),
    (b'JOB MISSION 02\x00\x00', b'BICO CLT 02\x00\x00\x00\x00\x00'),
    (b'JOB MISSION 03\x00\x00', b'BICO CLT 03\x00\x00\x00\x00\x00'),
    (b'JOB MISSION 04\x00\x00', b'BICO CLT 04\x00\x00\x00\x00\x00'),
    (b'JOB MISSION 05\x00\x00', b'BICO CLT 05\x00\x00\x00\x00\x00'),
    (b'JOB MISSION 06\x00\x00', b'BICO CLT 06\x00\x00\x00\x00\x00'),
    (b'JOB MISSION 07\x00\x00', b'BICO CLT 07\x00\x00\x00\x00\x00'),
    (b'JOB MISSION 08\x00\x00', b'BICO CLT 08\x00\x00\x00\x00\x00'),

    (b'BUG OUT\x00', b'INSETOS\x00'),
    (b'LAY THE PIPE\x00\x00\x00\x00', b'DESENTUP. BOSTA\x00'),
    (b'COCONUT GRABBER\x00', b'CATAR COCOS\x00\x00\x00\x00\x00'),
    (b'MAN THE MEAT\x00\x00\x00\x00', b'CHURRASQUEIRO\x00\x00\x00'),
    (b'TILE IN STYLE\x00\x00\x00', b'AZULEJISTA CLT\x00\x00'),
    (b'GETTING TRASHED\x00', b'CATADOR DE LIXO\x00'),
    (b'STINGS SO GOOD\x00\x00', b'ESCORPIOES CLT\x00\x00'),

    (b'STATUS\x00\x00', b'STATUS\x00\x00'),
    (b'DATA\x00\x00\x00\x00', b'DADOS\x00\x00\x00'),
    (b'CONFIG\x00\x00', b'AJUSTES\x00'),
    (b'CLOSE\x00\x00\x00', b'FECHAR\x00\x00'),
    (b'HEALTH\x00\x00', b'SAUDE\x00\x00\x00'),
    (b'ELECTRICITY\x00', b'BATERIA\x00\x00\x00\x00\x00'),
    (b'TENSION GAUGE\x00\x00\x00', b'BARRA DE TENSAO\x00'),
    (b'STAMINA\x00', b'ENERGIA\x00'),
    (b'MUSCLE\x00\x00', b'FORCA\x00\x00\x00'),
    (b'COSTUME\x00', b'ROUPAS\x00\x00'),
    (b'COLLECTION\x00\x00', b'COLECAO\x00\x00\x00\x00\x00'),
    (b'KILL COUNT\x00\x00', b'ABATES\x00\x00\x00\x00\x00\x00'),
    (b'SUBTITLES\x00\x00\x00', b'LEGENDAS\x00\x00\x00\x00'),
    (b'MINIMAP\x00', b'RADAR\x00\x00\x00'),
    (b'INVERT CAMERA X\x00', b'INVERTER EIXO X\x00'),
    (b'INVERT CAMERA Y\x00', b'INVERTER EIXO Y\x00'),
    (b'DONE\x00\x00\x00\x00', b'PRONTO\x00\x00'),
    (b'SOLD OUT\x00\x00\x00\x00', b'ESGOTADO\x00\x00\x00\x00'),
    (b'T-SHIRT\x00', b'CAMISA\x00\x00'),
    (b'JACKET\x00\x00', b'JAQUETA\x00'),
    (b'PANTS\x00\x00\x00', b'CALCA\x00\x00\x00'),
    (b'SUNGLASSES\x00\x00', b'OCULOS\x00\x00\x00\x00\x00\x00'),
    (b'WRISTBAND\x00\x00\x00', b'PULSEIRA\x00\x00\x00\x00'),
    (b'BELT\x00\x00\x00\x00', b'CINTO\x00\x00\x00'),
    (b'SHOES\x00\x00\x00', b'TENIS\x00\x00\x00'),
    (b'TELEVISION\x00\x00', b'TELEVISAO\x00\x00\x00'),
    (b'BJ 5 VIDEO\x00\x00', b'VICKZ_JOGA\x00\x00'),
    (b'E3 TRAILER 2009\x00', b'JUNIODEVS TRAD.\x00'),
    (b'CLOSET\x00\x00', b'ARMARIO\x00'),
    (b'TRAINING\x00\x00\x00\x00', b'TREINO\x00\x00\x00\x00\x00\x00'),
    (b'ARE YOU READY?\x00\x00', b'TUDO PRONTO?\x00\x00\x00\x00'),
    (b'THANK YOU!\x00\x00', b'VALEU MESMO\x00'),
    (b'CHECK POINT\x00', b'CHECKPOINT\x00\x00'),

    (b'CREATE NEW FILE?\x00\x00\x00\x00', b'CRIAR NOVO ARQUIVO?\x00'),
    (b'OVERWRITE?\x00\x00', b'SUBSTITUIR?\x00'),
    (b'SAVE OK\x00', b'SALVO!\x00\x00'),
    (b'CONTINUE?\x00\x00\x00', b'CONTINUAR?\x00\x00'),
    (b'GAME OVER\x00\x00\x00', b'FIM DE JOGO\x00'),
    (b'STAGE CLEAR\x00', b'FASE LIMPA!\x00'),
    (b'NOW LOADING\x00', b'CARREGANDO.\x00'),

    (b'PRESS ~200 TO START\x00', b'APERTE ~200 PRA IR\x00\x00'),
    (b'RESUME\x00\x00', b'VOLTAR\x00\x00'),
    (b'TIME OVER\x00\x00\x00', b'ACABOU!\x00\x00\x00\x00\x00'),
    (b'CLEAR TIME\x00\x00', b'TEMPO TOTAL\x00'),
    (b'MONEY\x00\x00\x00', b'GRANA\x00\x00\x00'),
    (b'QUIT GAME\x00\x00\x00', b'FECHAR JOGO\x00'),
    (b'TITLE SCREEN\x00\x00\x00\x00', b'TELA DE TITULO\x00\x00'),
    (b'PROCEED?\x00\x00\x00\x00', b'CONTINUAR?\x00\x00'),

    (b'UNSAVED PROGRESS WILL BE LOST\x00\x00\x00', b'PROGRESSO NAO SALVO SE PERDERA\x00\x00'),
    (b'YES\x00', b'SIM\x00'),
    (b'NO \x00', b'NAO\x00'),
    (b'\x00NO\x00\x00', b'\x00NAO\x00'),

    (b'CHANGE?\x00', b'TROCAR?\x00'),
    (b'BUY?\x00\x00\x00\x00', b'COMPRA?\x00'),
    (b'SHELF\x00\x00\x00', b'ESTANTE\x00'),
    (b'MAGAZINE\x00\x00\x00\x00', b'REVISTAS\x00\x00\x00\x00'),
    (b'BJ 5 GAME\x00\x00\x00', b'JOGO BJ 5\x00\x00\x00'),
    (b'PLAY\x00\x00\x00\x00', b'BRINCAR\x00'),
    (b'JUMP\x00\x00\x00\x00', b'PULAR\x00\x00\x00'),
    (b'STRETCH\x00', b'ALONGAR\x00'),
    (b'MASSAGE\x00', b'MASSAGE\x00'),
    (b'FEED\x00\x00\x00\x00', b'COMIDA\x00\x00'),
    (b'REGULAR    \x00', b'PADRAO     \x00'),
    (b'MOOD\x00\x00\x00\x00', b'HUMOR\x00\x00\x00'),
    (b'EXIT\x00\x00\x00\x00', b'SAIR\x00\x00\x00\x00'),
]


def apply_patch():
    if not GAME_EXE.exists():
        print(f"Erro: nmh2.exe não encontrado em {GAME_EXE}")
        return False

    BACKUP_EXE.parent.mkdir(parents=True, exist_ok=True)
    if not BACKUP_EXE.exists():
        shutil.copy2(GAME_EXE, BACKUP_EXE)
        print(f"[Backup] Backup original salvo em: {BACKUP_EXE}")
    else:
        print(f"[Backup] Backup original já preservado em: {BACKUP_EXE}")

    with open(BACKUP_EXE, 'rb') as f:
        data = bytearray(f.read())

    applied_count = 0
    verbose = "--verbose" in sys.argv
    for orig, rep in STRING_PATCHES:
        assert len(orig) == len(rep), f"Tamanhos diferentes: {orig} ({len(orig)}) vs {rep} ({len(rep)})"
        pos = data.find(orig, 0x632500)
        if pos != -1 and pos < 0x634000:
            data[pos : pos + len(orig)] = rep
            if verbose:
                print(f"  [+] 0x{pos:X}: {orig[:16].decode('latin-1', 'replace')} -> {rep[:16].decode('latin-1', 'replace')}")
            applied_count += 1
        elif verbose:
            print(f"  [!] String não localizada na tabela de texto: {orig[:16].decode('latin-1', 'replace')}")

    cancel_count = 0
    pos = 0x632500
    while True:
        pos = data.find(b':CANCEL', pos)
        if pos == -1 or pos >= 0x634000:
            break
        data[pos : pos + 7] = b':VOLTAR'
        cancel_count += 1
        if verbose:
            print(f"  [+] 0x{pos:X}: :CANCEL -> :VOLTAR")
        pos += 7

    prompt_patches = [
        (b':SELECT    ', b':ESCOLHER  '),
        (b':SELECT   ', b':ESCOLHER '),
        (b'   ~219:TURN   ~205:TURN RESET\x00\x00', b'   ~219:GIRAR  ~205:RESET GIRO\x00\x00'),
    ]
    for s_orig, s_rep in prompt_patches:
        assert len(s_orig) == len(s_rep), f"Tamanhos diferentes: {s_orig} ({len(s_orig)}) vs {s_rep} ({len(s_rep)})"
        pos = 0x632500
        while True:
            pos = data.find(s_orig, pos)
            if pos == -1 or pos >= 0x634000:
                break
            data[pos : pos + len(s_orig)] = s_rep
            if verbose:
                print(f"  [+] 0x{pos:X}: {s_orig} -> {s_rep}")
            pos += len(s_orig)

    import struct
    map_pointers = [0x60D6A8, 0x60E348, 0x14CD79]
    for p_off in map_pointers:
        old_val = struct.unpack('<I', data[p_off : p_off + 4])[0]
        if old_val == 0xA33CA8:
            struct.pack_into('<I', data, p_off, 0xA36684)
            if verbose:
                print(f"  [+] Redirecionado ponteiro MAP -> MAPA em 0x{p_off:X}")

    orig_len = BACKUP_EXE.stat().st_size
    assert len(data) == orig_len, f"ERRO CRITICO: Tamanho do executavel foi alterado! {len(data)} != {orig_len}"

    with open(GAME_EXE, 'wb') as f:
        f.write(data)

    print(f"[OK] Executável nmh2.exe atualizado ({applied_count}/{len(STRING_PATCHES)} textos de menu e opções traduzidos).")
    return True


def restore_backup():
    if not BACKUP_EXE.exists():
        print(f"Erro: Backup {BACKUP_EXE} não encontrado.")
        return False
    shutil.copy2(BACKUP_EXE, GAME_EXE)
    print(f"[Restaurado] nmh2.exe original restaurado a partir do backup.")
    return True


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--restore":
        restore_backup()
    else:
        apply_patch()
