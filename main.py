import asyncio
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
from agent_gardien import verifier_conformite_legale

ROOT = Path(__file__).resolve().parent
SITE_DIR = ROOT / "site"
ARTICLES_FILE = SITE_DIR / "articles.json"
THEMES_FILE = ROOT / "themes.json"
MODEL = os.getenv("GROQ_MODEL") or "openai/gpt-oss-20b"
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

def create_article(theme, sources, agent_reports=None):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("Secret GROQ_API_KEY absent dans GitHub Actions.")

    source_text = json.dumps(sources, ensure_ascii=False)
    prompt = f"""
Tu es le rédacteur d'un observatoire francophone Tech & Gaming.
Thème : {theme['name']}
Analyses des agents spécialisés (pistes, pas des preuves) : {json.dumps(agent_reports or [], ensure_ascii=False)}

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
    messages = [
        {"role": "system", "content": "Tu produis des synthèses factuelles, prudentes et lisibles."},
        {"role": "user", "content": prompt}
    ]
    raw = ""
    groq_error = None
    try:
        client = Groq(api_key=api_key, timeout=45, max_retries=2)
        completion = client.chat.completions.create(
            model=MODEL, messages=messages, temperature=0.25,
            max_completion_tokens=1200, reasoning_effort="low",
            response_format={"type": "json_object"},
        )
        raw = (completion.choices[0].message.content or "").strip()
    except Exception as exc:
        groq_error = exc
        hf_key = os.getenv("HF_API_KEY") or os.getenv("HF_TOKEN")
        if not hf_key:
            raise RuntimeError(f"Groq indisponible et aucun secret HF_API_KEY/HF_TOKEN configuré : {exc}") from exc
        try:
            from huggingface_hub import InferenceClient
            hf = InferenceClient(
                model=os.getenv("HF_MODEL") or "Qwen/Qwen2.5-7B-Instruct",
                token=hf_key, timeout=60
            )
            fallback = hf.chat.completions.create(
                messages=messages, max_tokens=1200, temperature=0.25
            )
            raw = (fallback.choices[0].message.content or "").strip()
            print("INFO : génération effectuée via Hugging Face après échec de Groq.")
        except Exception as hf_error:
            raise RuntimeError(f"Groq et Hugging Face indisponibles. Groq: {groq_error}; HF: {hf_error}") from hf_error
    # Certains modèles renvoient le JSON dans un bloc Markdown : on extrait l'objet.
    raw = re.sub(r"^\s*```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"\s*```\s*$", "", raw)
    if not raw.startswith("{"):
        start, end = raw.find("{"), raw.rfind("}")
        if start >= 0 and end > start:
            raw = raw[start:end + 1]
    data = None
    parse_warning = None
    if raw:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            parse_warning = f"Réponse IA non JSON ({exc.msg}); publication de secours utilisée."
    else:
        parse_warning = "Réponse IA vide; publication de secours utilisée."

    if not isinstance(data, dict) or not str(data.get("summary", "")).strip():
        # Ne bloque pas la publication si le modèle renvoie une réponse vide
        # ou un format inattendu. Les titres restent liés aux sources originales.
        selected = sources[:3]
        titles = [item["title"] for item in selected if item.get("title")]
        summary = "Les sources consultées signalent notamment : " + " ; ".join(titles)
        data = {
            "title": f"Le point sur {theme['name']}",
            "summary": summary[:1200],
            "verdict": "Cette synthèse de secours reprend les titres des sources ; consulte les liens pour vérifier les informations.",
            "tip": "Ouvre les sources originales avant de partager ou d'utiliser une information.",
            "source_indices": list(range(len(selected)))
        }
        print(f"AVERTISSEMENT : {parse_warning or 'Réponse IA incomplète'}")

    title = str(data.get("title", theme["name"]))[:140]
    summary = str(data.get("summary", ""))[:1200]
    verdict = str(data.get("verdict", ""))[:500]
    tip = str(data.get("tip", ""))[:500]

    indices = data.get("source_indices", [])
    used_sources = []
    if isinstance(indices, list):
        for index in indices:
            if isinstance(index, int) and 0 <= index < len(sources):
                used_sources.append(sources[index])
    if not used_sources:
        used_sources = sources[:3]
    if not summary.strip():
        raise ValueError("Impossible de créer un résumé, même en mode de secours.")

    return {
        "id": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "date": datetime.now(timezone.utc).isoformat(timespec="minutes"),
        "theme": theme["name"],
        "title": title,
        "summary": summary,
        "verdict": verdict,
        "tip": tip,
        "sources": used_sources[:5],
        "ai_notice": "Contenu assisté par IA ou synthèse de secours à partir des titres. Vérifiez toujours les sources originales."
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


def load_agent_profiles():
    folder = ROOT / "agents_dynamiques"
    if not folder.exists():
        return []
    profiles = []
    for path in sorted(folder.glob("*.json"))[:5]:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if data.get("mission") and data.get("instructions"):
                profiles.append(data)
        except (OSError, json.JSONDecodeError):
            print(f"Profil d'agent ignoré : {path.name}")
    return profiles

def executer_agents_dynamiques(theme, sources, profiles):
    if not profiles or not os.getenv("GROQ_API_KEY"):
        return []
    client = Groq(api_key=os.environ["GROQ_API_KEY"], timeout=45, max_retries=1)
    source_text = json.dumps(sources[:5], ensure_ascii=False)
    reports = []
    for profile in profiles[:3]:
        try:
            prompt = f"""Mission : {profile.get('mission', '')}
Instructions : {profile.get('instructions', '')}
Thème : {theme['name']}
Sources publiques : {source_text}
Rédige 2 phrases en français. Utilise seulement les sources. Indique les incertitudes."""
            result = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": "Tu es un analyste spécialisé prudent."},
                    {"role": "user", "content": prompt}
                ],
                reasoning_effort="low",
                max_completion_tokens=350,
            )
            report = (result.choices[0].message.content or "").strip()
            if report:
                reports.append({"agent": profile.get("name", "agent"), "report": report})
        except Exception as exc:
            print(f"Agent {profile.get('name', 'inconnu')} ignoré : {type(exc).__name__}.")
    return reports

def archive_memory(article):
    memory = ROOT / "memoire_tech.txt"
    with memory.open("a", encoding="utf-8") as f:
        f.write(
            f"\n[{article['date']}] {article['theme']} — {article['title']}\n"
            f"{article['summary']}\nSources : "
            + " ; ".join(s.get("url", "") for s in article.get("sources", [])[:5])
            + "\n"
        )

async def create_audio(article):
    try:
        import edge_tts
        audio_dir = SITE_DIR / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{article['id']}.mp3"
        spoken = (
            f"{article['title']}. {article['summary']} "
            f"Verdict du laboratoire : {article['verdict']}. "
            f"À retenir : {article['tip']}. "
            "Analyse préparée avec l'aide d'une intelligence artificielle."
        )
        await edge_tts.Communicate(spoken, "fr-FR-HenriNeural").save(str(audio_dir / filename))
        return f"audio/{filename}"
    except Exception as exc:
        print(f"Audio non créé ({type(exc).__name__}: {exc}); article texte conservé.")
        return None

def main():
    themes = load_themes()
    theme = choose_theme(themes)
    print(f"Thème choisi : {theme['name']}")
    sources = fetch_news(theme["query"])
    if not sources:
        raise RuntimeError("Aucune source RSS exploitable. Aucun article publié.")
    print(f"{len(sources)} source(s) récupérée(s).")
    profiles = load_agent_profiles()
    reports = executer_agents_dynamiques(theme, sources, profiles)
    if reports:
        print(f"{len(reports)} agent(s) spécialisé(s) ont rendu une analyse.")
    article = create_article(theme, sources, reports)
    if not verifier_conformite_legale(json.dumps(article, ensure_ascii=False), "PUBLICATION_WEB"):
        raise RuntimeError("Publication bloquée par le contrôle de sécurité.")
    article["audio_url"] = asyncio.run(create_audio(article))
    save_articles(article)
    archive_memory(article)
    print(f"Article créé : {article['title']}")
    print("Article, mémoire et audio éventuel enregistrés.")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERREUR : {exc}", file=sys.stderr)
        raise
