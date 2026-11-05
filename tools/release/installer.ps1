# -*- coding: utf-8 -*-
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$Host.UI.RawUI.WindowTitle = "Instalador No More Heroes 2 PT-BR (Beta)"

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
        Write-Host "Digite ou arraste o caminho da pasta do jogo ou do nmh2.exe:" -ForegroundColor Cyan
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

function Install-Translation {
    param([string]$gameDir, [string]$payloadDir)

    $backupDir = Join-Path $gameDir ".backup"
    if (-not (Test-Path $backupDir)) {
        New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
    }

    Write-Host ""
    Write-Host "Instalando traducao..." -ForegroundColor Cyan

    $files = Get-ChildItem -Path $payloadDir -Recurse -File
    $total = $files.Count
    $current = 0
    $backedUp = 0

    foreach ($f in $files) {
        $current++
        $relPath = $f.FullName.Substring($payloadDir.Length).TrimStart("\/")
        $targetFile = Join-Path $gameDir $relPath
        $backupFile = Join-Path $backupDir $relPath

        if ((Test-Path $targetFile) -and (-not (Test-Path $backupFile))) {
            $destDir = Split-Path $backupFile -Parent
            if (-not (Test-Path $destDir)) {
                New-Item -ItemType Directory -Path $destDir -Force | Out-Null
            }
            Copy-Item -Path $targetFile -Destination $backupFile -Force
            $backedUp++
        }

        $targetDir = Split-Path $targetFile -Parent
        if (-not (Test-Path $targetDir)) {
            New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
        }
        Copy-Item -Path $f.FullName -Destination $targetFile -Force

        $percent = [math]::Round(($current / $total) * 100)
        Write-Progress -Activity "Instalando arquivos..." -Status "$percent% ($current/$total)" -PercentComplete $percent
    }
    Write-Progress -Activity "Instalando arquivos..." -Completed

    $exePath = Join-Path $gameDir "nmh2.exe"
    $exeBackup = Join-Path $backupDir "nmh2.exe"
    if ((Test-Path $exePath) -and (-not (Test-Path $exeBackup))) {
        Copy-Item -Path $exePath -Destination $exeBackup -Force
    }

    $patchScript = Join-Path $PSScriptRoot "patch_exe.py"
    if (Test-Path $patchScript) {
        $python = Get-Command python -ErrorAction SilentlyContinue
        if ($python) {
            $env:GAME_EXE_OVERRIDE = $exePath
            & python $patchScript
        }
    }

    Write-Host ""
    Write-Host "Traducao instalada com sucesso ($total arquivos copiados)." -ForegroundColor Green
    if ($backedUp -gt 0) {
        Write-Host "Backup dos arquivos originais salvo em: $backupDir" -ForegroundColor Gray
    }
}

function Restore-Game {
    param([string]$gameDir)

    $backupDir = Join-Path $gameDir ".backup"
    if (-not (Test-Path $backupDir)) {
        Write-Host "Pasta de backup (.backup) nao encontrada em: $gameDir" -ForegroundColor Red
        return
    }

    $backupFiles = Get-ChildItem -Path $backupDir -Recurse -File
    if ($backupFiles.Count -eq 0) {
        Write-Host "A pasta .backup esta vazia." -ForegroundColor Red
        return
    }

    Write-Host ""
    Write-Host "Restaurando arquivos originais..." -ForegroundColor Cyan

    $current = 0
    $total = $backupFiles.Count

    foreach ($f in $backupFiles) {
        $current++
        $relPath = $f.FullName.Substring($backupDir.Length).TrimStart("\/")
        $targetFile = Join-Path $gameDir $relPath

        $targetDir = Split-Path $targetFile -Parent
        if (-not (Test-Path $targetDir)) {
            New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
        }
        Copy-Item -Path $f.FullName -Destination $targetFile -Force

        $percent = [math]::Round(($current / $total) * 100)
        Write-Progress -Activity "Restaurando..." -Status "$percent% ($current/$total)" -PercentComplete $percent
    }
    Write-Progress -Activity "Restaurando..." -Completed

    Write-Host ""
    Write-Host "Arquivos originais restaurados com sucesso ($total arquivos)." -ForegroundColor Green
}

$payloadDir = Join-Path $PSScriptRoot "traducao_arquivos"
if (-not (Test-Path $payloadDir)) {
    $repoPayload = Join-Path (Split-Path $PSScriptRoot -Parent) "data\translated"
    if (Test-Path $repoPayload) {
        $payloadDir = $repoPayload
    } else {
        $devPayload = Join-Path $PSScriptRoot "data\translated"
        if (Test-Path $devPayload) {
            $payloadDir = $devPayload
        } else {
            Write-Host "Pasta 'traducao_arquivos' nao encontrada." -ForegroundColor Red
            Read-Host "Pressione Enter para sair..."
            exit 1
        }
    }
}

$detected = Find-GameDirectory
$gameDir = Prompt-GameDirectory -detected $detected

while ($true) {
    Write-Host ""
    Write-Host "--- No More Heroes 2: Traducao PT-BR (Beta) ---" -ForegroundColor Cyan
    Write-Host "Diretorio do jogo: $gameDir" -ForegroundColor Gray
    Write-Host "1. Instalar traducao (cria backup em .backup)"
    Write-Host "2. Restaurar jogo original a partir de .backup"
    Write-Host "3. Sair"
    Write-Host ""
    $op = Read-Host "Opcao [1-3]"

    switch ($op) {
        "1" {
            Install-Translation -gameDir $gameDir -payloadDir $payloadDir
            Write-Host ""
            Read-Host "Pressione Enter para continuar..."
        }
        "2" {
            Restore-Game -gameDir $gameDir
            Write-Host ""
            Read-Host "Pressione Enter para continuar..."
        }
        "3" {
            exit 0
        }
        default {
            Write-Host "Opcao invalida." -ForegroundColor Red
        }
    }
}
