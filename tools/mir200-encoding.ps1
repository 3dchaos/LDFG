param(
    [string[]]$Path = @('AGENTS.md', 'docs', '.vscode', 'Mir200\Envir'),
    [switch]$Json
)

. "$PSScriptRoot\mir200-common.ps1"

$results = foreach ($item in $Path) {
    if (-not (Test-Path -LiteralPath $item)) { continue }

    $files = if ((Get-Item -LiteralPath $item).PSIsContainer) {
        Get-ChildItem -LiteralPath $item -Recurse -File
    } else {
        Get-Item -LiteralPath $item
    }

    foreach ($file in $files) {
        $encoding = Get-Mir200Encoding -Path $file.FullName
        [pscustomobject]@{
            Path     = Resolve-Path -LiteralPath $file.FullName -Relative
            Encoding = if ($encoding.CodePage -eq 936) { 'gbk' } else { 'utf8' }
        }
    }
}

if ($Json) {
    $results | ConvertTo-Json -Depth 4
} else {
    $results | Format-Table -AutoSize
}
