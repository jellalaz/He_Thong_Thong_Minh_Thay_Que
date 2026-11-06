$ErrorActionPreference="Stop"
Set-Location $PSScriptRoot
& (Join-Path $PSScriptRoot 'run-chatbot-local.ps1')
