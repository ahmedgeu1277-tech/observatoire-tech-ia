import asyncio
import html
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, urlparse
from defusedxml import ElementTree as ET

import requests
from agent_gardien import verifier_conformite_legale
from sources_specialisees import fetch_specialized_sources
from ai_providers import generate_text

ROOT = Path(__file__).resolve().parent
SITE_DIR = ROOT / "site"
ARTICLES_FILE = SITE_DIR / "articles.json"
THEMES_FILE = ROOT / "themes.json"
MAX_ARTICLES = 30
TIMEOUT = 20
MAX_SOURCES = 6
MAX_DYNAMIC_AGENTS = 2

def appliquer_cycle_vie(theme, now=None):
    """Applique une variante avant/après événement, sans modifier le fichier source."""
    result = dict(theme)
    lifecycle = result.get("lifecycle")
    if not isinstance(lifecycle, dict):
        return result
    now = now or datetime.now(timezone.utc)
    try:
        launch_at = datetime.fromisoformat(lifecycle["launch_at"].replace("Z", "+00:00"))
        end_at = datetime.fromisoformat(lifecycle["end_at"].replace("Z", "+00:00"))
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"Cycle de vie invalide pour le thème {theme.get('name', 'inconnu')}.") from exc
    if launch_at.tzinfo is None or end_at.tzinfo is None or end_at <= launch_at:
        raise ValueError(f"Dates de cycle de vie invalides pour {theme.get('name', 'inconnu')}.")
    if now < launch_at:
        variant = lifecycle.get("before", {})
    elif now <= end_at:
        variant = lifecycle.get("after", {})
    else:
        return result
    if not isinstance(variant, dict) or not variant.get("name") or not variant.get("query"):
        raise ValueError(f"Variante avant/après manquante pour {theme.get('name', 'inconnu')}.")
    result["name"] = str(variant["name"])
    result["query"] = str(variant["query"])
    return result


def load_themes():
    with THEMES_FILE.open("r", encoding="utf-8") as f:
        data = json.load(f)
    themes = data.get("themes", [])
    if not themes:
        raise ValueError("Aucun thème n'est configuré dans themes.json.")
    now = datetime.now(timezone.utc)
    return [appliquer_cycle_vie(theme, now) for theme in themes]

def get_priority_event_theme(themes, now=None):
    """Retourne un thème événementiel uniquement pendant sa fenêtre configurée."""
    now = now or datetime.now(timezone.utc)
    for theme in themes:
        lifecycle = theme.get("lifecycle", {})
        if not isinstance(lifecycle, dict):
            continue
        try:
            # dict.get avec une valeur par défaut évaluée immédiatement provoquait
            # un KeyError si launch_at était absent, même avec start_at présent.
            start_value = lifecycle.get("start_at") or lifecycle.get("launch_at")
            end_value = lifecycle.get("end_at")
            if not isinstance(start_value, str) or not isinstance(end_value, str):
                continue
            start_at = datetime.fromisoformat(start_value.replace("Z", "+00:00"))
            end_at = datetime.fromisoformat(end_value.replace("Z", "+00:00"))
        except (TypeError, ValueError):
            continue
        if (
            start_at.tzinfo is not None
            and end_at.tzinfo is not None
            and start_at <= now <= end_at
        ):
            return theme
    return None


def choose_theme(themes):
    state_file = ROOT / ".theme-index"
    try:
        index = int(state_file.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        index = 0

    event_theme = get_priority_event_theme(themes)
    if event_theme:
        regular_themes = [theme for theme in themes if theme is not event_theme]
        if regular_themes and index % 2 == 0:
            theme = event_theme
        elif regular_themes:
            theme = regular_themes[(index // 2) % len(regular_themes)]
        else:
            theme = event_theme
        state_file.write_text(str((index + 1) % (2 * max(1, len(regular_themes)))), encoding="utf-8")
        return theme

    theme = themes[index % len(themes)]
    state_file.write_text(str((index + 1) % len(themes)), encoding="utf-8")
    return theme

def fetch_news(query, limit=8):
    url = (
        "https://news.google.com/rss/search?q="
        + quote(query + " when:7d")
        + "&hl=fr&gl=FR&ceid=FR:fr"
    )
    try:
        response = requests.get(
            url, timeout=TIMEOUT,
            headers={"User-Agent": "ObservatoireTechGaming/1.0"}
        )
        response.raise_for_status()
        root = ET.fromstring(response.content)
    except (requests.RequestException, ET.ParseError) as exc:
        print(f"AVERTISSEMENT : Google Actualités indisponible ({type(exc).__name__}); les autres sources seront utilisées.")
        return []
    items = []
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        description = (item.findtext("description") or "").strip()
        published = (item.findtext("pubDate") or "").strip()
        description = re.sub(r"<[^>]+>", " ", description)
        description = html.unescape(re.sub(r"\s+", " ", description)).strip()
        if not title or not link:
            continue
        host = (urlparse(link).hostname or "").lower()
        if host.startswith("www."):
            host = host[4:]
        publisher = title.rsplit(" - ", 1)[-1].strip() if " - " in title else host
        headline = title.rsplit(" - ", 1)[0].strip() if " - " in title else title
        items.append({
            "title": headline[:260],
            "publisher": publisher[:100],
            "domain": host[:120],
            "published": published[:100],
            "description": description[:700],
            "url": link
        })

    # Sélectionne d'abord des médias différents, puis complète si nécessaire.
    diversified = []
    seen_domains = set()
    seen_titles = set()
    for source in items:
        title_key = re.sub(r"[^a-z0-9]+", "", source["title"].lower())
        if title_key in seen_titles:
            continue
        seen_titles.add(title_key)
        if source["domain"] not in seen_domains:
            diversified.append(source)
            seen_domains.add(source["domain"])
        if len(diversified) >= limit:
            break
    if len(diversified) < limit:
        for source in items:
            title_key = re.sub(r"[^a-z0-9]+", "", source["title"].lower())
            if title_key not in {re.sub(r"[^a-z0-9]+", "", x["title"].lower()) for x in diversified}:
                diversified.append(source)
            if len(diversified) >= limit:
                break
    return diversified[:limit]

def create_article(theme, sources, agent_reports=None):
    source_text = json.dumps(sources, ensure_ascii=False)
    prompt = f"""
Tu es journaliste-rédacteur pour un petit média indépendant francophone consacré à la technologie, à l'IA et aux jeux vidéo. Écris comme une personne qui explique clairement une actualité à ses lecteurs, pas comme une publicité ni comme un robot.
Thème : {theme['name']}
Analyses des agents spécialisés (simples pistes à vérifier, jamais des preuves) : {json.dumps(agent_reports or [], ensure_ascii=False)}

RÈGLES DE RÉDACTION :
- Appuie chaque information factuelle uniquement sur les sources fournies. N'invente aucun fait, chiffre, citation, date, test, expérience personnelle ou annonce.
- Fais une synthèse originale : ne recopie pas les titres et ne paraphrase pas chaque source l'une après l'autre.
- Écris un résumé de 3 à 5 phrases, autour de 85 mots (entre 70 et 100 si les sources le permettent), naturel et précis. Varie les débuts de phrases et la structure d'un article à l'autre.
- Explique ce qui s'est passé, pourquoi cela peut intéresser les lecteurs et ce qu'on ne sait pas encore, si c'est pertinent.
- Évite les expressions automatiques et le remplissage : « dans un monde en constante évolution », « révolutionnaire », « il est important de noter », « plongeons dans », « une avancée majeure » sans preuve.
- Pas de ton publicitaire, de fausse excitation, de fausse opinion personnelle ni de conclusion passe-partout.
- Un titre informatif, court et spécifique. Pas de clickbait.
- Si les sources se contredisent ou restent vagues, indique-le franchement. Si elles ne suffisent pas, ne transforme pas une rumeur en fait.
- Les agents spécialisés ne sont pas des sources indépendantes : ne reprends leurs affirmations que si les liens fournis les confirment.
- Choisis uniquement les indices des sources réellement utiles. Les indices commencent à 0.
- Réponds en français avec un objet JSON contenant exactement : "title", "summary", "verdict", "tip", "source_indices". Aucun texte hors JSON.
Sources :
{source_text}
"""
    messages = [
        {"role": "system", "content": "Tu produis des synthèses factuelles, prudentes et lisibles."},
        {"role": "user", "content": prompt}
    ]
    raw, ai_provider = generate_text(messages, max_tokens=1200, temperature=0.25, json_mode=True)
    # Certains modèles renvoient le JSON dans un bloc Markdown : on extrait l'objet.
    raw = re.sub(r"^\s*```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"\s*```\s*$", "", raw)
    if not raw.startswith("{"):
        start, end = raw.find("{"), raw.rfind("}")
        if start >= 0 and end > start:
            raw = raw[start:end + 1]
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Réponse IA invalide : JSON illisible ({exc.msg}). Aucun article publié.") from exc

    required = ("title", "summary", "verdict", "tip", "source_indices")
    if not isinstance(data, dict) or any(key not in data for key in required):
        raise ValueError("Réponse IA incomplète : champs obligatoires manquants. Aucun article publié.")
    if any(not isinstance(data[key], str) or not data[key].strip()
           for key in ("title", "summary", "verdict", "tip")):
        raise ValueError("Réponse IA incomplète : texte vide ou invalide. Aucun article publié.")
    summary_words = len(data["summary"].split())
    if summary_words < 35 or summary_words > 140:
        raise ValueError(f"Résumé IA hors longueur acceptable ({summary_words} mots). Aucun article publié.")

    title = data["title"].strip()[:140]
    summary = data["summary"].strip()[:1200]
    verdict = data["verdict"].strip()[:500]
    tip = data["tip"].strip()[:500]

    indices = data["source_indices"]
    if not isinstance(indices, list) or not indices:
        raise ValueError("La réponse IA ne référence aucune source. Aucun article publié.")
    used_sources = []
    for index in indices:
        if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < len(sources):
            raise ValueError("La réponse IA contient un indice de source invalide. Aucun article publié.")
        if sources[index] not in used_sources:
            used_sources.append(sources[index])
    if not used_sources:
        raise ValueError("Aucune source valide sélectionnée. Aucun article publié.")

    return {
        "id": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "date": datetime.now(timezone.utc).isoformat(timespec="minutes"),
        "theme": theme["name"],
        "title": title,
        "summary": summary,
        "verdict": verdict,
        "tip": tip,
        "sources": used_sources[:5],
        "ai_notice": f"Article rédigé avec l’aide de {ai_provider} à partir des sources indiquées. Consultez les liens pour retrouver le contexte complet."
    }

def load_previous_articles():
    if not ARTICLES_FILE.exists():
        return []
    try:
        data = json.loads(ARTICLES_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise RuntimeError("site/articles.json n'est pas une liste. Publication annulée pour préserver les archives.")
        return data
    except json.JSONDecodeError as exc:
        raise RuntimeError("site/articles.json est invalide. Publication annulée pour préserver les archives.") from exc
    except OSError as exc:
        raise RuntimeError("Impossible de lire les archives existantes. Publication annulée.") from exc

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
    if not profiles:
        return []
    source_text = json.dumps(sources[:5], ensure_ascii=False)
    reports = []
    for profile in profiles[:MAX_DYNAMIC_AGENTS]:
        try:
            prompt = f"""Mission : {profile.get('mission', '')}
Instructions : {profile.get('instructions', '')}
Thème : {theme['name']}
Sources publiques : {source_text}
Rédige 2 phrases en français. Utilise seulement les sources. Indique les incertitudes."""
            report, provider = generate_text(
                [
                    {"role": "system", "content": "Tu es un analyste spécialisé prudent."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=350,
                temperature=0.2,
            )
            if report.strip():
                reports.append({
                    "agent": profile.get("name", "agent"),
                    "provider": provider,
                    "report": report.strip()
                })
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
    sources = fetch_news(theme["query"], limit=MAX_SOURCES)
    specialized = fetch_specialized_sources(theme["name"], limit=4)
    # Les flux officiels apportent des annonces primaires ; les médias généralistes
    # complètent le contexte. On déduplique les URL avant de transmettre à l'IA.
    merged = []
    seen_urls = set()
    for source in specialized + sources:
        key = source.get("url", "").split("#", 1)[0]
        if key and key not in seen_urls:
            merged.append(source)
            seen_urls.add(key)
        if len(merged) >= MAX_SOURCES:
            break
    sources = merged
    print(f"{len(specialized)} source(s) spécialisée(s) officielle(s) disponible(s).")
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
