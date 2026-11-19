import asyncio
import html
import json
import re
import sys
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import parse_qs, quote, urlparse
from uuid import uuid4

import requests
from defusedxml import ElementTree as ET

from agent_gardien import verifier_conformite_legale
from ai_providers import generate_text
from sources_specialisees import fetch_specialized_sources

ROOT = Path(__file__).resolve().parent
SITE_DIR = ROOT / "site"
ARTICLES_FILE = SITE_DIR / "articles.json"
THEMES_FILE = ROOT / "themes.json"
MAX_ARTICLES = 30
TIMEOUT = 20
MAX_SOURCES = 6
MAX_DYNAMIC_AGENTS = 2

SOURCE_EDITOR_DOMAINS = {
    "rockstargames.com", "openai.com", "deepmind.google", "huggingface.co",
    "unity.com", "blog.unity.com", "unrealengine.com", "godotengine.org",
    "gamemaker.io", "epicgames.com", "microsoft.com",
    "google.com", "sony.com", "playstation.com", "nintendo.com", "apple.com",
    "samsung.com", "nvidia.com", "amd.com", "intel.com", "meta.com",
    "anthropic.com", "mistral.ai",
}
ORGANIZATION_DOMAINS = {
    "Rockstar": {"rockstargames.com"},
    "Epic Games": {"epicgames.com", "unrealengine.com"},
    "Unity": {"unity.com", "blog.unity.com"},
    "Godot": {"godotengine.org"},
    "GameMaker": {"gamemaker.io"},
    "OpenAI": {"openai.com"},
    "Google": {"google.com", "deepmind.google"},
    "Microsoft": {"microsoft.com"},
    "Sony": {"sony.com", "playstation.com"},
    "Nintendo": {"nintendo.com"},
    "Apple": {"apple.com"},
    "Samsung": {"samsung.com"},
    "NVIDIA": {"nvidia.com"},
    "AMD": {"amd.com"},
    "Intel": {"intel.com"},
    "Meta": {"meta.com"},
    "Anthropic": {"anthropic.com"},
    "Mistral": {"mistral.ai"},
    "Hugging Face": {"huggingface.co"},
}
OFFICIAL_ANNOUNCEMENT_VERBS = (
    r"(?:a\s+(?:officiellement\s+)?(?:annonc[ée]|confirm[ée]|révél[ée]|déclar[ée]|publi[ée]|présent[ée])"
    r"|announced|confirmed|revealed|declared|published|released)"
)
SOURCE_RESEARCH_DOMAINS = {"arxiv.org"}
RELEASE_UNCERTAINTY_RE = re.compile(
    r"\b(?:dates?\s+(?:de\s+)?sortie|date\s+officielle|calendrier\s+(?:de\s+)?lancement|disponibilit[ée])"
    r".{0,90}\b(?:incertain(?:e|es|s)?|à confirmer|a confirmer|non confirm[ée]s?|reste(?:nt)? à confirmer)\b"
    r"|\b(?:aucune|pas de)\s+(?:date(?:\s+officielle)?|date de sortie)\b.{0,70}\b(?:communiqu[ée]e?|annonc[ée]e?|confirm[ée]e?)\b"
    r"|\bdates?\b.{0,80}\b(?:incertain(?:e|es|s)?|non confirm[ée]s?|pas confirm[ée]s?|à confirmer|a confirmer)\b"
    r"|\bne\s+(?:fournissent|permettent|suffisent)\s+pas\b.{0,80}\b(?:confirmer|établir|documenter|préciser)\b.{0,50}\bdates?\b",
    re.IGNORECASE,
)

def classify_news_source(domain):
    """Classe une source directe : éditeur si domaine primaire connu, sinon média."""
    host = (domain or "").lower().removeprefix("www.")
    if host in {"news.google.com", "news.bing.com"}:
        return "media"
    if host in SOURCE_RESEARCH_DOMAINS:
        return "source_recherche"
    if any(host == item or host.endswith("." + item) for item in SOURCE_EDITOR_DOMAINS):
        return "source_editeur"
    return "media"

def verifier_dates_incertaines(article_data, selected_sources):
    """Bloque une affirmation d'incertitude sur une date sans source primaire sélectionnée."""
    text = " ".join(str(article_data.get(key, "")) for key in ("title", "summary", "verdict", "tip"))
    has_editor_source = any(
        classify_news_source(urlparse(source.get("url", "")).hostname or "") == "source_editeur"
        for source in selected_sources
    )
    if RELEASE_UNCERTAINTY_RE.search(text) and not has_editor_source:
        raise ValueError(
            "Publication bloquée : une date ou disponibilité est qualifiée d'incertaine "
            "sans source directe de l'éditeur. Vérification requise."
        )

def verifier_attributions_officielles(article_data, selected_sources):
    """Bloque une annonce attribuée à une entreprise sans lien direct vers son domaine."""
    text = " ".join(str(article_data.get(key, "")) for key in ("title", "summary", "verdict", "tip"))
    selected_domains = {
        (urlparse(source.get("url", "")).hostname or "").lower().removeprefix("www.")
        for source in selected_sources
    }
    for organization, official_domains in ORGANIZATION_DOMAINS.items():
        org = re.escape(organization)
        forward = re.search(rf"\b{org}\b.{{0,55}}\b{OFFICIAL_ANNOUNCEMENT_VERBS}\b", text, re.IGNORECASE)
        reverse = re.search(rf"\b{OFFICIAL_ANNOUNCEMENT_VERBS}\b.{{0,55}}\b{org}\b", text, re.IGNORECASE)
        if (forward or reverse) and not any(
            domain == official or domain.endswith("." + official)
            for domain in selected_domains for official in official_domains
        ):
            raise ValueError(
                f"Publication bloquée : annonce attribuée à {organization} sans source directe de cette organisation."
            )


def appliquer_cycle_vie(theme, now=None):
    """Applique une variante avant/après événement, sans modifier le fichier source."""
    result = dict(theme)
    lifecycle = result.get("lifecycle")
    if not isinstance(lifecycle, dict):
        return result
    now = now or datetime.now(UTC)
    try:
        launch_at = datetime.fromisoformat(lifecycle["launch_at"])
        end_at = datetime.fromisoformat(lifecycle["end_at"])
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
    now = datetime.now(UTC)
    return [appliquer_cycle_vie(theme, now) for theme in themes]

def get_priority_event_theme(themes, now=None):
    """Retourne un thème événementiel uniquement pendant sa fenêtre configurée."""
    now = now or datetime.now(UTC)
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
            start_at = datetime.fromisoformat(start_value)
            end_at = datetime.fromisoformat(end_value)
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
    google_url = (
        "https://news.google.com/rss/search?q="
        + quote(query + " when:7d")
        + "&hl=fr&gl=FR&ceid=FR:fr"
    )
    bing_url = (
        "https://www.bing.com/news/search?q="
        + quote(query)
        + "&format=rss&setlang=fr-FR"
    )
    root = None
    failures = []
    for provider, url in (("Google Actualités", google_url), ("Bing News", bing_url)):
        try:
            response = requests.get(
                url, timeout=TIMEOUT,
                headers={"User-Agent": "Mozilla/5.0 (compatible; ObservatoireTechGaming/1.0)"}
            )
            response.raise_for_status()
            candidate = ET.fromstring(response.content)
            if candidate.findall(".//item"):
                root = candidate
                print(f"INFO : flux d'actualités utilisé : {provider}.")
                break
            failures.append(f"{provider}:flux vide")
        except (requests.RequestException, ET.ParseError) as exc:
            failures.append(f"{provider}:{type(exc).__name__}")
    if root is None:
        print("AVERTISSEMENT : moteurs d'actualités indisponibles (" + ", ".join(failures) + "); les flux spécialisés seront utilisés.")
        return []
    items = []
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        parsed_link = urlparse(link)
        if (parsed_link.hostname or "").lower().removeprefix("www.") == "bing.com" and parsed_link.path.startswith("/news/apiclick"):
            target = parse_qs(parsed_link.query).get("url", [""])[0]
            link = target if urlparse(target).scheme == "https" else ""
        if urlparse(link).scheme != "https" or not urlparse(link).netloc:
            continue
        description = (item.findtext("description") or "").strip()
        published = (item.findtext("pubDate") or "").strip()
        if published:
            try:
                published_at = parsedate_to_datetime(published)
                if published_at.tzinfo is None:
                    published_at = published_at.replace(tzinfo=UTC)
                if datetime.now(UTC) - published_at > timedelta(days=7):
                    continue
            except (TypeError, ValueError, OverflowError):
                pass
        description = re.sub(r"<[^>]+>", " ", description)
        description = html.unescape(re.sub(r"\s+", " ", description)).strip()
        if not title or not link:
            continue
        host = (urlparse(link).hostname or "").lower()
        host = host.removeprefix("www.")
        publisher = title.rsplit(" - ", 1)[-1].strip() if " - " in title else host
        headline = title.rsplit(" - ", 1)[0].strip() if " - " in title else title
        items.append({
            "title": headline[:260],
            "publisher": publisher[:100],
            "domain": host[:120],
            "published": published[:100],
            "description": description[:700],
            "url": link,
            "source_type": classify_news_source(host),
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


REGION_ALIASES = {
    "thaïlande": ("thaïlande", "thailand", "thai", "thaïlandais", "thailandais"),
    "france": ("france", "français", "française", "french"),
    "états-unis": ("états-unis", "united states", "usa", "american"),
    "royaume-uni": ("royaume-uni", "united kingdom", "britain", "british"),
    "japon": ("japon", "japan", "japanese"),
    "canada": ("canada", "canadian"),
}


def appliquer_garde_regionale(theme, data, sources):
    """Empêche d'affirmer une disponibilité locale sans source qui mentionne la région."""
    theme_text = str(theme.get("name", "")).casefold()
    corpus = " ".join(
        str(source.get(field, ""))
        for source in sources
        for field in ("title", "description", "url", "publisher")
    ).casefold()
    for region, aliases in REGION_ALIASES.items():
        if region not in theme_text:
            continue
        if any(alias in corpus for alias in aliases):
            return data
        base_title = theme_text.split("—", 1)[0].strip().upper()
        data["title"] = f"{base_title} : les sources ne précisent pas la {region.title()}"
        data["summary"] = (
            f"Les sources consultées abordent l'actualité de {base_title}, mais aucune ne mentionne "
            f"la {region.title()}. Elles ne permettent donc pas de confirmer la disponibilité du jeu "
            f"ni son heure de lancement dans ce pays. Les informations régionales doivent être vérifiées "
            "auprès de l'éditeur et de la boutique officielle de la région concernée."
        )
        data["verdict"] = f"Disponibilité en {region.title()} non confirmée par les sources consultées."
        data["tip"] = (
            "Consulter les annonces de l'éditeur et la boutique officielle de la région avant de conclure."
        )
        print(f"INFO : garde régionale appliquée — aucune source ne mentionne {region.title()}.")
        return data
    return data


VERSION_CLAIM_RE = re.compile(
    r"\b(?:Unreal Engine|Unity|Godot|GameMaker)\s+\d+(?:\.\d+)*\b",
    re.IGNORECASE,
)


def appliquer_garde_versions(data, sources):
    """Empêche d'annoncer une version logicielle absente des sources consultées."""
    corpus = " ".join(
        str(source.get(field, ""))
        for source in sources
        for field in ("title", "description", "url")
    ).casefold()
    claims = VERSION_CLAIM_RE.findall(
        " ".join(str(data.get(field, "")) for field in ("title", "summary", "verdict", "tip"))
    )
    unsupported = sorted({claim for claim in claims if claim.casefold() not in corpus})
    if not unsupported:
        return data
    claim_text = " et ".join(unsupported)
    data["title"] = "Moteurs de jeu : versions non confirmées par les sources"
    data["summary"] = (
        f"Les sources consultées abordent les moteurs et outils de création de jeux, mais elles ne "
        f"confirment pas l'annonce ou la disponibilité de {claim_text}. Il serait donc prématuré de "
        "présenter cette version comme une nouveauté publiée. Les notes de version et annonces des "
        "éditeurs restent les références à consulter pour vérifier ces informations."
    )
    data["verdict"] = "Version précise non confirmée par les sources consultées."
    data["tip"] = "Consulter les notes de version officielles de l'éditeur avant de retenir un numéro de version."
    print("INFO : garde de version appliquée — affirmation non présente dans les sources.")
    return data


NUMBER_CLAIM_RE = re.compile(r"\d+(?:[.,]\d+)?")


def appliquer_garde_chiffres(theme, data, sources):
    """Refuse les chiffres et caractéristiques numériques absents des titres/descriptions sources."""
    if "version précise non confirmée" in str(data.get("verdict", "")).casefold():
        return data
    source_text = " ".join(
        str(source.get(field, ""))
        for source in sources
        for field in ("title", "description")
    )
    supported_numbers = set(NUMBER_CLAIM_RE.findall(source_text))
    article_text = " ".join(
        str(data.get(field, ""))
        for field in ("title", "summary", "verdict", "tip")
    )
    unsupported = sorted({
        number for number in NUMBER_CLAIM_RE.findall(article_text)
        if number not in supported_numbers
    })
    if not unsupported:
        return data
    base_title = str(theme.get("name", "Actualités Tech")).split("—", 1)[0].strip()
    data["title"] = f"{base_title} : détails chiffrés non confirmés"
    data["summary"] = (
        f"Les sources consultées mentionnent {base_title}, mais elles ne fournissent pas suffisamment "
        "d'éléments pour confirmer les caractéristiques chiffrées avancées. Les performances, la "
        "compatibilité et les spécifications techniques doivent être vérifiées dans les fiches officielles."
    )
    data["verdict"] = "Les chiffres et caractéristiques détaillés ne sont pas établis par les sources consultées."
    data["tip"] = "Consulter les annonces et fiches techniques officielles avant de retenir des chiffres précis."
    print("INFO : garde des chiffres appliquée — données numériques non présentes dans les sources.")
    return data


def appliquer_garde_sources_faibles(theme, data, sources):
    """N'autorise pas une synthèse détaillée quand les extraits ne font que répéter les titres."""
    substantive = False
    for source in sources:
        title_words = set(re.findall(r"\w+", str(source.get("title", "")).casefold()))
        description_words = set(re.findall(r"\w+", str(source.get("description", "")).casefold()))
        if len(description_words - title_words) >= 6:
            substantive = True
            break
    if substantive:
        return data
    base_title = str(theme.get("name", "Actualités Tech")).split("—", 1)[0].strip()
    data["title"] = f"{base_title} : détails insuffisants dans les sources"
    data["summary"] = (
        f"Les résultats récupérés signalent une actualité liée à {base_title}, mais les extraits disponibles "
        "reprennent surtout les titres et ne fournissent pas assez d'éléments pour confirmer la portée, "
        "les effets ou les modalités de l'annonce. Consultez l'article d'origine et le communiqué de "
        "l'organisation concernée avant de retenir des détails."
    )
    data["verdict"] = "Les extraits récupérés ne suffisent pas pour confirmer les détails."
    data["tip"] = "Lire l'article original et rechercher un communiqué officiel avant de partager l'information."
    print("INFO : garde de qualité des sources appliquée — extraits trop courts ou redondants.")
    return data

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
- Ne conclus jamais qu'une annonce, une date de sortie ou une disponibilité n'existe pas simplement parce que les sources récupérées n'en parlent pas.
- N'écris jamais « date officielle à confirmer », « aucune date annoncée » ou une formule équivalente sans une source explicite de l'éditeur qui le dit.
- Si la source disponible ne documente pas une date, écris précisément : « les sources consultées ici ne documentent pas cette date ; cela ne signifie pas qu'elle n'a pas déjà été annoncée ».
- Pour les dates, prix, plateformes et caractéristiques techniques, privilégie une source primaire de l'éditeur ou du fabricant. Si elle manque, limite clairement la portée de l'affirmation et ne présente pas une absence de preuve comme une preuve d'absence.
- Les agents spécialisés ne sont pas des sources indépendantes : ne reprends leurs affirmations que si les liens fournis les confirment.
- Un média (par exemple IGN ou GameSpot) est une source journalistique, pas une annonce officielle de l'éditeur du jeu. Seules les sources classées "source_editeur" peuvent être présentées comme une confirmation de l'éditeur ; les sources de recherche et les médias doivent être nommés correctement.
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

    data = appliquer_garde_sources_faibles(theme, data, sources)
    data = appliquer_garde_regionale(theme, data, sources)
    data = appliquer_garde_versions(data, sources)
    data = appliquer_garde_chiffres(theme, data, sources)
    title = data["title"].strip()[:140]
    summary = data["summary"].strip()[:1200]
    verdict = data["verdict"].strip()[:500]
    tip = data["tip"].strip()[:500]

    indices = data["source_indices"]

    def indices_valides(values):
        return (
            isinstance(values, list)
            and bool(values)
            and all(
                isinstance(index, int)
                and not isinstance(index, bool)
                and 0 <= index < len(sources)
                for index in values
            )
        )

    if not indices_valides(indices):
        # Répare une sélection d'indices erronée sans modifier le texte généré.
        repair_messages = [
            {
                "role": "system",
                "content": "Tu sélectionnes des sources. Réponds uniquement en JSON valide avec la clé source_indices.",
            },
            {
                "role": "user",
                "content": (
                    "Choisis les indices des sources qui soutiennent réellement cet article. "
                    f"Les indices commencent à 0 et vont de 0 à {len(sources) - 1}. "
                    "N'invente aucun indice. Réponds avec {\"source_indices\": [0]} au format JSON.\n"
                    + json.dumps(
                        {"title": title, "summary": summary, "verdict": verdict,
                         "tip": tip, "sources": sources},
                        ensure_ascii=False,
                    )
                ),
            },
        ]
        try:
            repaired_raw, _ = generate_text(
                repair_messages, max_tokens=300, temperature=0.0, json_mode=True
            )
            repaired_raw = re.sub(r"^\s*\x60{3}(?:json)?\s*", "", repaired_raw, flags=re.IGNORECASE)
            repaired_raw = re.sub(r"\s*\x60{3}\s*$", "", repaired_raw)
            repaired_data = json.loads(repaired_raw)
            indices = repaired_data.get("source_indices") if isinstance(repaired_data, dict) else None
        except Exception as exc:
            raise ValueError(
                "La réponse IA contient un indice de source invalide. Aucun article publié."
            ) from exc
        if not indices_valides(indices):
            raise ValueError("La réponse IA contient un indice de source invalide. Aucun article publié.")

    used_sources = []
    for index in indices:
        if sources[index] not in used_sources:
            used_sources.append(sources[index])
    if not used_sources:
        raise ValueError("Aucune source valide sélectionnée. Aucun article publié.")
    checked_text = {"title": title, "summary": summary, "verdict": verdict, "tip": tip}
    verifier_dates_incertaines(checked_text, used_sources)
    verifier_attributions_officielles(checked_text, used_sources)

    return {
        "id": datetime.now(UTC).strftime("%Y%m%dT%H%M%S") + "-" + uuid4().hex[:8],
        "date": datetime.now(UTC).isoformat(timespec="minutes"),
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
            raise TypeError("site/articles.json n'est pas une liste. Publication annulée pour préserver les archives.")
        return data
    except json.JSONDecodeError as exc:
        raise RuntimeError("site/articles.json est invalide. Publication annulée pour préserver les archives.") from exc
    except OSError as exc:
        raise RuntimeError("Impossible de lire les archives existantes. Publication annulée.") from exc

# Le flux public ne conserve qu'une occurrence par titre ou résumé normalisé.
def normaliser_texte_article(value):
    """Normalise titre et résumé pour éviter les doublons exacts de publication."""
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", str(value or "").casefold())).strip()

def save_articles(article):
    SITE_DIR.mkdir(parents=True, exist_ok=True)
    articles = load_previous_articles()
    articles.insert(0, article)
    unique = []
    seen_ids = set()
    seen_titles = set()
    seen_summaries = set()
    for item in articles:
        key = item.get("id")
        title_key = normaliser_texte_article(item.get("title"))
        summary_key = normaliser_texte_article(item.get("summary"))
        if not key or key in seen_ids:
            continue
        seen_ids.add(key)
        duplicate = (
            (title_key and title_key in seen_titles)
            or (summary_key and summary_key in seen_summaries)
        )
        if title_key:
            seen_titles.add(title_key)
        if summary_key:
            seen_summaries.add(summary_key)
        if duplicate:
            continue
        unique.append(item)
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
        except Exception as exc:  # noqa: BLE001 - les SDK IA ont des exceptions spécifiques.
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
        await edge_tts.Communicate(spoken, "fr-FR-RemyMultilingualNeural", rate="-5%", pitch="+0Hz", volume="+0%").save(str(audio_dir / filename))
        return f"audio/{filename}"
    except Exception as exc:  # noqa: BLE001 - edge-tts et ses transports ont plusieurs exceptions spécifiques.
        print(f"Audio non créé ({type(exc).__name__}: {exc}); article texte conservé.")
        return None

def main():
    themes = load_themes()
    theme = choose_theme(themes)
    print(f"Thème choisi : {theme['name']}")
    def collect_sources(selected_theme):
        general = fetch_news(selected_theme["query"], limit=MAX_SOURCES)
        official = fetch_specialized_sources(selected_theme["name"], limit=4)
        merged = []
        seen_urls = set()
        # Les flux officiels apportent des annonces primaires ; les médias généralistes
        # complètent le contexte. On déduplique les URL avant de transmettre à l'IA.
        for source in official + general:
            key = source.get("url", "").split("#", 1)[0]
            if key and key not in seen_urls:
                merged.append(source)
                seen_urls.add(key)
            if len(merged) >= MAX_SOURCES:
                break
        return merged, len(official)

    sources, official_count = collect_sources(theme)
    print(f"{official_count} source(s) spécialisée(s) officielle(s) disponible(s).")
    if not sources:
        # Un thème de jeu précis peut ne rien retourner pendant quelques heures.
        # Le plan B bascule explicitement sur la veille gaming générale : aucun
        # article générique ne sera présenté comme une actualité du jeu ciblé.
        fallback_theme = {
            "name": "Gaming et jeux vidéo — veille générale (recherche de secours)",
            "query": "jeux vidéo gaming actualité officielle mises à jour annonces éditeurs"
        }
        print("AVERTISSEMENT : aucune source pour le thème ciblé ; tentative de veille gaming générale.")
        theme = fallback_theme
        sources, official_count = collect_sources(theme)
        print(f"{official_count} source(s) officielle(s) disponible(s) après recherche de secours.")
    if not sources:
        raise RuntimeError("Aucune source RSS exploitable, même après recherche de secours. Aucun article publié.")
    print(f"{len(sources)} source(s) récupérée(s).")
    profiles = load_agent_profiles()
    reports = executer_agents_dynamiques(theme, sources, profiles)
    if reports:
        print(f"{len(reports)} agent(s) spécialisé(s) ont rendu une analyse.")
    try:
        article = create_article(theme, sources, reports)
    except ValueError as first_error:
        # Une réponse IA peut échouer à une vérification factuelle stricte.
        # Ne jamais affaiblir le contrôle : tenter une seule fois un sujet plus large.
        fallback_theme = {
            "name": "Technologie, IA et jeux vidéo — veille générale de secours",
            "query": "actualité technologie intelligence artificielle jeux vidéo annonces officielles"
        }
        if theme["name"] == fallback_theme["name"]:
            raise
        print(
            "AVERTISSEMENT : article refusé par les contrôles factuels "
            f"({type(first_error).__name__}). Nouvelle tentative sur une veille générale."
        )
        fallback_sources, fallback_official_count = collect_sources(fallback_theme)
        if not fallback_sources:
            raise RuntimeError(
                "Le sujet initial a été refusé et aucune source n'est disponible pour le sujet de secours."
            ) from first_error
        print(
            f"{len(fallback_sources)} source(s) récupérée(s) pour le sujet de secours "
            f"({fallback_official_count} source(s) officielle(s))."
        )
        fallback_reports = executer_agents_dynamiques(
            fallback_theme, fallback_sources, profiles
        )
        article = create_article(fallback_theme, fallback_sources, fallback_reports)
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
