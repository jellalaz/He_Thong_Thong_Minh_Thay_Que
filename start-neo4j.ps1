$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$neoHome = Join-Path $PSScriptRoot '.runtime/neo4j-community-2026.10.1'
if ($env:NEO4J_HOME) { $neoHome = $env:NEO4J_HOME }
if (-not (Test-Path (Join-Path $neoHome 'bin/neo4j.bat'))) { throw 'Không thấy Neo4j. Cài Neo4j hoặc dùng docker compose up -d neo4j theo README.md.' }
if (-not $env:JAVA_HOME) { $env:JAVA_HOME = 'C:\Program Files\Eclipse Adoptium\jdk-21.0.13.9-hotspot' }
& (Join-Path $neoHome 'bin/neo4j.bat') console
