# -*- coding: utf-8 -*-
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$Host.UI.RawUI.WindowTitle = "Atualizador No More Heroes 2 PT-BR"

function Find-GameDirectory {
    $candidates = @(
        $PSScriptRoot,
        (Split-Path $PSScriptRoot -Parent),
        "E:\SteamLibrary\steamapps\common\No More Heroes 2 Desperate Struggle",
        "C:\Program Files (x86)\Steam\steamapps\common\No More Heroes 2 Desperate Struggle",
        "C:\SteamLibrary\steamapps\common\No More Heroes 2 Desperate Struggle",
        "D:\SteamLibrary\steamapps\common\No More Heroes 2 Desperate Struggle"
    )

    foreach ($cand in $candidates) {
        if ($cand -and (Test-Path "$cand\nmh2.exe")) {
            return (Resolve-Path $cand).Path
        }
    }
    return $null
}

function Prompt-GameDirectory {
    param([string]$detected)

    if ($detected) {
        Write-Host "Pasta do jogo localizada: $detected" -ForegroundColor Green
        $resp = Read-Host "Usar esta pasta? [S/N] (Padrao: S)"
        if ($resp -eq "" -or $resp.ToUpper() -eq "S") {
            return $detected
        }
    }

    while ($true) {
        Write-Host "Digite ou arraste o caminho da pasta do jogo onde fica o nmh2.exe:" -ForegroundColor Cyan
        $inputPath = Read-Host "Caminho"
        $inputPath = $inputPath.Trim().Trim('"').Trim("'")

        if (Test-Path $inputPath) {
            $item = Get-Item $inputPath
            if (-not $item.PSIsContainer) {
                if ($item.Name.ToLower() -eq "nmh2.exe") {
                    return $item.DirectoryName
                }
            } else {
                if (Test-Path "$inputPath\nmh2.exe") {
                    return (Resolve-Path $inputPath).Path
                }
            }
        }
        Write-Host "nmh2.exe nao foi encontrado no caminho informado. Tente novamente." -ForegroundColor Red
    }
}

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "     NO MORE HEROES 2 - ATUALIZADOR AUTOMATICO DE TRADUCAO      " -ForegroundColor Yellow
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host ""

$detected = Find-GameDirectory
$gameDir = Prompt-GameDirectory -detected $detected

# Ler versao local instalada
$versionFile = Join-Path $gameDir "version.txt"
$localVer = "v1.0.0-beta"
if (Test-Path $versionFile) {
    $localVer = (Get-Content $versionFile -Raw).Trim()
}

Write-Host ""
Write-Host "[*] Versao instalada no PC: $localVer" -ForegroundColor White
Write-Host "[*] Verificando atualizacoes no GitHub..." -ForegroundColor Cyan

try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $releases = Invoke-RestMethod -Uri "https://api.github.com/repos/juniodevs/nmh2-ptbr/releases" -Headers @{"User-Agent"="PowerShell-NMH2-Updater"}
    if (-not $releases -or $releases.Count -eq 0) {
        Write-Host "[!] Nenhuma release encontrada no repositorio." -ForegroundColor Yellow
        exit
    }
    $latest = $releases[0]
    $remoteVer = $latest.tag_name
} catch {
    Write-Host "[!] Falha ao verificar atualizacoes: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host "[*] Versao mais recente disponivel: $remoteVer" -ForegroundColor White

if ($localVer -eq $remoteVer) {
    Write-Host ""
    Write-Host "=================================================================" -ForegroundColor Green
    Write-Host "  Sua traducao ja esta 100% atualizada na versao $localVer!      " -ForegroundColor Green
    Write-Host "=================================================================" -ForegroundColor Green
    Write-Host ""
    Read-Host "Pressione Enter para fechar..."
    exit 0
}

Write-Host ""
Write-Host "[+] Nova versao encontrada: $remoteVer!" -ForegroundColor Yellow
Write-Host "[+] Localizando pacote de atualizacao leve..." -ForegroundColor Cyan

# Procurar asset de update ou fallback para o pacote completo
$asset = $latest.assets | Where-Object { $_.name -like "*Update*.zip" } | Select-Object -First 1
if (-not $asset) {
    $asset = $latest.assets | Where-Object { $_.name -like "*.zip" } | Select-Object -First 1
}

if (-not $asset) {
    Write-Host "[!] Nenhum arquivo ZIP encontrado na release $remoteVer." -ForegroundColor Red
    exit 1
}

$zipSizeMB = [math]::Round($asset.size / (1024 * 1024), 1)
Write-Host "[+] Baixando $($asset.name) ($zipSizeMB MB)..." -ForegroundColor Yellow

$tempZip = Join-Path $env:TEMP "nmh2_update_$remoteVer.zip"
$tempExtract = Join-Path $env:TEMP "nmh2_update_extract_$remoteVer"

try {
    if (Test-Path $tempZip) { Remove-Item $tempZip -Force }
    if (Test-Path $tempExtract) { Remove-Item $tempExtract -Recurse -Force }

    Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $tempZip -UseBasicParsing
    Write-Host "[+] Download concluido com sucesso!" -ForegroundColor Green

    Write-Host "[+] Extraindo arquivos de atualizacao..." -ForegroundColor Cyan
    Expand-Archive -Path $tempZip -DestinationPath $tempExtract -Force

    # Identificar se os arquivos estao dentro de traducao_arquivos ou na raiz
    $sourcePayload = $tempExtract
    if (Test-Path "$tempExtract\traducao_arquivos") {
        $sourcePayload = "$tempExtract\traducao_arquivos"
    } elseif (Test-Path "$tempExtract\No_More_Heroes_2_Traducao_PTBR_Beta\traducao_arquivos") {
        $sourcePayload = "$tempExtract\No_More_Heroes_2_Traducao_PTBR_Beta\traducao_arquivos"
    }

    $filesToCopy = Get-ChildItem -Path $sourcePayload -Recurse -File
    $count = 0
    foreach ($f in $filesToCopy) {
        $relPath = $f.FullName.Substring($sourcePayload.Length).TrimStart("\/")
        $destFile = Join-Path $gameDir $relPath
        $destFolder = Split-Path $destFile -Parent
        if (-not (Test-Path $destFolder)) {
            New-Item -ItemType Directory -Path $destFolder -Force | Out-Null
        }
        Copy-Item -Path $f.FullName -Destination $destFile -Force
        $count++
    }

    # Copiar scripts auxiliares para a pasta do jogo se existirem no zip
    foreach ($scriptName in @("patch_exe.py", "Atualizar_Traducao.bat", "updater.ps1")) {
        $foundScript = Get-ChildItem -Path $tempExtract -Recurse -Filter $scriptName | Select-Object -First 1
        if ($foundScript) {
            Copy-Item -Path $foundScript.FullName -Destination (Join-Path $gameDir $scriptName) -Force
        }
    }

    # Executar patch do executavel se patch_exe.py existir
    $localPatchScript = Join-Path $gameDir "patch_exe.py"
    if (Test-Path $localPatchScript) {
        $python = Get-Command python -ErrorAction SilentlyContinue
        if ($python) {
            Write-Host "[+] Aplicando correcoes no executavel nmh2.exe..." -ForegroundColor Cyan
            $env:GAME_EXE_OVERRIDE = Join-Path $gameDir "nmh2.exe"
            & python $localPatchScript | Out-Null
        }
    }

    # Salvar versao atualizada
    Set-Content -Path $versionFile -Value $remoteVer -Force

    Write-Host ""
    Write-Host "=================================================================" -ForegroundColor Green
    Write-Host "  TRADUCAO ATUALIZADA COM SUCESSO PARA $remoteVer!               " -ForegroundColor Green
    Write-Host "  ($count arquivos atualizados)                                  " -ForegroundColor Green
    Write-Host "=================================================================" -ForegroundColor Green
    Write-Host ""
} finally {
    if (Test-Path $tempZip) { Remove-Item $tempZip -Force -ErrorAction SilentlyContinue }
    if (Test-Path $tempExtract) { Remove-Item $tempExtract -Recurse -Force -ErrorAction SilentlyContinue }
}

Read-Host "Pressione Enter para fechar..."

