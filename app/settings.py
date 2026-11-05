"""Configuration shared by local runs, graph imports and cloud deployments."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_environment():
    path = Path(os.environ.get("GLUCOGUIDE_ENV_FILE", ROOT / ".env"))
    if path.exists():
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip().strip('"\''))


load_environment()


def database():
    return os.environ.get("NEO4J_DATABASE", "neo4j")


def browser_url():
    configured = os.environ.get("NEO4J_BROWSER_URL")
    if configured:
        return configured
    if os.environ.get("VERCEL") or "databases.neo4j.io" in os.environ.get("NEO4J_URI", ""):
        return "https://console.neo4j.io/"
    return "http://localhost:7474/browser/"
