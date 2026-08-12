Set-StrictMode -Version Latest

function Get-Mir200Encoding {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    $extension = [IO.Path]::GetExtension($Path).ToLowerInvariant()
    if ($extension -eq '.md' -or $extension -eq '.json' -or $extension -eq '.ps1') {
        return [Text.UTF8Encoding]::new($false)
    }

    return [Text.Encoding]::GetEncoding(936)
}

function Read-Mir200Text {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,

        [Text.Encoding]$Encoding
    )

    $resolved = (Resolve-Path -LiteralPath $Path).Path
    if ($null -eq $Encoding) {
        $Encoding = Get-Mir200Encoding -Path $resolved
    }

    return $Encoding.GetString([IO.File]::ReadAllBytes($resolved))
}

function Write-Mir200Text {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,

        [Parameter(Mandatory = $true)]
        [string]$Text,

        [Text.Encoding]$Encoding
    )

    $resolved = (Resolve-Path -LiteralPath $Path).Path
    if ($null -eq $Encoding) {
        $Encoding = Get-Mir200Encoding -Path $resolved
    }

    [IO.File]::WriteAllText($resolved, $Text, $Encoding)
}

function Get-Mir200NewLine {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Text
    )

    if ($Text.Contains("`r`n")) { return "`r`n" }
    if ($Text.Contains("`n")) { return "`n" }
    return "`r"
}

function Split-Mir200Lines {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Text
    )

    return [regex]::Split($Text, '\r\n|\n|\r')
}

function Get-Mir200MapLinks {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    $text = Read-Mir200Text -Path $Path -Encoding ([Text.Encoding]::GetEncoding(936))
    $lineNumber = 0
    foreach ($line in Split-Mir200Lines -Text $text) {
        $lineNumber++
        if ($line -match '^\s*;') { continue }
        if ($line -match '^\s*([^\s\[]+)\s+([0-9]+)[,\s]+([0-9]+)\s*->\s*([^\s\[]+)\s+([0-9]+)[,\s]+([0-9]+)') {
            [pscustomobject]@{
                Line      = $lineNumber
                SourceMap = $matches[1]
                SourceX   = [int]$matches[2]
                SourceY   = [int]$matches[3]
                TargetMap = $matches[4]
                TargetX   = [int]$matches[5]
                TargetY   = [int]$matches[6]
                Raw       = $line
            }
        }
    }
}

function Get-Mir200StageMap {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    $text = Read-Mir200Text -Path $Path -Encoding ([Text.Encoding]::GetEncoding(936))
    $stageByMap = @{}
    $currentStage = $null

    foreach ($line in Split-Mir200Lines -Text $text) {
        if ($line -match '^\[@地图开放_检查阶段(\d+)\]') {
            $currentStage = [int]$matches[1]
            continue
        }

        if ($line -match '^\[@' -and $line -notmatch '^\[@地图开放_检查阶段') {
            $currentStage = $null
            continue
        }

        if ($null -ne $currentStage -and $line -match '^EQUAL\s+<\$MAP>\s+(\S+)') {
            $stageByMap[$matches[1]] = $currentStage
        }
    }

    return $stageByMap
}

function Find-Mir200MapOpenScript {
    param(
        [string]$Root = '.'
    )

    $questDiary = Join-Path $Root 'Mir200\Envir\QuestDiary'
    Get-ChildItem -LiteralPath $questDiary -Recurse -Filter '*.txt' |
        Select-String -Encoding ansi -Pattern '^\[@地图开放_杀怪触发\]' |
        Select-Object -First 1 -ExpandProperty Path
}
