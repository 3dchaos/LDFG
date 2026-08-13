param(
    [string]$Root = (Resolve-Path '.').Path
)

$ErrorActionPreference = 'Stop'

$base = Join-Path $Root 'Mir200\Envir'
$scriptPath = Join-Path $base 'QuestDiary\系统功能\军鼓BUFF.txt'
$configPath = Join-Path $base 'QuestDiary\系统功能\军鼓流派配置.txt'
$warriorPath = Join-Path $base 'QuestDiary\系统功能\军鼓流派\战士军鼓.txt'
$wizardPath = Join-Path $base 'QuestDiary\系统功能\军鼓流派\法师军鼓.txt'
$taoistPath = Join-Path $base 'QuestDiary\系统功能\军鼓流派\道士军鼓.txt'
$qFunction = Join-Path $base 'Market_def\QFunction-0.txt'
$qManage = Join-Path $base 'MapQuest_def\QManage.txt'
$attackPath = Join-Path $base 'QuestDiary\系统功能\老登辅助\攻击触发.txt'
$deathPath = Join-Path $base 'QuestDiary\系统功能\老登辅助\死亡触发.txt'
$specPath = Join-Path $Root 'docs\军鼓位玩法StdItems.csv'
$descPath = Join-Path $base 'ItemDescList.txt'
$gbk = [Text.Encoding]::GetEncoding(936)

$fail = @()

if (-not (Test-Path -LiteralPath $specPath)) {
    $fail += "missing spec: $specPath"
}

$specRows = @()
if (Test-Path -LiteralPath $specPath) {
    $specRows = @(Import-Csv -LiteralPath $specPath -Encoding utf8)
    if ($specRows.Count -ne 54) {
        $fail += "expected 54 spec rows, got $($specRows.Count)"
    }
    foreach ($row in $specRows) {
        if ($row.StdMode -ne '65') {
            $fail += "non StdMode=65 item in spec: $($row.Name)"
        }
    }
}

if (Test-Path -LiteralPath $scriptPath) {
    $buffText = Get-Content -LiteralPath $scriptPath -Encoding ansi -Raw

    foreach ($needle in @(
            '[@军鼓BUFF_刷新]',
            '[@军鼓BUFF_应用当前模块]',
            '[@军鼓BUFF_关闭当前模块]',
            '[@军鼓BUFF_模块开启]',
            '[@军鼓BUFF_模块刷新]',
            '[@军鼓BUFF_刷新图标]',
            '[@军鼓BUFF_战斗确认]',
            '[@军鼓BUFF_攻击触发]',
            '[@军鼓BUFF_攻击掉血前]',
            '[@军鼓BUFF_被打掉血前]',
            '[@军鼓BUFF_宝宝掉血前]',
            '[@军鼓BUFF_死亡检查]',
            '[@军鼓BUFF_清理]',
            'CHECKUSEITEM 14',
            'GetItemFieldValue 14 name S$军鼓名称',
            '#CALL [系统功能\军鼓流派配置.txt] @军鼓配置_读取',
            'SetOnTimer 87 2',
            'SETOFFTIMER 87',
            'CloseArrBuff 1 87'
        )) {
        if ($buffText -notmatch [regex]::Escape($needle)) {
            $fail += "buff script missing $needle"
        }
    }
    foreach ($forbidden in @('ChangeSpeed', 'ChangeSlaveAbilityEX')) {
        if ($buffText -match [regex]::Escape($forbidden)) {
            $fail += "buff script should not use high-frequency $forbidden"
        }
    }
    if ($buffText -match [regex]::Escape('GOTO @军鼓BUFF_战斗确认')) {
        $fail += "buff combat labels must #CALL battle confirmation instead of GOTO"
    }
    if ($buffText -notmatch [regex]::Escape('#CALL [系统功能\军鼓BUFF.txt] @军鼓BUFF_战斗确认')) {
        $fail += "buff combat labels missing battle confirmation #CALL"
    }
    if ($buffText -notmatch 'MOV N\$军鼓当前品质 <\$STR\(N\$军鼓品质\)>[\r\n]+#CALL \[系统功能\\军鼓BUFF\.txt\] @军鼓BUFF_模块开启') {
        $fail += "buff refresh must open module after switching current item state"
    }
    foreach ($row in $specRows) {
        if ($buffText -match [regex]::Escape($row.Name)) {
            $fail += "item name should be in config, not main buff script: $($row.Name)"
        }
    }
} else {
    $fail += "missing script: $scriptPath"
}

if (Test-Path -LiteralPath $configPath) {
    $configText = Get-Content -LiteralPath $configPath -Encoding ansi -Raw
    $configLines = $configText -split "\r\n|\n|\r"
    $getStringPosExLine = $null
    $getStringPosExIndex = -1
    $insideConfigRead = $false
    $lastControl = ''
    for ($i = 0; $i -lt $configLines.Count; $i++) {
        $line = $configLines[$i].Trim()
        if ($line -eq '[@军鼓配置_读取]') {
            $insideConfigRead = $true
            continue
        }
        if ($insideConfigRead -and $line -match '^\[@') {
            break
        }
        if (-not $insideConfigRead -or $line -eq '') {
            continue
        }
        if ($line -match '^(#IF|#ACT|#ELSEACT|#ELSESAY|#SAY)\b') {
            $lastControl = $line
        }
        if ($line -match '^GetStringPosEX\b') {
            $getStringPosExLine = $line
            $getStringPosExIndex = $i + 1
            if ($lastControl -ne '#IF') {
                $fail += "GetStringPosEX must be in #IF condition block: $configPath line $getStringPosExIndex"
            }
        }
    }
    if ($null -eq $getStringPosExLine) {
        $fail += "config missing GetStringPosEX lookup: $configPath"
    }
    if ($getStringPosExLine -and $getStringPosExLine -notmatch '\s0\s*$') {
        $fail += "config GetStringPosEX must use relative-path flag 0: $configPath"
    }
    $extractStringLine = $configLines | Where-Object { $_ -match '^\s*ExtractStringEx\s+\|\s+<\$STR\(S\$军鼓配置文本\)>\s+S\$军鼓配置字段\s*$' }
    if (-not $extractStringLine) {
        $fail += "config must split the returned line with ExtractStringEx: $configPath"
    }
    foreach ($field in 1..7) {
        $fieldName = 'S$军鼓配置字段' + $field
        if ($configText -notmatch [regex]::Escape($fieldName)) {
            $fail += "config missing extracted field ${field}: $configPath"
        }
    }
    foreach ($row in $specRows) {
        $count = ([regex]::Matches($configText, '(?m)^' + [regex]::Escape($row.Name) + '\|')).Count
        if ($count -ne 1) {
            $fail += "config coverage error: $($row.Name) appears $count times"
        }
    }
    foreach ($needle in @(
            '[@军鼓配置_读取]',
            'N$军鼓品质',
            'N$军鼓阶段',
            'S$军鼓互斥组'
        )) {
        if ($configText -notmatch [regex]::Escape($needle)) {
            $fail += "config missing $needle"
        }
    }

    $configRows = @()
    foreach ($line in ($configText -split "\r\n|\n|\r")) {
        if ($line -match '^\s*;' -or $line -notmatch '\|') { continue }
        $parts = $line -split '\|'
        if ($parts.Count -eq 7 -and $parts[0] -ne 'Name') {
            $configRows += [pscustomobject]@{
                Name      = $parts[0]
                Job       = $parts[1]
                Direction = $parts[2]
                Quality   = $parts[3]
                Stage     = $parts[4]
                Group     = $parts[5]
                Module    = $parts[6]
            }
        }
    }

    if ($configRows.Count -ne 54) {
        $fail += "expected 54 config rows, got $($configRows.Count)"
    }
    foreach ($direction in @('拆门板', '铁头娃', '剁馅机', '电耗子', '火葫芦', '小冰箱', '养娃人', '奶不死', '毒嘴子')) {
        $count = @($configRows | Where-Object { $_.Direction -eq $direction }).Count
        if ($count -ne 6) {
            $fail += "direction $direction expected 6 rows, got $count"
        }
    }
    foreach ($quality in 1..6) {
        $count = @($configRows | Where-Object { $_.Quality -eq [string]$quality }).Count
        if ($count -ne 9) {
            $fail += "quality $quality expected 9 rows, got $count"
        }
    }
} else {
    $fail += "missing config: $configPath"
}

foreach ($module in @(
        @{ Path = $warriorPath; Name = 'warrior'; Directions = @('拆门板', '铁头娃', '剁馅机') },
        @{ Path = $wizardPath; Name = 'wizard'; Directions = @('电耗子', '火葫芦', '小冰箱') },
        @{ Path = $taoistPath; Name = 'taoist'; Directions = @('养娃人', '奶不死', '毒嘴子') }
    )) {
    if (Test-Path -LiteralPath $module.Path) {
        $moduleText = Get-Content -LiteralPath $module.Path -Encoding ansi -Raw
        foreach ($forbidden in @('ChangeSpeed', 'ChangeSlaveAbilityEX')) {
            if ($moduleText -match [regex]::Escape($forbidden)) {
                $fail += "$($module.Name) module should not use high-frequency $forbidden"
            }
        }
        foreach ($direction in $module.Directions) {
            foreach ($action in @('开启', '刷新', '关闭')) {
                $label = "[@军鼓$($module.Name)_$($action)_$direction]"
                if ($moduleText -notmatch [regex]::Escape($label)) {
                    $fail += "$($module.Name) module missing $label"
                }
            }
        }
    } else {
        $fail += "missing $($module.Name) module: $($module.Path)"
    }
}

if (Test-Path -LiteralPath $descPath) {
    $descText = Get-Content -LiteralPath $descPath -Encoding ansi -Raw
    foreach ($row in $specRows) {
        $count = ([regex]::Matches($descText, '(?m)^' + [regex]::Escape($row.Name) + '=')).Count
        if ($count -ne 1) {
            $fail += "ItemDescList coverage error: $($row.Name) appears $count times"
        }
    }
} else {
    $fail += "missing ItemDescList: $descPath"
}

if (Test-Path -LiteralPath $qFunction) {
    $qf = Get-Content -LiteralPath $qFunction -Encoding ansi -Raw
    foreach ($needle in @('@TakeOnEx', '@TakeOffEx', '@HumDropItem', '@AttackDamage', '@StruckDamage', '@SlaveAttackDamage')) {
        if ($qf -notmatch [regex]::Escape($needle)) {
            $fail += "QFunction-0 missing $needle"
        }
    }
    foreach ($needle in @(
            '#CALL [系统功能\军鼓BUFF.txt] @军鼓BUFF_刷新',
            '#CALL [系统功能\军鼓BUFF.txt] @军鼓BUFF_清理',
            '#CALL [系统功能\军鼓BUFF.txt] @军鼓BUFF_死亡检查',
            '#CALL [系统功能\军鼓BUFF.txt] @军鼓BUFF_攻击掉血前',
            '#CALL [系统功能\军鼓BUFF.txt] @军鼓BUFF_被打掉血前',
            '#CALL [系统功能\军鼓BUFF.txt] @军鼓BUFF_宝宝掉血前'
        )) {
        if ($qf -notmatch [regex]::Escape($needle)) {
            $fail += "QFunction-0 missing callback $needle"
        }
    }
} else {
    $fail += "missing qfunction: $qFunction"
}

if (Test-Path -LiteralPath $qManage) {
    $qm = Get-Content -LiteralPath $qManage -Encoding ansi -Raw
    foreach ($needle in @('@Login', '@OnTimer87')) {
        if ($qm -notmatch [regex]::Escape($needle)) {
            $fail += "QManage missing $needle"
        }
    }
    if ($qm -notmatch '\[@OnTimer87\][\s\S]*?#CALL \[系统功能\\军鼓BUFF\.txt\] @军鼓BUFF_刷新') {
        $fail += "QManage missing OnTimer87 buff refresh callback"
    }
    if ($qm -notmatch '\[@Login\][\s\S]*?#CALL \[系统功能\\军鼓BUFF\.txt\] @军鼓BUFF_刷新') {
        $fail += "QManage missing login buff refresh callback"
    }
} else {
    $fail += "missing qmanage: $qManage"
}

if (Test-Path -LiteralPath $attackPath) {
    $attack = Get-Content -LiteralPath $attackPath -Encoding ansi -Raw
    if ($attack -notmatch [regex]::Escape('#CALL [系统功能\军鼓BUFF.txt] @军鼓BUFF_攻击触发')) {
        $fail += "attack trigger missing buff callback"
    }
} else {
    $fail += "missing attack trigger: $attackPath"
}

if (Test-Path -LiteralPath $deathPath) {
    $death = Get-Content -LiteralPath $deathPath -Encoding ansi -Raw
    if ($death -notmatch [regex]::Escape('#CALL [系统功能\军鼓BUFF.txt] @军鼓BUFF_死亡检查')) {
        $fail += "death trigger missing buff death check"
    }
} else {
    $fail += "missing death trigger: $deathPath"
}

$callScanPaths = @(
    $scriptPath,
    $configPath,
    $warriorPath,
    $wizardPath,
    $taoistPath,
    $qFunction,
    $qManage,
    $attackPath,
    $deathPath
)
foreach ($sourcePath in $callScanPaths) {
    if (-not (Test-Path -LiteralPath $sourcePath)) { continue }
    $sourceText = $gbk.GetString([IO.File]::ReadAllBytes((Resolve-Path -LiteralPath $sourcePath).Path))
    foreach ($match in [regex]::Matches($sourceText, '#CALL\s+\[([^\]]+)\]\s+(@[^\s\r\n]+)')) {
        $callPath = $match.Groups[1].Value.Trim()
        $label = $match.Groups[2].Value.Trim()
        if ($callPath.StartsWith('\')) { continue }

        if ($callPath -match '^(系统功能|数据文件|攻击触发|游戏登陆|装备回收|老登辅助)\\') {
            $targetPath = Join-Path $base ('QuestDiary\' + $callPath)
        } else {
            $targetPath = Join-Path (Split-Path -Parent $sourcePath) $callPath
        }

        if (-not (Test-Path -LiteralPath $targetPath)) {
            $fail += "missing call file: $sourcePath -> $callPath $label"
            continue
        }

        $targetText = $gbk.GetString([IO.File]::ReadAllBytes((Resolve-Path -LiteralPath $targetPath).Path))
        if ($targetText -notmatch [regex]::Escape("[$label]")) {
            $fail += "missing call label: $sourcePath -> $callPath $label"
        }
    }
}

if ($fail.Count -gt 0) {
    $fail | ForEach-Object { Write-Host $_ }
    exit 1
}

Write-Host 'jungu buff static check ok'
