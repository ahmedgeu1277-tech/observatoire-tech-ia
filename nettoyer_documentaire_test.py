"""Nettoie les archives du documentaire uniquement après 30 jours."""
import json
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "site"
MANIFEST = SITE / "documentaire-test.json"
PAGE = SITE / "documentaire-test.html"
SCRIPT = SITE / "documentaire-test.md"
AUDIO_DIR = SITE / "audio"
VIDEO_DIR = SITE / "video"
ARCHIVE_DIR = SITE / "archives"
RETENTION = timedelta(days=30)
STAMP_RE = re.compile(r"^documentaire-test-(\d{8}T\d{6}Z)\.(mp3|mp4|md)$")


def main():
    now = datetime.now(UTC)
    cutoff = now - RETENTION
    removed = 0
    for directory in (AUDIO_DIR, VIDEO_DIR, ARCHIVE_DIR):
        if not directory.exists():
            continue
        for path in directory.iterdir():
            match = STAMP_RE.match(path.name)
            if not match or not path.is_file():
                continue
            created = datetime.strptime(match.group(1), "%Y%m%dT%H%M%SZ").replace(tzinfo=UTC)
            if created < cutoff:
                path.unlink()
                removed += 1

    if not MANIFEST.exists():
        print(f"{removed} archive(s) de plus de 30 jours supprimée(s).")
        return
    try:
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        expires = datetime.fromisoformat(data["expires_at"]).astimezone(UTC)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Manifeste d'expiration invalide : {exc}") from exc
    if now < expires:
        print(f"{removed} archive(s) ancienne(s) nettoyée(s) ; documentaire courant conservé.")
        return
    for path in (SCRIPT, MANIFEST):
        if path.exists():
            path.unlink()
    PAGE.write_text("""<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Documentaire archivé</title></head>
<body><h1>Documentaire archivé</h1><p>La version en cours a expiré. Les archives de moins de 30 jours restent conservées.</p>
<a href="./index.html">Retour à l'accueil</a></body></html>""", encoding="utf-8")
    print(f"Documentaire courant expiré ; {removed} ancienne(s) archive(s) supprimée(s).")


if __name__ == "__main__":
    main()
