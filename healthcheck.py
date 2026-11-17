"""Contrôle de santé du dépôt et des contenus avant publication."""
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
REQUIRED_ARTICLE_FIELDS = ("id", "date", "theme", "title", "summary", "verdict", "tip", "sources")


def _read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"JSON illisible : {path.relative_to(ROOT)}") from exc


def check_repository(root: Path = ROOT) -> dict:
    root = Path(root)
    themes = _read_json(root / "themes.json")
    if not isinstance(themes, dict) or not isinstance(themes.get("themes"), list) or not themes["themes"]:
        raise ValueError("themes.json doit contenir une liste non vide de thèmes.")
    for index, theme in enumerate(themes["themes"]):
        if not isinstance(theme, dict) or not str(theme.get("name", "")).strip() or not str(theme.get("query", "")).strip():
            raise ValueError(f"Thème invalide à l'index {index}.")

    articles = _read_json(root / "site" / "articles.json")
    if not isinstance(articles, list):
        raise ValueError("site/articles.json doit être une liste.")
    ids = set()
    audio_count = 0
    source_count = 0
    for index, article in enumerate(articles):
        if not isinstance(article, dict) or any(not str(article.get(k, "")).strip() for k in REQUIRED_ARTICLE_FIELDS):
            raise ValueError(f"Article incomplet à l'index {index}.")
        if article["id"] in ids:
            raise ValueError(f"Identifiant d'article dupliqué : {article['id']}.")
        ids.add(article["id"])
        if not isinstance(article["sources"], list) or not article["sources"]:
            raise ValueError(f"Article sans source : {article['id']}.")
        for source in article["sources"]:
            url = source.get("url", "") if isinstance(source, dict) else ""
            parsed = urlparse(url)
            if parsed.scheme != "https" or not parsed.netloc:
                raise ValueError(f"URL de source non sécurisée dans {article['id']}.")
            source_count += 1
        audio_url = article.get("audio_url")
        if audio_url:
            if not isinstance(audio_url, str) or not audio_url.startswith("audio/") or ".." in Path(audio_url).parts:
                raise ValueError(f"Chemin audio invalide dans {article['id']}.")
            audio_path = root / "site" / audio_url
            if not audio_path.is_file() or audio_path.stat().st_size == 0:
                raise ValueError(f"Fichier audio absent ou vide : {audio_url}.")
            audio_count += 1

    government = _read_json(root / "site" / "data" / "gouvernement.json")
    if not isinstance(government, dict) or len(government.get("directors", [])) != 30:
        raise ValueError("Le tableau de bord gouvernemental doit contenir 30 administrateurs.")
    if government.get("currency", {}).get("real_value") != 0:
        raise ValueError("La monnaie virtuelle ne doit avoir aucune valeur réelle.")

    return {
        "themes": len(themes["themes"]),
        "articles": len(articles),
        "sources": source_count,
        "audio_files": audio_count,
        "directors": len(government["directors"]),
    }


if __name__ == "__main__":
    result = check_repository()
    print("DIAGNOSTIC OK — " + json.dumps(result, ensure_ascii=False))
