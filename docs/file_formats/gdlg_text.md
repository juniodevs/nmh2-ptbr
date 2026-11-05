# Especificação Técnica: Formato de Textos e Diálogos GDLG (.GDL)

> **Origem:** Grasshopper Manufacture  
> **Magic Bytes:** `47 44 4C 47` (`GDLG`)  
> **Identificado em:** `NMH1` e `NMH2` (presente em mais de 104 arquivos do jogo)  
> **Codificação das Strings:** UTF-16LE (Little-Endian Unicode)  
> **Status:** Revertido e validado com sucesso através da engenharia reversa do pacote de tradução  

---

## 1. Visão Geral

O formato `.GDL` (`GDLG`) é o padrão proprietário da Grasshopper Manufacture para todos os textos de diálogo, legendas de cutscenes, menus e informações de missões em *No More Heroes 1* e *No More Heroes 2*.

Diferente de formatos legados que usam tabelas ASCII ou Shift-JIS de byte único com substituição de caracteres, o `GDLG` utiliza nativamente **UTF-16LE** para o corpo das frases, permitindo suporte direto a toda a acentuação do Português Brasileiro (`á, à, â, ã, é, ê, í, ó, ô, õ, ú, ç`).

---

## 2. Estrutura do Cabeçalho GDLG

O cabeçalho inicial possui tamanho variável e ponteiros fixos em Little-Endian:

| Offset | Tamanho | Tipo | Descrição |
|---|---|---|---|
| `0x00` | 4 bytes | char[4] | Magic `GDLG` |
| `0x04` | 4 bytes | uint32 | Versão / Flags do formato |
| `0x08` | 4 bytes | uint16/uint16 | Contagem de blocos e identificadores |
| `0x0C` | 4 bytes | uint32 | Offset da tabela de descritores de eventos |
| `0x14` | 4 bytes | uint32 | Offset da tabela de ponteiros de strings |
| `0x2C` | 4 bytes | uint32 | **Ponteiro de Início da Tabela de Textos UTF-16LE** |
| `0x30` | 4 bytes | uint32 | Ponteiro da Tabela de Identificadores/Chaves (ASCII) |

---

## 3. Armazenamento das Frases (Pool UTF-16LE)

A partir do offset apontado por `0x2C`:
- Cada linha de texto é armazenada como uma sequência de caracteres de 16 bits (2 bytes por caractere).
- O término de cada linha é delimitado por `0x00 0x00` (caractere nulo em UTF-16LE).
- Quebras de linha manuais utilizam `\r\n` codificado em UTF-16LE (`0x0D 0x00 0x0A 0x00`).
- Caracteres especiais da língua portuguesa:
  - `ã`: `0xE3 0x00`
  - `õ`: `0xF5 0x00`
  - `ç`: `0xE7 0x00`
  - `é`: `0xE9 0x00`
  - `á`: `0xE1 0x00`
  - `í`: `0xED 0x00`
  - `ó`: `0xF3 0x00`
  - `ú`: `0xFA 0x00`

---

## 4. Relação com STRIMAG2

Em diversas instâncias, cada arquivo `.GDL` (ex: `EVESM02E.GDL`) é acompanhado por um arquivo binário complementar `_GC.BIN` (ex: `EVESM02E_GC.BIN`).
- O `.GDL` fornece a lógica de exibição, temporização e as strings literais.
- O `_GC.BIN` (`STRIMAG2`) fornece o cache de bitmaps/textura de glifos pré-renderizados quando aplicável.

