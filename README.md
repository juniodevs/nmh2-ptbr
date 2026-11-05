# No More Heroes 2: Desperate Struggle - Tradução PT-BR

Tradução em Português do Brasil para No More Heroes 2: Desperate Struggle de PC (Steam).

## Aviso de Versão Beta

Esta tradução está em fase de testes abertos. Como o jogo possui muitas fases, diálogos em combate e minigames específicos, travamentos, falhas de formatação ou crashes pontuais ainda podem ocorrer durante o jogo.

Se encontrar qualquer erro, travamento ou texto quebrado, abra uma Issue aqui no GitHub com o nome da missão, a cutscene ou o momento exato em que o problema aconteceu.

## Créditos

- juniodevs (DoubleXXP): Tradução e engenharia reversa
- Vickz_Joga: Testes in-game e validação
- Timo654: Ferramenta No-More-RSL (descompactação e recompactação dos arquivos RSL)

## Como Instalar

1. Baixe o pacote da tradução na aba Releases e extraia os arquivos.
2. Certifique-se de que o jogo está fechado.
3. Dê dois cliques em `Instalar_Traducao.bat`.
4. O instalador tentará localizar a pasta do jogo na Steam automaticamente. Caso seu jogo esteja instalado em outro diretório, digite ou arraste o caminho da pasta onde fica o arquivo `nmh2.exe`.
5. Digite `1` e pressione Enter para instalar.

O instalador salva uma cópia dos arquivos originais em uma pasta chamada `.backup` dentro do diretório do jogo antes de aplicar as modificações.

## Como Restaurar o Jogo Original

1. Abra o arquivo `Instalar_Traducao.bat`.
2. Digite `2` e pressione Enter.

O script copia os arquivos salvos em `.backup` de volta para a pasta do jogo, restaurando os arquivos originais em inglês.

## Conteúdo Traduzido

- 75 cutscenes com legendas em português
- Diálogos de combate, chefes e tutoriais adaptados
- Bicos de Santa Destroy (minigames 8-bit com nomes adaptados)
- Banners de combate e rank up traduzidos (FALHA, TEMPO ESGOTADO, VAI!, TEMPO FINAL)
- Legenda gráfica da batalha contra Skelter Helter
- Menus, seleção de dificuldade, opções e telas de save no executável

## Estrutura do Repositório

- `data/translated/`: arquivos do jogo modificados e prontos para inserção (cutscenes, cenários, texturas)
- `translation/pt-BR/`: textos extraídos em formato JSON
- `tools/`: scripts em Python para descompressão LZ, montagem de RSL e aplicação de patches no executável
- `release/`: estrutura do pacote pronto para distribuição aos jogadores

## Requisitos para Desenvolvimento

Para quem deseja alterar textos, scripts ou recompilar arquivos:

- Windows 10 ou 11
- Python 3.10 ou superior
- Dependências: `pip install binary_reader Pillow numpy`
