param([int]$Port = 8765)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$env:GLUCOGUIDE_LOCAL_LLM = '1'
$env:GLUCOGUIDE_LOCAL_ONLY = '1'
$env:GLUCOGUIDE_LLAMA_URL = 'http://127.0.0.1:11435'
$env:GLUCOGUIDE_LLAMA_KEY_FILE = Join-Path $PSScriptRoot '.runtime/llama-api.key'
if (-not (Test-Path -LiteralPath $env:GLUCOGUIDE_LLAMA_KEY_FILE)) {
    $localKey = [guid]::NewGuid().ToString('N') + [guid]::NewGuid().ToString('N')
    Set-Content -LiteralPath $env:GLUCOGUIDE_LLAMA_KEY_FILE -Value $localKey -Encoding Ascii
}
$modelHeaders = @{ Authorization = 'Bearer ' + (Get-Content -LiteralPath $env:GLUCOGUIDE_LLAMA_KEY_FILE -Raw).Trim() }
$env:HF_HUB_OFFLINE = '1'
$env:TRANSFORMERS_OFFLINE = '1'
$env:PYTHONIOENCODING = 'utf-8'
try {
    $running = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/api/status" -TimeoutSec 2
    if ($running.local_only -and $running.local_llm) { Write-Host "GlucoGuide is already running at http://localhost:$Port"; return }
} catch {}
$modelFile = Join-Path $PSScriptRoot '.local-models/Qwen3-4B-Q4_K_M.gguf'
$serverFile = Join-Path $PSScriptRoot '.runtime/llama-vulkan/llama-server.exe'
if (-not (Test-Path -LiteralPath $modelFile) -or -not (Test-Path -LiteralPath $serverFile)) {
    throw 'Run .venv-llm/Scripts/python.exe scripts/setup_local_qwen4.py first.'
}
$modelReady = $false
try { $health = Invoke-RestMethod -Uri 'http://127.0.0.1:11435/health' -Headers $modelHeaders -TimeoutSec 2; $modelReady = $health.status -eq 'ok' } catch {}
if (-not $modelReady) {
    $arguments = @('-m', $modelFile, '--host', '127.0.0.1', '--port', '11435', '--device', 'Vulkan0', '-ngl', '99', '-c', '8192', '-np', '1', '-t', '6', '--jinja', '--no-webui', '--api-key-file', $env:GLUCOGUIDE_LLAMA_KEY_FILE)
    Start-Process -FilePath $serverFile -ArgumentList $arguments -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -RedirectStandardOutput '.runtime/llama-server.out.log' -RedirectStandardError '.runtime/llama-server.err.log'
    for ($attempt = 0; $attempt -lt 40; $attempt++) {
        Start-Sleep -Seconds 1
        try { $health = Invoke-RestMethod -Uri 'http://127.0.0.1:11435/health' -Headers $modelHeaders -TimeoutSec 2; if ($health.status -eq 'ok') { $modelReady = $true; break } } catch {}
    }
}
if (-not $modelReady) { throw 'Local Qwen server did not become ready. See .runtime/llama-server.err.log.' }
Write-Host "GlucoGuide local: http://localhost:$Port"
& ./.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port $Port
