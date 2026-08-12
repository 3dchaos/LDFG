param(
    [string]$MapInfo = 'Mir200\Envir\MapInfo.txt',
    [string]$SourceMap,
    [string]$TargetMap,
    [switch]$Json
)

. "$PSScriptRoot\mir200-common.ps1"

$links = Get-Mir200MapLinks -Path $MapInfo

if ($SourceMap) {
    $links = $links | Where-Object { $_.SourceMap -eq $SourceMap }
}

if ($TargetMap) {
    $links = $links | Where-Object { $_.TargetMap -eq $TargetMap }
}

if ($Json) {
    $links | ConvertTo-Json -Depth 4
} else {
    $links | Sort-Object Line | Format-Table Line, SourceMap, SourceX, SourceY, TargetMap, TargetX, TargetY -AutoSize
}
