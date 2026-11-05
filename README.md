# No More Heroes 2: Desperate Struggle (Tradução PT-BR)

Tradução em português do Brasil para a versão de PC (Steam) do No More Heroes 2: Desperate Struggle.

## Aviso de versão beta

A tradução está em fase de testes abertos. Como o jogo tem dezenas de fases, falas em combate e minigames próprios, você ainda pode encontrar algum travamento, crash pontual ou detalhe visual fora do lugar.

Se passar por algum erro, abra uma Issue aqui no repositório informando a fase, a cutscene ou o momento em que a falha aconteceu.

## Créditos

- [juniodevs](https://junio.is-a.dev/): tradução e engenharia reversa
- [Vickz_Joga](https://www.youtube.com/@Vickz_Joga): testes e validação em gameplay
- Timo654: ferramenta No-More-RSL (descompactação e recompactação de contêineres RSL)

## Como instalar

1. Baixe o arquivo da tradução na aba de Releases do GitHub e extraia a pasta.
2. Feche o jogo antes de continuar.
3. Abra o arquivo `Instalar_Traducao.bat`.
4. O script tenta achar a pasta da Steam automaticamente. Se o seu jogo estiver em outro diretório, digite ou cole o caminho da pasta onde fica o executável `nmh2.exe`.
5. Escolha a opção `1` e aperte Enter.

O instalador cria uma cópia dos arquivos originais em uma pasta `.backup` dentro do diretório do jogo antes de substituir qualquer dado.

## Como restaurar o jogo original

1. Abra o arquivo `Instalar_Traducao.bat`.
2. Escolha a opção `2` e aperte Enter.

O script restaura os arquivos guardados na pasta `.backup`, voltando o jogo ao inglês original da Steam.

## O que está traduzido

- Cutscenes com legendas em português e fonte retrô VCR OSD Mono calibrada
- Diálogos de combate, falas de chefes e tutoriais
- Bicos e minigames de Santa Destroy (minigames em 8-bit e cata aos escorpiões)
- Missões de Vingança (Revenge Missions) e missão de infiltração da Shinobu
- Instalações de Santa Destroy e Motel do Travis (armário, revistas de wrestling, minigame da Jeane, balões e TV)
- Banners de combate e rank up (FALHA, TEMPO ESGOTADO, VAI!, TEMPO FINAL)
- Legenda gráfica da luta contra Skelter Helter
- Menus principais, opções, telas de save e seleção de dificuldade direto no executável

## Requisitos para compilação local

Caso queira alterar textos, scripts ou gerar arquivos novos por conta própria:

- Windows 10 ou 11
- Python 3.10 ou superior
- Bibliotecas necessárias: `pip install binary_reader Pillow numpy`
