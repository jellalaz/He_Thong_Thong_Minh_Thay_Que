if (Test-Path (Join-Path $PSScriptRoot '.local-models/Qwen3-4B-Q4_K_M.gguf')) {
    & (Join-Path $PSScriptRoot 'run-chatbot-local.ps1') -Port 8766
    exit
}
$env:GLUCOGUIDE_LOCAL_LLM='1'
$env:GLUCOGUIDE_LOCAL_ONLY='1'
$env:HF_HUB_OFFLINE='1'
$env:TRANSFORMERS_OFFLINE='1'
Set-Location -LiteralPath $PSScriptRoot
& ./.venv-llm/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8766
