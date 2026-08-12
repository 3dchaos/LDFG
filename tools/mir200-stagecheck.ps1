param(
    [string]$MapInfo = 'Mir200\Envir\MapInfo.txt',
    [string]$MapOpenScript,
    [switch]$Json
)

. "$PSScriptRoot\mir200-common.ps1"

if (-not $MapOpenScript) {
    $MapOpenScript = Find-Mir200MapOpenScript
}

if (-not $MapOpenScript) {
    throw 'Map open script not found. Pass -MapOpenScript explicitly.'
}

$stageByMap = Get-Mir200StageMap -Path $MapOpenScript
$violations = foreach ($link in Get-Mir200MapLinks -Path $MapInfo) {
    $sourceStage = if ($stageByMap.ContainsKey($link.SourceMap)) { [int]$stageByMap[$link.SourceMap] } else { 0 }
    $targetStage = if ($stageByMap.ContainsKey($link.TargetMap)) { [int]$stageByMap[$link.TargetMap] } else { 0 }

    if ($targetStage -gt $sourceStage) {
        [pscustomobject]@{
            Line        = $link.Line
            SourceMap   = $link.SourceMap
            SourceStage = $sourceStage
            SourceX     = $link.SourceX
            SourceY     = $link.SourceY
            TargetMap   = $link.TargetMap
            TargetStage = $targetStage
            TargetX     = $link.TargetX
            TargetY     = $link.TargetY
            Raw         = $link.Raw
        }
    }
}

if ($Json) {
    [pscustomobject]@{
        MapInfo       = $MapInfo
        MapOpenScript = $MapOpenScript
        Violations    = @($violations)
    } | ConvertTo-Json -Depth 6
} else {
    $items = @($violations)
    "MapInfo: $MapInfo"
    "MapOpenScript: $MapOpenScript"
    "LowToHighStaticLinks: $($items.Count)"
    if ($items.Count -gt 0) {
        $items | Sort-Object Line | Format-Table Line, SourceMap, SourceStage, TargetMap, TargetStage, SourceX, SourceY, TargetX, TargetY -AutoSize
    }
}
