param(
    [string]$Root = (Resolve-Path '.').Path
)

$ErrorActionPreference = 'Stop'
$gbk = [Text.Encoding]::GetEncoding(936)
$envir = Join-Path $Root 'Mir200\Envir'
$buffPath = Join-Path $envir 'QuestDiary\系统功能\军鼓BUFF.txt'
$warriorPath = Join-Path $envir 'QuestDiary\系统功能\军鼓流派\战士军鼓.txt'
$wizardPath = Join-Path $envir 'QuestDiary\系统功能\军鼓流派\法师军鼓.txt'
$taoistPath = Join-Path $envir 'QuestDiary\系统功能\军鼓流派\道士军鼓.txt'
$ratePath = Join-Path $envir 'QuestDiary\系统功能\倍率结算.txt'
$qManagePath = Join-Path $envir 'MapQuest_def\QManage.txt'
$setupPath = Join-Path $Root 'Mir200\!setup.txt'
$targetPaths = @($buffPath, $warriorPath, $wizardPath, $taoistPath, $ratePath)
$fail = @()

function Read-GbkText {
    param([string]$Path)

    return $gbk.GetString([IO.File]::ReadAllBytes((Resolve-Path -LiteralPath $Path).Path))
}

function Get-LabelBlock {
    param(
        [string]$Text,
        [string]$Label
    )

    $pattern = '(?ms)^\[' + [regex]::Escape($Label) + '\]\s*(.*?)(?=^\[@|\z)'
    return [regex]::Match($Text, $pattern)
}

function Test-CallCycle {
    param(
        [string]$Node,
        [hashtable]$Graph,
        [hashtable]$State
    )

    if ($State[$Node] -eq 1) { return $true }
    if ($State[$Node] -eq 2) { return $false }

    $State[$Node] = 1
    foreach ($target in $Graph[$Node]) {
        if (Test-CallCycle -Node $target -Graph $Graph -State $State) {
            return $true
        }
    }
    $State[$Node] = 2
    return $false
}

foreach ($path in $targetPaths) {
    if (-not (Test-Path -LiteralPath $path)) {
        $fail += "missing target script: $path"
        continue
    }

    $text = Read-GbkText -Path $path
    $sourceName = [IO.Path]::GetFileName($path)
    foreach ($match in [regex]::Matches($text, '(?m)^\s*#CALL\s+\[([^\]]+\.txt)\]\s+(@[^\s\r\n]+)\s*$')) {
        if ([IO.Path]::GetFileName($match.Groups[1].Value) -ieq $sourceName) {
            $target = $match.Groups[2].Value
            if ($text -notmatch [regex]::Escape("[$target]")) {
                $fail += "missing same-file #CALL label: $path -> $target"
            }
        }
    }

    foreach ($match in [regex]::Matches($text, '(?m)^\s*GOTO\s+(@[^\s\r\n(]+)')) {
        $target = $match.Groups[1].Value
        if ($text -notmatch [regex]::Escape("[$target]")) {
            $fail += "missing GOTO label: $path -> $target"
        }
    }

    $graph = @{}
    foreach ($block in [regex]::Matches($text, '(?ms)^\[(?<label>@[^\]]+)\]\s*(?<body>.*?)(?=^\[@|\z)')) {
        $label = $block.Groups['label'].Value
        $targets = [Collections.Generic.List[string]]::new()
        foreach ($match in [regex]::Matches($block.Groups['body'].Value, '(?m)^\s*GOTO\s+(@[^\s\r\n(]+)')) {
            $targets.Add($match.Groups[1].Value)
        }
        foreach ($match in [regex]::Matches($block.Groups['body'].Value, '(?m)^\s*#CALL\s+\[([^\]]+\.txt)\]\s+(@[^\s\r\n]+)\s*$')) {
            if ([IO.Path]::GetFileName($match.Groups[1].Value) -ieq $sourceName) {
                $targets.Add($match.Groups[2].Value)
            }
        }
        $graph[$label] = $targets
    }

    $state = @{}
    foreach ($label in $graph.Keys) {
        if (Test-CallCycle -Node $label -Graph $graph -State $state) {
            $fail += "same-file call cycle detected: $path -> $label"
            break
        }
    }
}

if (Test-Path -LiteralPath $setupPath) {
    $setupText = Read-GbkText -Path $setupPath
    $limitMatch = [regex]::Match($setupText, '(?m)^LimitScriptGotoCount=(\d+)\s*$')
    if (-not $limitMatch.Success) {
        $fail += 'Mir200 !setup.txt missing LimitScriptGotoCount'
    } elseif ([int]$limitMatch.Groups[1].Value -lt 100) {
        $fail += "LimitScriptGotoCount must be at least 100; current value is $($limitMatch.Groups[1].Value)"
    }
} else {
    $fail += "missing Mir200 setup: $setupPath"
}

if (Test-Path -LiteralPath $qManagePath) {
    $qManageText = Read-GbkText -Path $qManagePath
    $timerBlock = Get-LabelBlock -Text $qManageText -Label '@OnTimer87'
    if (-not $timerBlock.Success) {
        $fail += 'QManage missing @OnTimer87'
    } else {
        $timerText = $timerBlock.Groups[1].Value
        if ($timerText -notmatch [regex]::Escape('#CALL [系统功能\军鼓BUFF.txt] @军鼓BUFF_定时检查')) {
            $fail += 'QManage @OnTimer87 must call @军鼓BUFF_定时检查'
        }
        if ($timerText -match [regex]::Escape('@军鼓BUFF_刷新')) {
            $fail += 'QManage @OnTimer87 must not call the full buff refresh'
        }
    }
} else {
    $fail += "missing QManage: $qManagePath"
}

if (Test-Path -LiteralPath $buffPath) {
    $buffText = Read-GbkText -Path $buffPath
    $timerCheck = Get-LabelBlock -Text $buffText -Label '@军鼓BUFF_定时检查'
    if (-not $timerCheck.Success) {
        $fail += 'buff script missing @军鼓BUFF_定时检查'
    } else {
        foreach ($needle in @(
                'NOT CHECKUSEITEM 14',
                'GetItemFieldValue 14 name S$军鼓确认名',
                'EQUAL <$STR(S$军鼓确认名)> <$STR(S$军鼓当前名称)>',
                'EQUAL N$军鼓需要刷新 1',
                'MOV N$军鼓职业确认 0',
                'MOV S$军鼓校验职业 <$STR(S$军鼓当前职业)>',
                '#CALL [系统功能\军鼓BUFF.txt] @军鼓BUFF_职业确认',
                'EQUAL N$军鼓职业确认 0',
                '#CALL [系统功能\军鼓BUFF.txt] @军鼓BUFF_刷新',
                '#CALL [系统功能\军鼓BUFF.txt] @军鼓BUFF_清理',
                '#CALL [系统功能\军鼓BUFF.txt] @军鼓BUFF_定时续期'
            )) {
            if ($timerCheck.Groups[1].Value -notmatch [regex]::Escape($needle)) {
                $fail += "timer check missing: $needle"
            }
        }
    }

    $deathCheck = Get-LabelBlock -Text $buffText -Label '@军鼓BUFF_死亡检查'
    if (-not $deathCheck.Success -or $deathCheck.Groups[1].Value -notmatch [regex]::Escape('MOV N$军鼓需要刷新 1')) {
        $fail += 'death check must request one full refresh'
    }

    $refresh = Get-LabelBlock -Text $buffText -Label '@军鼓BUFF_刷新'
    if (-not $refresh.Success -or $refresh.Groups[1].Value -notmatch [regex]::Escape('MOV N$军鼓需要刷新 0')) {
        $fail += 'full refresh must clear the pending refresh flag'
    }

    $renew = Get-LabelBlock -Text $buffText -Label '@军鼓BUFF_定时续期'
    if (-not $renew.Success) {
        $fail += 'buff script missing @军鼓BUFF_定时续期'
    } else {
        foreach ($needle in @(
                '#CALL [系统功能\军鼓流派\战士军鼓.txt] @军鼓warrior_定时续期',
                '#CALL [系统功能\军鼓BUFF.txt] @军鼓BUFF_刷新战士攻速',
                '#CALL [系统功能\军鼓流派\法师军鼓.txt] @军鼓wizard_定时续期',
                '#CALL [系统功能\军鼓BUFF.txt] @军鼓BUFF_刷新法师施法速度',
                '#CALL [系统功能\军鼓流派\道士军鼓.txt] @军鼓taoist_定时续期'
            )) {
            if ($renew.Groups[1].Value -notmatch [regex]::Escape($needle)) {
                $fail += "timer renew missing dispatch: $needle"
            }
        }
    }
}

$renewExpectations = @(
    @{
        Path = $warriorPath
        Label = '@军鼓warrior_定时续期'
        Needles = @(
            'ChangeHumAbility 1 = <$STR(N$军鼓点)> 3',
            'ChangeHumAbility 2 = <$STR(N$军鼓大点)> 3',
            'ChangeHumAbility 11 = <$STR(N$军鼓血蓝)> 3',
            'AddHumNewValue 4 = <$STR(N$军鼓破防)> 3',
            'AddHumNewValue 2 = <$STR(N$军鼓物伤减)> 3',
            'AddHumNewValue 3 = <$STR(N$军鼓魔伤减)> 3',
            'AddHumNewValue 19 = <$STR(N$军鼓防冰)> 3',
            'AddHumNewValue 24 = <$STR(N$军鼓暴抗)> 3',
            'ChangeHumAbility 19 = <$STR(N$军鼓准确)> 3',
            'ChangeState 10 3 100 <$STR(N$军鼓吸血)>'
        )
    },
    @{
        Path = $wizardPath
        Label = '@军鼓wizard_定时续期'
        Needles = @(
            'ChangeHumAbility 7 = <$STR(N$军鼓点)> 3',
            'ChangeHumAbility 8 = <$STR(N$军鼓大点)> 3',
            'ChangeHumAbility 12 = <$STR(N$军鼓血蓝)> 3',
            'AddHumNewValue 1 = <$STR(N$军鼓元素)> 3',
            'ChangeHumAbility 18 = <$STR(N$军鼓点)> 3',
            'ChangeHumAbility 3 = <$STR(N$军鼓点)> 3',
            'ChangeHumAbility 4 = <$STR(N$军鼓大点)> 3',
            'ChangeHumAbility 11 = <$STR(N$军鼓血蓝)> 3',
            'AddHumNewValue 3 = <$STR(N$军鼓元素)> 3',
            'AddHumNewValue 19 = <$STR(N$军鼓元素)> 3',
            'ChangeState 11 3 100 <$STR(N$军鼓吸蓝)>'
        )
    },
    @{
        Path = $taoistPath
        Label = '@军鼓taoist_定时续期'
        Needles = @(
            'ChangeHumAbility 9 = <$STR(N$军鼓点)> 3',
            'ChangeHumAbility 10 = <$STR(N$军鼓大点)> 3',
            'ChangeHumAbility 11 = <$STR(N$军鼓血蓝)> 3',
            'ChangeHumAbility 12 = <$STR(N$军鼓血蓝)> 3',
            'ChangeHumAbility 14 = <$STR(N$军鼓恢复)> 3',
            'ChangeHumAbility 15 = <$STR(N$军鼓恢复)> 3',
            'AddHumNewValue 11 = <$STR(N$军鼓爆率)> 3',
            'AddHumNewValue 13 = <$STR(N$军鼓元素)> 3',
            'AddHumNewValue 16 = <$STR(N$军鼓元素)> 3',
            'AddHumNewValue 18 = <$STR(N$军鼓元素)> 3',
            'AddHumNewValue 19 = <$STR(N$军鼓元素)> 3',
            'AddHumNewValue 20 = <$STR(N$军鼓元素)> 3',
            'AddHumNewValue 24 = <$STR(N$军鼓元素)> 3',
            '#CALL [系统功能\军鼓流派\道士军鼓.txt] @军鼓taoist_养娃人_召唤检查',
            'HumanHP + <$STR(N$军鼓恢复)> 100 1',
            'HumanMP + <$STR(N$军鼓恢复)> 100 1',
            'BB.HumanHP + <$STR(N$军鼓恢复)> 500 1',
            'ChangeHumAbility 16 = <$STR(N$军鼓大点)> 3',
            'ChangeHumAbility 17 = <$STR(N$军鼓大点)> 3',
            'ChangeHumAbility 18 = <$STR(N$军鼓点)> 3',
            'AddHumNewValue 0 = <$STR(N$军鼓元素)> 3'
        )
    }
)

foreach ($expectation in $renewExpectations) {
    if (-not (Test-Path -LiteralPath $expectation.Path)) { continue }
    $moduleText = Read-GbkText -Path $expectation.Path
    $renew = Get-LabelBlock -Text $moduleText -Label $expectation.Label
    if (-not $renew.Success) {
        $fail += "module missing $($expectation.Label): $($expectation.Path)"
        continue
    }
    foreach ($needle in $expectation.Needles) {
        if ($renew.Groups[1].Value -notmatch [regex]::Escape($needle)) {
            $fail += "$($expectation.Label) missing: $needle"
        }
    }
}

if ($fail.Count -gt 0) {
    $fail | ForEach-Object { Write-Host $_ }
    exit 1
}

Write-Host 'jungu dead-loop static check ok'
