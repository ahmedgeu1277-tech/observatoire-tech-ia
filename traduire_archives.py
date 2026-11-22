"""Backfill progressif des traductions d'articles historiques.

Un petit lot est traduit par exécution pour respecter les quotas gratuits.
Les sources, liens, dates et fichiers audio ne sont jamais modifiés.
"""
from __future__ import annotations

import json
from pathlib import Path

import main

MAX_PER_RUN = 3


def backfill_translations(max_items: int = MAX_PER_RUN) -> dict:
    if isinstance(max_items, bool) or not isinstance(max_items, int) or not 1 <= max_items <= 5:
        raise ValueError("Le lot doit contenir entre 1 et 5 articles.")
    path: Path = main.ARTICLES_FILE
    try:
        articles = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError("Impossible de lire les articles ; aucune modification effectuée.") from exc
    if not isinstance(articles, list) or any(not isinstance(item, dict) for item in articles):
        raise RuntimeError("Le catalogue d'articles est invalide ; aucune modification effectuée.")

    translated = 0
    remaining = sum(not isinstance(item.get("translations"), dict) or not item["translations"] for item in articles)
    # Traiter les plus anciens d'abord, sans retirer ni réordonner les articles.
    for article in reversed(articles):
        if translated >= max_items:
            break
        if isinstance(article.get("translations"), dict) and article["translations"]:
            continue
        result = main.traduire_article(article)
        if not result:
            # Un quota ou fournisseur indisponible arrête proprement le lot.
            break
        article["translations"] = result
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(json.dumps(articles, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(path)
        translated += 1
        remaining -= 1
    summary = {"translated": translated, "remaining": remaining, "total": len(articles)}
    print(json.dumps(summary, ensure_ascii=False))
    return summary


if __name__ == "__main__":
    backfill_translations()
