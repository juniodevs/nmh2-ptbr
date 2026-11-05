# Especificação Técnica: Algoritmo de Compressão ghmGcLz

> **Origem:** Grasshopper Manufacture (GameCube / Wii)  
> **Identificado em:** `nmh2.exe` (Função em `0x82B4C0`, chamada em `0x801844`)  
> **Status:** Revertido e validado com sucesso  

---

## 1. Estrutura do Cabeçalho (9 Bytes)

| Offset | Tamanho | Tipo | Descrição |
|---|---|---|---|
| `0x00` | 4 bytes | uint32 (LE) | Tamanho descompactado do arquivo (`uncompressed_size`) |
| `0x04` | 4 bytes | uint32 (LE) | Tamanho total do arquivo compactado (`compressed_size`). O payload tem tamanho `compressed_size - 9`. |
| `0x08` | 1 byte  | uint8       | Byte de escape (`escape_byte`). Escolhido dinamicamente pelo compactador (geralmente o byte menos frequente no arquivo original). |

---

## 2. Formato do Stream de Dados Compactado

O payload inicia imediatamente no offset `0x09` e é processado sequencialmente até que `len(output) == uncompressed_size` ou o stream termine:

1. **Byte Literal:**
   - Se o byte lido `b != escape_byte`:
     - O byte `b` é emitido diretamente no buffer de saída: `output.append(b)`.

2. **Byte de Escape Duplicado (Literal do Escape):**
   - Se o byte lido for igual a `escape_byte`, lê-se o próximo byte `nxt`.
   - Se `nxt == escape_byte`:
     - Emite um único `escape_byte` literal no buffer de saída: `output.append(escape_byte)`.

3. **Referência LZ (Backreference / Match):**
   - Se `nxt != escape_byte`, temos uma correspondência retroativa:
     - `code = (nxt - 1) if nxt > escape_byte else nxt` (revertido de `0x82B54A..0x82B55C` em `nmh2.exe`: `cmp ecx, escape_byte; lea eax, [ecx - 1]; cmovbe eax, ecx`). Como o byte de escape é removido do domínio dos códigos literais, qualquer valor maior que o escape tem seu índice decrementado em 1.
     - **Cálculo do Comprimento (`length`):**
       - `length = (code >> 3) + 4`.
       - Se `(code & 4) != 0` (flag indicando byte de comprimento extra):
         - Lê o próximo byte `extra_len`.
         - `length = ((code >> 3) | (extra_len << 5)) + 4`.
     - **Cálculo da Distância (`distance`):**
       - `offset_bytes = (code & 3)`.
       - Lê `dist_byte0`.
       - `dist = dist_byte0`.
       - Se `offset_bytes != 0`:
         - Lê `dist_byte1`.
         - `dist |= (dist_byte1 << 8)`.
         - Se `offset_bytes == 2`:
           - Lê `dist_byte2`.
           - `dist |= (dist_byte2 << 16)`.
       - `distance = dist + 1`.
     - **Cópia do Match Retroativo:**
       - Copia `length` bytes a partir de `pos = len(output) - distance`.
       - Permite cópias sobrepostas (RLE/runs repetitivos onde `length > distance`).

