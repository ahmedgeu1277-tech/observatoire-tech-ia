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
ARTICLES_FILE = SITE / "articles.json"
AUDIO_DIR = SITE / "audio"
VIDEO_DIR = SITE / "video"
ARCHIVE_DIR = SITE / "archives"
RETENTION = timedelta(days=30)
STAMP_RE = re.compile(r"^documentaire-test-(\d{8}T\d{6}Z)\.(mp3|mp4|md)$")


def main():
    now = datetime.now(UTC)
    cutoff = now - RETENTION
    removed = 0
    removed_audio_names = set()
    articles = None
    if ARTICLES_FILE.exists():
        try:
            articles = json.loads(ARTICLES_FILE.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError("Catalogue d'articles illisible ; nettoyage annulé.") from exc
        if not isinstance(articles, list) or any(not isinstance(item, dict) for item in articles):
            raise RuntimeError("Catalogue d'articles invalide ; nettoyage annulé.")

    for directory in (AUDIO_DIR, VIDEO_DIR, ARCHIVE_DIR):
        if not directory.exists():
            continue
        for path in directory.iterdir():
            if not path.is_file():
                continue
            stamp = None
            match = STAMP_RE.match(path.name)
            if match:
                stamp = datetime.strptime(match.group(1), "%Y%m%dT%H%M%SZ").replace(tzinfo=UTC)
            translated = TRANSLATED_DOCUMENTARY_RE.match(path.name)
            if translated:
                stamp = datetime.strptime(translated.group("stamp"), "%Y%m%dT%H%M%SZ").replace(tzinfo=UTC)
            article_audio = ARTICLE_AUDIO_RE.match(path.name) if directory == AUDIO_DIR else None
            if article_audio:
                stamp = datetime.strptime(article_audio.group("stamp"), "%Y%m%dT%H%M%S").replace(tzinfo=UTC)
            chapter = WEEKLY_CHAPTER_RE.match(path.name) if directory == AUDIO_DIR else None
            if chapter:
                stamp = datetime.strptime(chapter.group("stamp"), "%Y%m%d").replace(tzinfo=UTC)
            if stamp and stamp < cutoff:
                path.unlink()
                removed += 1
                if directory == AUDIO_DIR:
                    removed_audio_names.add(path.name)

    if articles is not None and removed_audio_names:
        changed = False
        for article in articles:
            audio_url = article.get("audio_url")
            if isinstance(audio_url, str) and Path(audio_url).name in removed_audio_names:
                article["audio_url"] = None
                changed = True
            translations = article.get("translations")
            if isinstance(translations, dict):
                for translated in translations.values():
                    if not isinstance(translated, dict):
                        continue
                    audio_url = translated.get("audio_url")
                    if isinstance(audio_url, str) and Path(audio_url).name in removed_audio_names:
                        translated["audio_url"] = None
                        changed = True
        if changed:
            temporary = ARTICLES_FILE.with_suffix(".json.tmp")
            temporary.write_text(json.dumps(articles, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")
            temporary.replace(ARTICLES_FILE)

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
