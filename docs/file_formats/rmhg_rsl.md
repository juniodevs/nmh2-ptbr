# Especificação Técnica: Contêiner RMHG (.RSL)

> **Origem:** Grasshopper Manufacture (RooM GrassHopper)  
> **Magic Bytes:** `52 4D 48 47` (`RMHG`)  
> **Utilização:** Embalagem principal de modelos, texturas, scripts e diálogos em *Killer7*, *No More Heroes 1* e *No More Heroes 2*.  

---

## 1. Estrutura do Cabeçalho RMHG (32 Bytes)

| Offset | Tamanho | Tipo | Descrição |
|---|---|---|---|
| `0x00` | 4 bytes | char[4] | Magic: `RMHG` |
| `0x04` | 4 bytes | uint32 (LE) | Quantidade de recursos no arquivo (`resource_count`) |
| `0x08` | 4 bytes | uint32 (LE) | Offset relativo dos atributos de recursos (geralmente `0x20` = 32) |
| `0x0C` | 4 bytes | uint32 (LE) | Versão do formato (`1069` no NMH2 Steam) |
| `0x10` | 4 bytes | uint32 (LE) | Offset relativo da tabela de strings (nomes dos recursos) |
| `0x14` | 12 bytes | padding | Preenchido com zeros |

---

## 2. Tabela de Strings de Recursos

Se `str_table_offset > 0`:
- Contém a contagem de strings e os ponteiros para cada nome de arquivo/pasta.
- **Ofuscação de Strings:** Para versões superiores a `1040` (como a versão `1069` do NMH2), os caracteres das strings de nomes são ofuscados com a chave XOR `0x8D`.

---

## 3. Tabela de Atributos de Recursos (32 Bytes por Entrada)

Cada recurso contido possui uma entrada descritora:

| Offset Relativo | Tamanho | Tipo | Descrição |
|---|---|---|---|
| `0x00` | 4 bytes | uint32 (LE) | Offset dos dados do recurso |
| `0x04` | 4 bytes | uint32 (LE) | Tamanho dos dados em bytes |
| `0x08` | 4 bytes | uint32 (LE) | Flags de processamento (1 = sub-contêiner RMHG) |
| `0x0C` | 4 bytes | uint32 (LE) | Versão do recurso |
| `0x10` | 4 bytes | int32 (LE)  | Índice da string com o nome do arquivo (-1 se anônimo) |
| `0x14` | 12 bytes | padding | Zeros |

