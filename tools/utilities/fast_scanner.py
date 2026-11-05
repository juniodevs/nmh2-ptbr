# -*- coding: utf-8 -*-
import os
import sys
import time
import struct
from pathlib import Path

def decompress_fast(data: bytes) -> bytes:
    if len(data) < 9:
        return data
    uncomp_sz, comp_sz = struct.unpack('<II', data[:8])
    if comp_sz != len(data) or uncomp_sz <= comp_sz:
        return data
        
    escape_byte = data[8]
    esc_b = bytes([escape_byte])
    
    src = 9
    src_end = min(len(data), comp_sz)
    out = bytearray(uncomp_sz)
    dst = 0
    
    while src < src_end and dst < uncomp_sz:
        next_esc = data.find(esc_b, src, src_end)
        if next_esc == -1:
            chunk_len = src_end - src
            out[dst : dst + chunk_len] = data[src : src_end]
            dst += chunk_len
            break
        elif next_esc > src:
            chunk_len = next_esc - src
            out[dst : dst + chunk_len] = data[src : next_esc]
            dst += chunk_len
            src = next_esc
            
        src += 1
        if src >= src_end:
            break
        nxt = data[src]
        src += 1
        if nxt == escape_byte:
            out[dst] = escape_byte
            dst += 1
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
            
            ref = dst - dist
            for _ in range(length):
                out[dst] = out[ref]
                dst += 1
                ref += 1

    return bytes(out[:dst])

if __name__ == "__main__":
    stg0101_path = Path(r"E:\SteamLibrary\steamapps\common\No More Heroes 2 Desperate Struggle\STG\STG0101\STG0101.bin")
    data = stg0101_path.read_bytes()
    t0 = time.time()
    res = decompress_fast(data)
    t1 = time.time()
    print(f"STG0101: {len(data)} -> {len(res)} bytes in {t1 - t0:.3f}s. GDLG count: {res.count(b'GDLG')}")
