"""Retire uniquement le documentaire de test lorsqu'il a dépassé ses 24 heures."""
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "site"
MANIFEST = SITE / "documentaire-test.json"
PAGE = SITE / "documentaire-test.html"
SCRIPT = SITE / "documentaire-test.md"
AUDIO_DIR = SITE / "audio"


def main():
    if not MANIFEST.exists():
        print("Aucun documentaire temporaire à nettoyer.")
        return
    try:
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        expires = datetime.fromisoformat(data["expires_at"])
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Manifeste d'expiration invalide : {exc}") from exc
    if datetime.now(timezone.utc) < expires.astimezone(timezone.utc):
        print("Documentaire encore dans sa période de test.")
        return

    audio_name = data.get("audio_file", "")
    if audio_name and Path(audio_name).name == audio_name:
        audio = AUDIO_DIR / audio_name
        if audio.exists():
            audio.unlink()
    for path in (SCRIPT, MANIFEST):
        if path.exists():
            path.unlink()
    PAGE.write_text("""<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Test terminé</title>
<style>body{font:17px system-ui;background:#0b1020;color:#eef3ff;max-width:700px;margin:12vh auto;padding:24px}
a{color:#65ddff}</style></head><body><h1>La période de test est terminée</h1>
<p>Le documentaire temporaire a été retiré automatiquement après 24 heures.</p>
<a href="./index.html">Retour à l'accueil</a></body></html>""", encoding="utf-8")
    print("Documentaire de test retiré après expiration.")


if __name__ == "__main__":
    main()
