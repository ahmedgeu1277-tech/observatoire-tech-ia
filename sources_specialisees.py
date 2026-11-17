"""Collecte prudente de flux RSS officiels spécialisés."""
import html
import re
from urllib.parse import urlparse

import requests
from defusedxml import ElementTree as ET

TIMEOUT = 12
FEEDS = {
    "ai": [
        ("OpenAI", "https://openai.com/news/rss.xml"),
        ("Google DeepMind", "https://deepmind.google/blog/rss.xml"),
        ("Google Research", "https://research.google/blog/rss/"),
        ("Hugging Face", "https://huggingface.co/blog/feed.xml"),
        ("arXiv Intelligence artificielle", "https://rss.arxiv.org/rss/cs.AI"),
        ("arXiv Machine Learning", "https://rss.arxiv.org/rss/cs.LG"),
    ],
    "gaming": [
        ("IGN France", "https://fr.ign.com/feed.xml"),
        ("IGN", "https://www.ign.com/rss/v2/articles/feed"),
        ("GameSpot", "https://www.gamespot.com/feeds/news/"),
    ],
    "engines": [
        ("Unity", "https://blog.unity.com/feed"),
        ("Unreal Engine / Epic", "https://www.unrealengine.com/rss?lang=en-US"),
        ("Godot", "https://godotengine.org/rss.xml"),
        ("GameMaker", "https://gamemaker.io/en/blog/rss"),
    ],
    # Roblox n'ayant pas de flux éditorial dédié validé ici, on utilise
    # des médias gaming et on filtre strictement sur le mot-clé Roblox.
    "roblox": [
        ("IGN France", "https://fr.ign.com/feed.xml"),
        ("IGN", "https://www.ign.com/rss/v2/articles/feed"),
        ("GameSpot", "https://www.gamespot.com/feeds/news/"),
    ],
}

def _clean(value):
    value = re.sub(r"<[^>]+>", " ", value or "")
    return html.unescape(re.sub(r"\s+", " ", value)).strip()

def _text(element, names):
    for name in names:
        found = element.find(name)
        if found is not None and found.text:
            return found.text.strip()
    return ""

def parse_feed(content, publisher, feed_url):
    """Parse les flux RSS 2.0 et Atom ; retourne des sources normalisées."""
    root = ET.fromstring(content)
    host = (urlparse(feed_url).hostname or "").lower()
    items = root.findall(".//item")
    if not items:
        items = root.findall(".//{http://www.w3.org/2005/Atom}entry")
    results = []
    for item in items:
        title = _clean(_text(item, ["title", "{http://www.w3.org/2005/Atom}title"]))
        link = _text(item, ["link"])
        if not link:
            atom_link = item.find("{http://www.w3.org/2005/Atom}link")
            if atom_link is not None:
                link = atom_link.attrib.get("href", "")
        description = _text(item, ["description", "summary", "{http://www.w3.org/2005/Atom}summary",
                                   "{http://www.w3.org/2005/Atom}content"])
        published = _text(item, ["pubDate", "published", "updated",
                                 "{http://www.w3.org/2005/Atom}published",
                                 "{http://www.w3.org/2005/Atom}updated"])
        if title and link.startswith("https://"):
            results.append({
                "title": title[:260],
                "publisher": publisher[:100],
                "domain": (urlparse(link).hostname or host)[:120],
                "published": published[:100],
                "description": _clean(description)[:700],
                "url": link,
                "source_type": "flux_officiel"
            })
    return results

def fetch_specialized_sources(theme_name, limit=5):
    """Récupère uniquement les flux correspondant au thème ; un flux en panne est ignoré."""
    theme = (theme_name or "").lower()
    keywords = ()
    if "roblox" in theme:
        feeds = FEEDS["roblox"]
        keywords = ("roblox",)
    elif any(word in theme for word in ("moteur", "logiciel de création", "game engine", "unity", "unreal", "godot", "gamemaker")):
        feeds = FEEDS["engines"]
        keywords = ("unity", "unreal", "godot", "gamemaker", "engine", "moteur")
    elif any(word in theme for word in ("gta", "grand theft auto", "rockstar")):
        feeds = FEEDS["gaming"]
        keywords = ("gta", "grand theft auto", "rockstar")
    elif any(word in theme for word in ("gaming", "jeux vidéo", "jeu vidéo")):
        feeds = FEEDS["gaming"]
    elif any(word in theme for word in ("intelligence artificielle", "ia", "machine learning")):
        feeds = FEEDS["ai"]
    else:
        feeds = []
    collected = []
    seen = set()
    for publisher, url in feeds:
        try:
            response = requests.get(url, timeout=TIMEOUT, headers={
                "User-Agent": "ObservatoireTechGaming/1.0 (+https://github.com/ahmedgeu1277-tech/observatoire-tech-ia)"
            })
            response.raise_for_status()
            for source in parse_feed(response.content, publisher, url):
                searchable = (source["title"] + " " + source["description"]).casefold()
                if keywords and not any(keyword in searchable for keyword in keywords):
                    continue
                key = source["url"].split("#", 1)[0]
                if key not in seen:
                    collected.append(source)
                    seen.add(key)
        except (requests.RequestException, ET.ParseError, ValueError) as exc:
            print(f"Flux spécialisé ignoré ({publisher}, {type(exc).__name__}).")
    return collected[:max(0, limit)]
