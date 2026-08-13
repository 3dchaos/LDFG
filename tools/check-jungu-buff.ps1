param(
    [string]$Root = (Resolve-Path '.').Path
)

$ErrorActionPreference = 'Stop'

$base = Join-Path $Root 'Mir200\Envir'
$scriptPath = Join-Path $base 'QuestDiary\系统功能\军鼓BUFF.txt'
$qFunction = Join-Path $base 'Market_def\QFunction-0.txt'
$qManage = Join-Path $base 'MapQuest_def\QManage.txt'
$attackPath = Join-Path $base 'QuestDiary\系统功能\老登辅助\攻击触发.txt'
$deathPath = Join-Path $base 'QuestDiary\系统功能\老登辅助\死亡触发.txt'
$specPath = Join-Path $Root 'docs\军鼓位玩法StdItems.csv'

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
    foreach ($row in $specRows) {
        $count = ([regex]::Matches($buffText, [regex]::Escape($row.Name))).Count
        if ($count -ne 1) {
            $fail += "item name coverage error: $($row.Name) appears $count times"
        }
    }

    foreach ($needle in @(
            '[@军鼓BUFF_刷新]',
            '[@军鼓BUFF_应用]',
            '[@军鼓BUFF_战斗确认]',
            '[@军鼓BUFF_攻击触发]',
            '[@军鼓BUFF_攻击掉血前]',
            '[@军鼓BUFF_被打掉血前]',
            '[@军鼓BUFF_宝宝掉血前]',
            '[@军鼓BUFF_死亡检查]',
            '[@军鼓BUFF_清理]',
            'CHECKUSEITEM 14',
            'GetItemFieldValue 14 name S$军鼓名称',
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
} else {
    $fail += "missing script: $scriptPath"
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

if ($fail.Count -gt 0) {
    $fail | ForEach-Object { Write-Host $_ }
    exit 1
}

Write-Host 'jungu buff static check ok'
