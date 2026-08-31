param(
    [string]$Root = (Resolve-Path '.').Path
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'mir200-common.ps1')

$path = Join-Path $Root 'Mir200\Envir\QuestDiary\系统功能\军鼓BUFF.txt'
$text = Read-Mir200Text -Path $path
$newLine = Get-Mir200NewLine -Text $text
$old = @'
#IF
EQUAL N$军鼓需要刷新 1
#ACT
#CALL [系统功能\军鼓BUFF.txt] @军鼓BUFF_刷新
BREAK

#IF
#ACT
#CALL [系统功能\军鼓BUFF.txt] @军鼓BUFF_定时续期
'@
$new = @'
#IF
EQUAL N$军鼓需要刷新 1
#ACT
#CALL [系统功能\军鼓BUFF.txt] @军鼓BUFF_刷新
BREAK

#IF
#ACT
MOV N$军鼓职业确认 0
MOV S$军鼓校验职业 <$STR(S$军鼓当前职业)>
#CALL [系统功能\军鼓BUFF.txt] @军鼓BUFF_职业确认

#IF
EQUAL N$军鼓职业确认 0
#ACT
#CALL [系统功能\军鼓BUFF.txt] @军鼓BUFF_清理
BREAK

#IF
#ACT
#CALL [系统功能\军鼓BUFF.txt] @军鼓BUFF_定时续期
'@
$old = [regex]::Replace($old.Trim(), '\r\n|\n|\r', $newLine)
$new = [regex]::Replace($new.Trim(), '\r\n|\n|\r', $newLine)
$count = ([regex]::Matches($text, [regex]::Escape($old))).Count
if ($count -ne 1) {
    throw "expected one timer guard anchor; found $count"
}

Write-Mir200Text -Path $path -Text $text.Replace($old, $new)
Write-Host 'jungu timer job guard applied'
