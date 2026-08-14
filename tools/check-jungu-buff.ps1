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
            'CloseArrBuff 87'
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
    foreach ($needle in @(
            '[@军鼓BUFF_生成图标说明]',
            '[@军鼓BUFF_触发反馈]',
            'S$军鼓图标说明',
            'S$军鼓触发说明',
            'S$军鼓触发记录',
            'N$军鼓触发成功',
            'CHECK [63] 1',
            'SENDMSG 7 【军鼓】'
        )) {
        if ($buffText -notmatch [regex]::Escape($needle)) {
            $fail += "buff script missing icon/feedback support $needle"
        }
    }
    if ($buffText -notmatch [regex]::Escape('SetArrBuff 1 87 0 <$STR(N$军鼓BUFF图标)> -1 0 0 0 <$STR(S$军鼓图标说明)>')) {
        $fail += 'main buff icon must use direction-specific persistent SetArrBuff button mode with detailed hover text'
    }
    foreach ($icon in 273..281) {
        if ($buffText -notmatch [regex]::Escape("MOV N`$军鼓BUFF图标 $icon")) {
            $fail += "main buff icon missing direction image $icon"
        }
    }
    foreach ($pair in @('剁馅机 282', '铁头娃 283', '拆门板 284', '小冰箱 287', '奶不死 285')) {
        $parts = $pair -split ' '
        if ($buffText -notmatch [regex]::Escape("EQUAL <`$STR(S`$军鼓当前方向)> $($parts[0])")) {
            $fail += "main buff head icon missing direction $($parts[0])"
        }
        if ($buffText -notmatch [regex]::Escape("MOV N`$军鼓头戴图标 $($parts[1])")) {
            $fail += "main buff head icon missing image $($parts[1])"
        }
    }
    if ($buffText -notmatch [regex]::Escape('SETICON 1 0 <$STR(N$军鼓头戴图标)> 44 -30 1 0 0 150 0')) {
        $fail += 'main buff missing self head icon SETICON on position 1'
    }
    if ($buffText -notmatch [regex]::Escape('SETICON 1 -1')) {
        $fail += 'main buff missing self head icon cleanup'
    }
    if ($buffText -match 'SetArrBuff\s+1\s+87\s+0\s+<\$STR\(N\$军鼓BUFF图标\)>\s+(?!-1\b)') {
        $fail += 'main buff icon must not use countdown mode'
    }
    if ($buffText -match '`n|`r') {
        $fail += 'buff script contains literal PowerShell newline escape text'
    }
    foreach ($forbiddenDetail in @('机制：', '安全：', '复核：', '清理：', '基础：', '记录：<$STR(S$军鼓触发记录)>', '2秒定时', '3秒短时', '脚本回收', '复核')) {
        if ($buffText -match [regex]::Escape($forbiddenDetail)) {
            $fail += "buff hover text contains developer detail $forbiddenDetail"
        }
    }
    foreach ($needle in @('名称：<$STR(S$军鼓当前名称)>', '玩法：', '触发：')) {
        if ($buffText -notmatch [regex]::Escape($needle)) {
            $fail += "buff hover text missing player detail $needle"
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
        $qualityExpectations = @(
            @{ Quality = 1; Point = 0; Big = 1; Percent = 0; Element = 0; HpMp = 20; Extra = 0; Proc = 0 },
            @{ Quality = 2; Point = 1; Big = 1; Percent = 1; Element = 0; HpMp = 40; Extra = 0; Proc = 0 },
            @{ Quality = 3; Point = 1; Big = 2; Percent = 1; Element = 1; HpMp = 70; Extra = 0; Proc = 15 },
            @{ Quality = 4; Point = 2; Big = 3; Percent = 2; Element = 2; HpMp = 120; Extra = 0; Proc = 25 },
            @{ Quality = 5; Point = 3; Big = 5; Percent = 3; Element = 3; HpMp = 180; Extra = 1; Proc = 35 },
            @{ Quality = 6; Point = 4; Big = 7; Percent = 4; Element = 4; HpMp = 260; Extra = 2; Proc = 45 }
        )
        foreach ($expect in $qualityExpectations) {
            $patternParts = @(
                "EQUAL N`$军鼓品质 $($expect.Quality)",
                "MOV N`$军鼓点 $($expect.Point)",
                "MOV N`$军鼓大点 $($expect.Big)",
                "MOV N`$军鼓百分 $($expect.Percent)",
                "MOV N`$军鼓元素 $($expect.Element)",
                "MOV N`$军鼓血蓝 $($expect.HpMp)",
                "MOV N`$军鼓顶级加码 $($expect.Extra)",
                "MOV N`$军鼓触发几率 $($expect.Proc)"
            ) | ForEach-Object { [regex]::Escape($_) }
            $pattern = $patternParts -join '[\s\S]*?'
            if ($moduleText -notmatch $pattern) {
                $fail += "$($module.Name) quality $($expect.Quality) does not match nerfed jungu curve"
            }
        }
        foreach ($needle in @(
                'RANDOMEX <$STR(N$军鼓触发几率)> 100',
                'N$军鼓触发几率'
            )) {
            if ($moduleText -notmatch [regex]::Escape($needle)) {
                $fail += "$($module.Name) module missing proc gate $needle"
            }
        }
        if ($moduleText -match [regex]::Escape('RANDOM <$STR(N$军鼓触发几率)>')) {
            $fail += "$($module.Name) module must not use inverse RANDOM with percent-style proc variable"
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
            continue
        }
        $lineMatch = [regex]::Match($descText, '(?m)^' + [regex]::Escape($row.Name) + '=.*$')
        $line = $lineMatch.Value
        foreach ($needle in @('14号位', '生效：', '玩法：', '触发：', '效果：', '品质：')) {
            if ($line -notmatch [regex]::Escape($needle)) {
                $fail += "ItemDescList detail missing $needle for $($row.Name)"
            }
        }
        foreach ($forbiddenDetail in @('复核：', '清理：', '基础：', '机制：', '安全：', '记录：', '2秒定时', '3秒短时', '脚本回收', '确认14号位仍是当前物品')) {
            if ($line -match [regex]::Escape($forbiddenDetail)) {
                $fail += "ItemDescList contains developer detail $forbiddenDetail for $($row.Name)"
            }
        }
        foreach ($oldWording in @('命中时结算', '实际受击时结算', '都会按流派结算', '成名以上会给目标挂雷痕', '成名以上会给目标挂火种')) {
            if ($line -match [regex]::Escape($oldWording)) {
                $fail += "ItemDescList still implies guaranteed old proc wording $oldWording for $($row.Name)"
            }
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
    foreach ($needle in @(
            '[@CloseArrBuff8]',
            'MOV S$军鼓雷痕',
            '[@CloseArrBuff4]',
            'MOV S$军鼓火种',
            '[@CloseArrBuff5]',
            'MOV S$军鼓毒印'
        )) {
        if ($qf -notmatch [regex]::Escape($needle)) {
            $fail += "QFunction-0 missing target buff cleanup $needle"
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
