param([switch]$Apply)
$ErrorActionPreference = 'Stop'
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..')).TrimEnd('\')
$prefix = $projectRoot + '\'

# Reviewed, expendable artifacts only. Keep databases, active runtimes, models and secrets.
$relativePaths = @(
    '.local-models/download-parts',
    '.local-models/hf-cache', '.local-models/qwen4-parts',
    '.runtime/llama-cpp',
    '.runtime/llama-b12128-bin-win-cuda-12.4-x64.zip',
    '.runtime/llama-b12128-bin-win-vulkan-x64.zip',
    '.runtime/neo4j.zip', '.runtime/pandoc.zip', '.runtime/tectonic.zip',
    '.runtime/cloudflared.exe', '.runtime/pdf-qa',
    '.runtime/tunnel-new.stderr.log', '.runtime/tunnel-new.stdout.log',
    '.runtime/tunnel.stderr.log', '.runtime/tunnel.stdout.log',
    '.runtime/api.stderr.log', '.runtime/api.stdout.log',
    '.runtime/web.stderr.log', '.runtime/web.stdout.log',
    '.runtime/local-qwen.err.log', '.runtime/local-qwen.out.log', '.runtime/local-qwen.pid',
    '.runtime/complete_graph.py', '.runtime/update_reports_current.py', '.runtime/finalize_sources.py',
    '.runtime/probe_generation.py', '.runtime/refine_reports.py',
    '.runtime/dialogue-comparison.json', '.runtime/dialogue-live-checks.json', '.runtime/safety-offline-results.json',
    'app/__pycache__', 'scripts/__pycache__', 'experiments/local_qwen/__pycache__',
    'README.txt', 'reports/converted.tex', 'reports/legacy.tex',
    'reports/demo-chat.png', 'reports/demo-graph.png', 'reports/demo-local-context.png',
    'reports/demo-local-qwen.png', 'reports/demo-sources.png',
    'results/graph_ui_desktop.png'
)
$relativePaths += Get-ChildItem -LiteralPath (Join-Path $projectRoot 'reports') -File |
    Where-Object { $_.Extension -in @('.aux','.log','.out','.toc','.lof','.lot','.xdv','.fls','.fdb_latexmk') -or $_.Name.EndsWith('.synctex.gz') } |
    ForEach-Object { 'reports/' + $_.Name }

# Download parts are disposable only after validating the standalone completed model.
$modelPath = Join-Path $projectRoot '.local-models/Qwen3-1.7B/model.safetensors'
if (-not (Test-Path -LiteralPath $modelPath)) { throw 'Completed model is missing; keep download parts.' }
$modelItem = Get-Item -LiteralPath $modelPath
if ($modelItem.LinkType -or $modelItem.Length -ne 3441185608) { throw 'Expected a standalone complete base model.' }
if ((Get-FileHash -LiteralPath $modelPath -Algorithm SHA256).Hash -ne '169AD53EC313C3A34B06C0809216E4FC072CCE444A5D4FF2B59690D064130ED5') { throw 'Base model checksum mismatch.' }
foreach ($baseFile in @('config.json','tokenizer.json','tokenizer_config.json','generation_config.json')) {
    if (-not (Test-Path -LiteralPath (Join-Path $projectRoot ('.local-models/Qwen3-1.7B/' + $baseFile)))) { throw "Keep model cache: missing $baseFile" }
}
foreach ($required in @('.runtime/llama-vulkan/llama-server.exe','.local-models/Qwen3-4B-Q4_K_M.gguf','.runtime/tectonic/tectonic.exe','.runtime/pandoc/pandoc-3.13/pandoc.exe','.runtime/neo4j-community-2026.10.1/bin/neo4j.bat')) {
    if (-not (Test-Path -LiteralPath (Join-Path $projectRoot $required))) { throw "Keep archives: missing $required" }
}

$activeExecutables = @(Get-CimInstance Win32_Process | Where-Object ExecutablePath | ForEach-Object { $_.ExecutablePath })
$items = @()
foreach ($relative in ($relativePaths | Select-Object -Unique)) {
    $target = [IO.Path]::GetFullPath((Join-Path $projectRoot $relative))
    if (-not $target.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) { throw "Unsafe path: $relative" }
    if (-not (Test-Path -LiteralPath $target)) { continue }
    $item = Get-Item -LiteralPath $target -Force
    if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Refuse linked target: $relative" }
    $files = if ($item.PSIsContainer) { @(Get-ChildItem -LiteralPath $target -File -Recurse -Force) } else { @($item) }
    if ($item.PSIsContainer -and (Get-ChildItem -LiteralPath $target -Recurse -Force | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint })) { throw "Refuse nested links: $relative" }
    foreach ($executable in $activeExecutables) {
        if ($executable -eq $target -or $executable.StartsWith($target + '\',[StringComparison]::OrdinalIgnoreCase)) { throw "Target still running: $relative" }
    }
    $bytes = ($files | Measure-Object -Property Length -Sum).Sum
    $items += [pscustomobject]@{ path=$relative; bytes=[long]$bytes; files=$files.Count; absolute=$target }
}
$total = ($items | Measure-Object -Property bytes -Sum).Sum
Write-Output ("{0} targets, {1:N2} GiB in files; apply={2}" -f $items.Count,($total/1GB),$Apply.IsPresent)
if (-not $Apply) { $items | Select-Object path,bytes,files; return }
if ($items.Count -eq 0) { Write-Output 'No generated artifacts need removal.'; return }
$record = [ordered]@{ completed_at=(Get-Date -Format o); bytes_removed=[long]$total; files_removed=($items | Measure-Object -Property files -Sum).Sum; items=@($items | Select-Object path,bytes,files) }
$manifestPath = Join-Path $projectRoot 'results/cleanup_manifest.json'
$runs = @()
if (Test-Path -LiteralPath $manifestPath) {
    $previous = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
    $runs = @(if ($previous.runs) { $previous.runs } else { $previous })
}
$runs = @($runs) + @([pscustomobject]$record)
$manifest = [ordered]@{ schema_version=2; bytes_removed=[long](($runs | Measure-Object -Property bytes_removed -Sum).Sum); known_files_removed=[long](($runs | Measure-Object -Property files_removed -Sum).Sum); file_count_complete=(@($runs | Where-Object { $null -eq $_.files_removed }).Count -eq 0); runs=$runs }
$manifestJson = $manifest | ConvertTo-Json -Depth 7
foreach ($item in $items) { Remove-Item -LiteralPath $item.absolute -Recurse -Force }
$manifestJson | Set-Content -LiteralPath $manifestPath -Encoding utf8
Write-Output 'Removed reviewed artifacts; active resources were kept.'
