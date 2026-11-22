"""Backfill progressif des traductions d'articles historiques.

Un petit lot est traité par exécution pour respecter les quotas gratuits.
Les sources, liens et dates ne sont jamais modifiés.
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

import main

MAX_PER_RUN = 5


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

    languages = tuple(main.ARTICLE_TRANSLATION_LANGUAGES)
    fields = tuple(main.ARTICLE_TRANSLATION_FIELDS)

    def text_complete(article):
        translations = article.get("translations")
        return isinstance(translations, dict) and all(
            isinstance(translations.get(language), dict)
            and all(
                isinstance(translations[language].get(field), str)
                and translations[language][field].strip()
                for field in fields
            )
            for language in languages
        )

    def audio_complete(article):
        translations = article.get("translations")
        return isinstance(translations, dict) and all(
            isinstance(translations.get(language), dict)
            and isinstance(translations[language].get("audio_url"), str)
            and translations[language]["audio_url"].startswith("audio/")
            for language in languages
        )

    def save():
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(articles, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)

    processed = 0
    remaining = sum(not (text_complete(item) and audio_complete(item)) for item in articles)
    # Traiter les plus anciens d'abord, sans retirer ni réordonner les articles.
    for article in reversed(articles):
        if processed >= max_items:
            break
        if text_complete(article) and audio_complete(article):
            continue

        existing = article.get("translations")
        merged = dict(existing) if isinstance(existing, dict) else {}
        if not text_complete(article):
            result = main.traduire_article(article)
            if not result:
                # Un quota ou fournisseur indisponible arrête proprement le lot.
                break
            merged.update(result)

        # Ne génère que les narrations manquantes : les textes déjà traduits
        # ne sont pas renvoyés inutilement au modèle IA.
        missing_audio = {
            language: fields_by_language
            for language, fields_by_language in merged.items()
            if language in main.ARTICLE_TRANSLATION_LANGUAGES
            and (
                not isinstance(fields_by_language, dict)
                or not isinstance(fields_by_language.get("audio_url"), str)
                or not fields_by_language["audio_url"].startswith("audio/")
            )
        }
        if missing_audio:
            generated = asyncio.run(main.create_translated_audio(article, missing_audio))
            merged.update(generated)

        article["translations"] = merged
        save()
        processed += 1
        remaining = sum(not (text_complete(item) and audio_complete(item)) for item in articles)

    summary = {"translated": processed, "remaining": remaining, "total": len(articles)}
    print(json.dumps(summary, ensure_ascii=False))
    return summary


if __name__ == "__main__":
    backfill_translations()
