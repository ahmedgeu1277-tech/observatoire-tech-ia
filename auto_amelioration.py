"""Boucle bornée d'auto-évaluation et d'amélioration continue.

Le système agit comme un testeur/utilisateur synthétique : il exécute uniquement
des contrôles autorisés, mesure les résultats et produit un backlog priorisé.
Il ne modifie pas le code de production et ne déploie rien automatiquement.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ALLOWED_CHECKS = {
    "python_tests": [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
    "python_syntax": [sys.executable, "-m", "compileall", "-q", "."],
    "healthcheck": [sys.executable, "healthcheck.py"],
}
MAX_CHECK_SECONDS = 180


def run_check(name: str, timeout: int = MAX_CHECK_SECONDS) -> dict:
    """Lance un contrôle strictement allowlisté, sans shell et sans commande fournie par l'IA."""
    if name not in ALLOWED_CHECKS:
        raise ValueError("Contrôle non autorisé.")
    if isinstance(timeout, bool) or not isinstance(timeout, int) or not 1 <= timeout <= MAX_CHECK_SECONDS:
        raise ValueError("Délai invalide.")
    try:
        result = subprocess.run(
            ALLOWED_CHECKS[name],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            shell=False,
        )
        return {
            "name": name,
            "status": "passed" if result.returncode == 0 else "failed",
            "return_code": result.returncode,
            "stdout_tail": result.stdout[-5000:],
            "stderr_tail": result.stderr[-5000:],
        }
    except subprocess.TimeoutExpired:
        return {"name": name, "status": "timeout", "return_code": None}


def build_improvement_report(results: list[dict]) -> dict:
    """Transforme les contrôles en backlog actionnable, sans prétendre corriger les bugs."""
    if not isinstance(results, list) or any(not isinstance(item, dict) for item in results):
        raise ValueError("Résultats de contrôles invalides.")
    known = {item.get("name") for item in results}
    if not known.issubset(ALLOWED_CHECKS):
        raise ValueError("Le rapport contient un contrôle inconnu.")
    failed = [item for item in results if item.get("status") != "passed"]
    backlog = []
    for item in failed:
        name = item["name"]
        backlog.append({
            "priority": "critical" if name == "python_tests" else "high",
            "area": name,
            "observation": f"Le contrôle {name} n'a pas réussi ({item.get('status')}).",
            "next_action": "Examiner les logs, reproduire le problème, proposer une correction isolée et relancer tous les tests.",
            "automatic_code_change": False,
            "automatic_deployment": False,
        })
    if not failed:
        backlog.append({
            "priority": "normal",
            "area": "product_quality",
            "observation": "Les contrôles automatiques autorisés sont réussis.",
            "next_action": "Ajouter des parcours utilisateurs réalistes, mesurer accessibilité, vitesse, clarté et robustesse, puis traiter les irritants observés.",
            "automatic_code_change": False,
            "automatic_deployment": False,
        })
    return {
        "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "status": "needs_attention" if failed else "checks_passed",
        "checks": results,
        "improvement_backlog": backlog,
        "autonomy": {
            "synthetic_user_testing": True,
            "bounded_self_evaluation": True,
            "automatic_production_code_changes": False,
            "automatic_publication": False,
            "human_review_required_for_code_changes": True,
        },
    }


def run_cycle() -> dict:
    results = [run_check(name) for name in ALLOWED_CHECKS]
    return build_improvement_report(results)


def main() -> int:
    report = run_cycle()
    output = ROOT / "self_improvement_report.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "checks": {item["name"]: item["status"] for item in report["checks"]},
        "backlog_items": len(report["improvement_backlog"]),
        "report": str(output),
    }, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "checks_passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
