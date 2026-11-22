"""Contrôle de santé du dépôt et des contenus avant publication."""
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
REQUIRED_ARTICLE_FIELDS = ("id", "date", "theme", "title", "summary", "verdict", "tip", "sources")


def _check_documentary_media(root: Path) -> int:
    """Vérifie que les médias référencés par le documentaire public existent."""
    manifest_path = root / "site" / "documentaire-test.json"
    if not manifest_path.exists():
        return 0
    manifest = _read_json(manifest_path)
    if not isinstance(manifest, dict):
        raise ValueError("Le manifeste du documentaire doit être un objet JSON.")

    def check_file(folder: str, name: object, extension: str) -> None:
        if (
            not isinstance(name, str)
            or not name
            or Path(name).name != name
            or "\\\\" in name
            or not name.lower().endswith(extension)
        ):
            raise ValueError(f"Référence média invalide : {folder}/{name}.")
        base = (root / "site" / folder).resolve()
        target = (base / name).resolve()
        try:
            target.relative_to(base)
        except ValueError as exc:
            raise ValueError(f"Média hors du dossier public autorisé : {folder}/{name}.") from exc
        if not target.is_file() or target.stat().st_size == 0:
            raise ValueError(f"Média du documentaire absent ou vide : {folder}/{name}.")

    check_file("audio", manifest.get("audio_file"), ".mp3")
    check_file("video", manifest.get("video_file"), ".mp4")
    check_file("archives", manifest.get("archive_file"), ".md")
    media_count = 3
    translations = manifest.get("translations", {})
    if not isinstance(translations, dict):
        raise ValueError("Les traductions du documentaire doivent être un objet.")
    for language, variant in translations.items():
        if not isinstance(language, str) or not isinstance(variant, dict):
            raise ValueError("Variante de traduction documentaire invalide.")
        for field, folder, extension in (
            ("audio", "audio", ".mp3"),
            ("video", "video", ".mp4"),
            ("subtitles", "video", ".vtt"),
        ):
            name = variant.get(field)
            if name is not None:
                check_file(folder, name, extension)
                media_count += 1
    return media_count


def _read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"JSON illisible : {path.relative_to(ROOT)}") from exc


def _is_safe_source_url(value: object) -> bool:
    """Accepte uniquement une URL HTTPS absolue sans identifiants intégrés."""
    if not isinstance(value, str) or not value or any(char.isspace() for char in value):
        return False
    try:
        parsed = urlparse(value)
        return (
            parsed.scheme.lower() == "https"
            and bool(parsed.hostname)
            and parsed.username is None
            and parsed.password is None
            and parsed.port in (None, 443)
        )
    except ValueError:
        return False


def check_repository(root: Path = ROOT) -> dict:
    root = Path(root).resolve()
    themes = _read_json(root / "themes.json")
    if not isinstance(themes, dict) or not isinstance(themes.get("themes"), list) or not themes["themes"]:
        raise ValueError("themes.json doit contenir une liste non vide de thèmes.")
    for index, theme in enumerate(themes["themes"]):
        if (
            not isinstance(theme, dict)
            or not isinstance(theme.get("name"), str) or not theme["name"].strip()
            or not isinstance(theme.get("query"), str) or not theme["query"].strip()
        ):
            raise ValueError(f"Thème invalide à l'index {index}.")

    articles = _read_json(root / "site" / "articles.json")
    if not isinstance(articles, list):
        raise ValueError("site/articles.json doit être une liste.")
    ids = set()
    audio_count = 0
    source_count = 0
    audio_root = (root / "site" / "audio").resolve()
    for index, article in enumerate(articles):
        if not isinstance(article, dict) or any(
            not isinstance(article.get(k), str) or not article[k].strip()
            for k in REQUIRED_ARTICLE_FIELDS if k != "sources"
        ):
            raise ValueError(f"Article incomplet à l'index {index}.")
        if not isinstance(article["sources"], list) or not article["sources"]:
            raise ValueError(f"Article sans source : {article['id']}.")
        article_id = article["id"]
        if article_id in ids:
            raise ValueError(f"Identifiant d'article dupliqué : {article_id}.")
        ids.add(article_id)
        for source in article["sources"]:
            if not isinstance(source, dict) or not _is_safe_source_url(source.get("url")):
                raise ValueError(f"URL de source non sécurisée dans {article_id}.")
            source_count += 1
        audio_url = article.get("audio_url")
        if audio_url:
            if not isinstance(audio_url, str) or not audio_url.startswith("audio/") or ".." in Path(audio_url).parts:
                raise ValueError(f"Chemin audio invalide dans {article_id}.")
            audio_path = (root / "site" / audio_url).resolve()
            try:
                audio_path.relative_to(audio_root)
            except ValueError as exc:
                raise ValueError(f"Chemin audio hors du dossier autorisé : {audio_url}.") from exc
            if not audio_path.is_file() or audio_path.stat().st_size == 0:
                raise ValueError(f"Fichier audio absent ou vide : {audio_url}.")
            audio_count += 1

    documentary_media = _check_documentary_media(root)

    profiles_count = 0
    profiles_path = root / "site" / "data" / "agents.json"
    if profiles_path.exists():
        profile_index = _read_json(profiles_path)
        if not isinstance(profile_index, dict) or not isinstance(profile_index.get("profiles"), list):
            raise ValueError("site/data/agents.json doit contenir une liste de profils.")
        for profile in profile_index["profiles"]:
            if not isinstance(profile, dict) or not all(
                isinstance(profile.get(key), str) and profile[key].strip()
                for key in ("name", "role", "mission", "status")
            ):
                raise ValueError("Profil IA incomplet dans agents.json.")
            if "non exécuté" not in profile["status"].casefold():
                raise ValueError("Un profil configuré ne doit pas être présenté comme un agent actif.")
        profiles_count = len(profile_index["profiles"])

    # Les données de la ville sont internes : leur présence dans site/ est une fuite.
    public_city_state = root / "site" / "data" / "gouvernement.json"
    if public_city_state.exists():
        raise ValueError("Données internes interdites dans site/data/gouvernement.json.")

    return {
        "themes": len(themes["themes"]),
        "articles": len(articles),
        "sources": source_count,
        "audio_files": audio_count,\n        "documentary_media_files": documentary_media,
        "city_state_public": False,
        "agent_profiles": profiles_count,
    }


if __name__ == "__main__":
    result = check_repository()
    print("DIAGNOSTIC OK — " + json.dumps(result, ensure_ascii=False))
