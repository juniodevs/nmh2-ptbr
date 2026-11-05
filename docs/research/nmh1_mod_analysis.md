# Análise Técnica do Mod PT-BR de No More Heroes 1 (Quessada House)

> **Fonte Analisada:** Pacote de tradução PT-BR v1.0.3 para NMH1 (Steam Build 24776853)  
> **Caminho Local:** `C:\Users\irama\Downloads\will\NMH1\No_More_Heroes_PTBR_Final_24776853_Final`  
> **Data da Análise:** 2026-11-04  

---

## 1. Descobertas Críticas Aplicáveis a No More Heroes 2

### 1.1. Codificação e Formato dos Diálogos
- **Formato:** O tradutor não precisou criar um formato novo nem alterar ponteiros complexos de código: ele editou diretamente os arquivos `.GDL` (`GDLG`) dentro dos contêineres `.RSL` nas pastas `SCRIPT/MESSAGE_US/` e equivalentes.
- **Codificação:** As strings de diálogos são codificadas em **UTF-16LE**, permitindo acentos e caracteres especiais do português sem gambiarras ou substituição destrutiva de caracteres em tabelas ANSI.

### 1.2. Ativação de Legendas In-Game
- O executável lê a flag de legendas ativas a partir do arquivo de configuração do usuário em:
  `%USERPROFILE%\Saved Games\NMH\nmh.ini`
  Chave: `[General] -> EnableEngSubtitles = 1`
- Em *No More Heroes 2*, o arquivo análogo é verificado na pasta de saves correspondente (`Saved Games\NMH2` ou registro Steam).

### 1.3. Modificações no Executável (`nmh.exe`)
- O autor adicionou uma nova seção PE de 512 bytes chamada `.ptbr` no executável para substituir quatro palavras de botões e interface que estavam chumbadas no código binário em UTF-16LE:
  - `APERTE`
  - `AJUSTES`
  - `MAPA`
  - `DADOS`
- Para *No More Heroes 2*, utilizaremos a mesma técnica caso sejam identificadas strings de interface estáticas no `nmh2.exe`.

### 1.4. Pipeline de Instalação e Segurança
- O mod utiliza um manifesto JSON (`manifesto.json`) com hashes SHA256 de antes e depois para 557 arquivos.
- Criação de backup atômico antes de qualquer cópia, permitindo rollback limpo via script `Restaurar.ps1`.

