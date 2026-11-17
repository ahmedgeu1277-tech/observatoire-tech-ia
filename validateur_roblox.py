"""Analyse statique de sécurité pour les projets Roblox générés.

Ce contrôle lit les fichiers Luau sans les exécuter. Il détecte quelques
motifs dangereux connus ; ce n'est ni un sandbox ni une certification.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

REQUIRED_FILES = (
    "default.project.json",
    "src/shared/Config.lua",
    "src/server/PlayerSetup.server.lua",
    "src/server/CoinPickup.server.lua",
    "src/client/ClientStatus.client.lua",
)
DANGEROUS_PATTERNS = (
    ("critical", re.compile(r"\bloadstring\s*\("), "exécution dynamique de code"),
    ("high", re.compile(r"\brequire\s*\(\s*\d+\s*\)"), "chargement d'un asset par identifiant numérique"),
    ("high", re.compile(r"\bHttpService\s*:\s*(?:GetAsync|PostAsync|RequestAsync)\s*\("), "requête réseau depuis un script"),
    ("high", re.compile(r"\bInsertService\s*:\s*LoadAsset\s*\("), "chargement dynamique d'asset"),
    ("high", re.compile(r"\bTeleportService\s*:\s*Teleport(?:Async)?\s*\("), "téléportation déclenchée par script"),
)
CLIENT_WRITE_PATTERN = re.compile(
    r"\b(?:leaderstats|Coins|coins)\b[^\n]*(?:\.Value\s*(?:\+|-|\*|/)?=|\+=|-=)"
)


def _inside(root: Path, candidate: Path) -> bool:
    try:
        candidate.resolve().relative_to(root)
        return True
    except (OSError, ValueError):
        return False


def validate_project(project_dir: str | Path) -> dict:
    root = Path(project_dir).expanduser().resolve()
    findings: list[dict] = []
    if not root.is_dir():
        return {
            "status": "failed",
            "project": str(root),
            "files_scanned": 0,
            "findings": [{"severity": "critical", "file": ".", "line": 0, "message": "Dossier de projet introuvable."}],
            "limitations": "Analyse statique uniquement ; aucun code Luau n'est exécuté.",
        }

    existing: dict[str, Path] = {}
    for relative in REQUIRED_FILES:
        candidate = root / relative
        if not _inside(root, candidate):
            findings.append({"severity": "critical", "file": relative, "line": 0, "message": "Chemin sortant du projet ou lien symbolique suspect."})
        elif not candidate.is_file():
            findings.append({"severity": "high", "file": relative, "line": 0, "message": "Fichier indispensable manquant."})
        else:
            existing[relative] = candidate

    project_file = existing.get("default.project.json")
    if project_file:
        try:
            config = json.loads(project_file.read_text(encoding="utf-8"))
            tree = config.get("tree", {})
            for service in ("ReplicatedStorage", "ServerScriptService", "StarterPlayer"):
                if service not in tree:
                    findings.append({"severity": "high", "file": "default.project.json", "line": 0, "message": f"Service Rojo absent : {service}."})
            for value in re.findall(r'"\$path"\s*:\s*"([^"]+)"', project_file.read_text(encoding="utf-8")):
                if value.startswith(("/", "\\")) or ".." in Path(value).parts:
                    findings.append({"severity": "critical", "file": "default.project.json", "line": 0, "message": "Chemin Rojo absolu ou avec traversée détecté."})
        except (OSError, json.JSONDecodeError, AttributeError):
            findings.append({"severity": "critical", "file": "default.project.json", "line": 0, "message": "Configuration JSON Rojo invalide."})

    lua_files = sorted(root.rglob("*.lua"))
    scanned = 0
    for path in lua_files:
        relative = path.relative_to(root).as_posix()
        if not _inside(root, path):
            findings.append({"severity": "critical", "file": relative, "line": 0, "message": "Fichier Luau lié hors du projet."})
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            findings.append({"severity": "high", "file": relative, "line": 0, "message": "Fichier Luau illisible."})
            continue
        scanned += 1
        for line_number, line in enumerate(content.splitlines(), start=1):
            for severity, pattern, message in DANGEROUS_PATTERNS:
                if pattern.search(line):
                    findings.append({"severity": severity, "file": relative, "line": line_number, "message": message})
            if relative.startswith("src/client/") and CLIENT_WRITE_PATTERN.search(line):
                findings.append({"severity": "critical", "file": relative, "line": line_number, "message": "Le client semble modifier des statistiques ou la monnaie."})

    server_coin = existing.get("src/server/CoinPickup.server.lua")
    if server_coin:
        content = server_coin.read_text(encoding="utf-8")
        if "GetPlayerFromCharacter" not in content or "IntValue" not in content:
            findings.append({"severity": "high", "file": "src/server/CoinPickup.server.lua", "line": 0, "message": "Validation serveur du joueur ou du type de donnée absente."})

    failed = any(item["severity"] in {"critical", "high"} for item in findings)
    return {
        "status": "failed" if failed else "passed",
        "project": str(root),
        "files_scanned": scanned,
        "findings": findings,
        "limitations": "Analyse statique uniquement ; elle ne prouve pas l'absence de vulnérabilité et ne remplace pas les tests dans Roblox Studio.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Contrôle statique d'un projet Roblox.")
    parser.add_argument("project_dir", help="Dossier du projet Roblox/Rojo")
    args = parser.parse_args()
    report = validate_project(args.project_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
