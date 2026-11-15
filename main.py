import html
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
import xml.etree.ElementTree as ET

import requests
from groq import Groq

ROOT = Path(__file__).resolve().parent
SITE_DIR = ROOT / "site"
ARTICLES_FILE = SITE_DIR / "articles.json"
THEMES_FILE = ROOT / "themes.json"
MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
MAX_ARTICLES = 40
TIMEOUT = 25

def load_themes():
    with THEMES_FILE.open("r", encoding="utf-8") as f:
        data = json.load(f)
    themes = data.get("themes", [])
    if not themes:
        raise ValueError("Aucun thème n'est configuré dans themes.json.")
    return themes

def choose_theme(themes):
    state_file = ROOT / ".theme-index"
    try:
        index = int(state_file.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        index = 0
    theme = themes[index % len(themes)]
    state_file.write_text(str((index + 1) % len(themes)), encoding="utf-8")
    return theme

def fetch_news(query, limit=8):
    url = (
        "https://news.google.com/rss/search?q="
        + quote(query + " when:7d")
        + "&hl=fr&gl=FR&ceid=FR:fr"
    )
    response = requests.get(
        url, timeout=TIMEOUT,
        headers={"User-Agent": "UsineIATechGaming/1.0"}
    )
    response.raise_for_status()
    root = ET.fromstring(response.content)
    items = []
    for item in root.findall(".//item")[:limit]:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        description = (item.findtext("description") or "").strip()
        description = re.sub(r"<[^>]+>", " ", description)
        description = html.unescape(re.sub(r"\s+", " ", description)).strip()
        if title and link:
            items.append({
                "title": title[:300],
                "description": description[:700],
                "url": link
            })
    return items

def create_article(theme, sources):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("Secret GROQ_API_KEY absent dans GitHub Actions.")

    client = Groq(api_key=api_key, timeout=45, max_retries=2)
    source_text = json.dumps(sources, ensure_ascii=False)
    prompt = f"""
Tu es le rédacteur d'un observatoire francophone Tech & Gaming.
Thème : {theme['name']}

Utilise UNIQUEMENT les informations contenues dans les sources ci-dessous.
N'invente aucun fait, aucune date, aucun chiffre et aucune annonce.
Si les sources sont trop vagues, dis clairement que l'information reste à confirmer.
Ne prétends pas avoir testé un produit ou un jeu.
Ne copie pas les articles : fais une synthèse originale et courte.
Réponds en français sous forme d'un objet JSON avec exactement ces clés :
"title" (titre court), "summary" (2 à 4 phrases), "verdict" (une phrase prudente),
"tip" (une astuce utile), "source_indices" (liste d'indices des sources utilisées).
Les indices commencent à 0. N'ajoute aucun autre texte.

Sources :
{source_text}
"""
    completion = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "Tu produis des synthèses factuelles, prudentes et lisibles."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.25,
        max_tokens=550,
        response_format={"type": "json_object"}
    )
    raw = completion.choices[0].message.content or "{}"
    data = json.loads(raw)

    title = str(data.get("title", theme["name"]))[:140]
    summary = str(data.get("summary", ""))[:1200]
    verdict = str(data.get("verdict", ""))[:500]
    tip = str(data.get("tip", ""))[:500]

    indices = data.get("source_indices", [])
    used_sources = []
    for index in indices:
        if isinstance(index, int) and 0 <= index < len(sources):
            used_sources.append(sources[index])
    if not used_sources:
        used_sources = sources[:3]
    if not summary.strip():
        raise ValueError("La réponse IA ne contient pas de résumé.")

    return {
        "id": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "date": datetime.now(timezone.utc).isoformat(timespec="minutes"),
        "theme": theme["name"],
        "title": title,
        "summary": summary,
        "verdict": verdict,
        "tip": tip,
        "sources": used_sources[:5],
        "ai_notice": "Article rédigé avec l'aide d'une intelligence artificielle. Vérifiez les sources."
    }

def load_previous_articles():
    if not ARTICLES_FILE.exists():
        return []
    try:
        data = json.loads(ARTICLES_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []

def save_articles(article):
    SITE_DIR.mkdir(parents=True, exist_ok=True)
    articles = load_previous_articles()
    articles.insert(0, article)
    unique = []
    seen = set()
    for item in articles:
        key = item.get("id")
        if key and key not in seen:
            unique.append(item)
            seen.add(key)
    ARTICLES_FILE.write_text(
        json.dumps(unique[:MAX_ARTICLES], ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

def main():
    themes = load_themes()
    theme = choose_theme(themes)
    print(f"Thème choisi : {theme['name']}")
    sources = fetch_news(theme["query"])
    if not sources:
        raise RuntimeError("Aucune source RSS exploitable. Aucun article publié.")
    print(f"{len(sources)} source(s) récupérée(s).")
    article = create_article(theme, sources)
    save_articles(article)
    print(f"Article créé : {article['title']}")
    print("Terminé. GitHub Actions enregistrera les fichiers du site.")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERREUR : {exc}", file=sys.stderr)
        raise
