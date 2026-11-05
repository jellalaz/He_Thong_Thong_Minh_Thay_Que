$env:GLUCOGUIDE_LOCAL_LLM='1'
$env:HF_HUB_OFFLINE='1'
$env:TRANSFORMERS_OFFLINE='1'
Set-Location -LiteralPath $PSScriptRoot
& ./.venv-llm/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8766
