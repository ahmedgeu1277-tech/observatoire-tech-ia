"""Documentaire hebdomadaire compilé à partir des articles publiés et vérifiés."""
import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path

from agent_gardien import verifier_conformite_legale

ROOT = Path(__file__).resolve().parent
ARTICLES_FILE = ROOT / "site" / "articles.json"


def charger_dossiers():
    if not ARTICLES_FILE.is_file():
        raise RuntimeError("Le fichier des articles publiés est absent.")
    articles = json.loads(ARTICLES_FILE.read_text(encoding="utf-8"))
    if not isinstance(articles, list):
        raise RuntimeError("Le fichier des articles n'est pas une liste.")

    selected = []
    seen_themes = set()
    for article in sorted(articles, key=lambda item: str(item.get("date", "")), reverse=True):
        if not isinstance(article, dict):
            continue
        theme = str(article.get("theme") or article.get("title") or "").strip()
        title = str(article.get("title") or "").strip()
        summary = str(article.get("summary") or "").strip()
        verdict = str(article.get("verdict") or "").strip()
        tip = str(article.get("tip") or "").strip()
        sources = article.get("sources")
        if not theme or theme.casefold() in seen_themes or not title or len(summary) < 40:
            continue
        if not isinstance(sources, list) or not sources:
            continue
        secure_sources = [
            source for source in sources
            if isinstance(source, dict) and str(source.get("url", "")).startswith("https://")
        ]
        if not secure_sources:
            continue
        selected.append({
            "theme": theme,
            "title": title,
            "summary": summary,
            "verdict": verdict,
            "tip": tip,
            "sources": secure_sources[:3],
        })
        seen_themes.add(theme.casefold())
        if len(selected) == 3:
            break
    if len(selected) < 3:
        raise RuntimeError("Il faut au moins trois dossiers récents avec des sources HTTPS.")
    return selected


def construire_chapitres(dossiers):
    chapters = []
    for number, dossier in enumerate(dossiers, 1):
        source_names = ", ".join(
            str(source.get("publisher") or source.get("domain") or "source")
            for source in dossier["sources"]
        )
        body = (
            f"Le dossier publié par l'Observatoire s'intitule « {dossier['title']} ». "
            f"Résumé éditorial : {dossier['summary']} "
            f"Évaluation : {dossier['verdict']} "
            f"Conseil : {dossier['tip']} "
            f"Les références associées sont : {source_names}. "
            "Les éléments explicitement signalés comme incertains ne doivent pas être présentés "
            "comme des faits établis. Pour approfondir, il faut ouvrir les sources originales "
            "et vérifier leur date, leur contexte et leur portée."
        )
        chapters.append((number, dossier["title"], body, dossier["sources"]))

    chapters.append((
        4,
        "Comment vérifier une annonce",
        "Avant de conclure qu'un jeu, un logiciel ou une mise à jour est disponible, il faut "
        "distinguer une annonce officielle, une rumeur, un article de presse et une simple absence "
        "d'information. Vérifier le communiqué de l'éditeur, la boutique officielle de la région "
        "concernée et la date de publication. Une source qui ne parle pas d'un pays ne prouve pas "
        "que le produit y est indisponible. Le bon réflexe consiste à signaler ce que les sources "
        "confirment et ce qu'elles ne précisent pas.",
        [],
    ))
    chapters.append((
        5,
        "Comment vérifier les chiffres et caractéristiques",
        "Les numéros de version, les dates de sortie, les prix, les performances et les caractéristiques "
        "techniques doivent être rattachés à une source précise. Comparer le modèle exact, la région, "
        "la version du logiciel et la date du communiqué. Si un chiffre n'apparaît pas dans les sources "
        "consultées, il ne faut pas le compléter par une supposition ou par une ancienne fiche technique. "
        "Mieux vaut publier une information limitée mais vérifiable qu'un détail spectaculaire non confirmé.",
        [],
    ))
    return chapters


async def creer_documentaire_tech():
    dossiers = charger_dossiers()
    chapters = construire_chapitres(dossiers)
    title = "Revue hebdomadaire Tech & Gaming : faits, incertitudes et vérifications"
    intro = (
        "Cette édition rassemble trois dossiers récents publiés par l'Observatoire et deux chapitres "
        "de méthode. Elle reprend les résumés éditoriaux et leurs sources sans ajouter de nouvelles "
        "affirmations techniques. Les points incertains restent explicitement signalés."
    )

    parts = ["# " + title, "", intro, "", "Documentaire compilé automatiquement à partir des articles publiés.", ""]
    for number, heading, body, sources in chapters:
        parts.extend([f"## Chapitre {number} — {heading}", body])
        if sources:
            parts.append("Sources :")
            for source in sources:
                publisher = str(source.get("publisher") or source.get("domain") or "Source")
                parts.append(f"- {publisher} : {source['url']}")
        parts.append("")
    script = "\n".join(parts)
    if not verifier_conformite_legale(script, "DOCUMENTAIRE"):
        raise RuntimeError("Documentaire bloqué par le contrôle de sécurité.")

    stamp = datetime.now(UTC).strftime("%Y%m%d")
    folder = ROOT / "archives"
    folder.mkdir(exist_ok=True)
    markdown = folder / f"documentaire_tech_{stamp}.md"
    markdown.write_text(script, encoding="utf-8")

    audio_folder = ROOT / "site" / "audio"
    audio_folder.mkdir(parents=True, exist_ok=True)

    async def produire_audio():
        import edge_tts

        created = 0
        for number, heading, body, _sources in chapters:
            spoken = f"Chapitre {number}. {heading}. {body}"
            audio_file = audio_folder / f"documentaire_tech_{stamp}_chapitre_{number}.mp3"
            try:
                await edge_tts.Communicate(spoken, "fr-FR-HenriNeural").save(str(audio_file))
                if not audio_file.exists() or audio_file.stat().st_size < 1000:
                    audio_file.unlink(missing_ok=True)
                    raise RuntimeError("fichier audio absent ou trop petit")
                created += 1
                print(f"Piste audio {number} créée.")
            except Exception as exc:  # noqa: BLE001 — une piste défaillante ne bloque pas les autres.
                print(f"Piste audio {number} indisponible ({type(exc).__name__}: {str(exc)[:120]}).")
            await asyncio.sleep(2)
        print(f"Pistes audio créées : {created}/5.")

    await produire_audio()
    print(f"Documentaire écrit : {markdown}")
    return str(markdown)


if __name__ == "__main__":
    asyncio.run(creer_documentaire_tech())
