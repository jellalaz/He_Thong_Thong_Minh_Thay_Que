#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
bash run-macos.sh start
open http://localhost:8765
