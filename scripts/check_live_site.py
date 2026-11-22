"""Vérifie le site NEXORA réellement publié et ses médias publics."""
from __future__ import annotations

import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urljoin, urlparse
from urllib.request import Request, urlopen

BASE_URL = os.getenv(
    "SITE_BASE_URL",
    "https://ahmedgeu1277-tech.github.io/observatoire-tech-ia/",
).rstrip("/") + "/"
TIMEOUT = 20
failures: list[str] = []
checks = 0


def request(url: str, method: str = "HEAD"):
    global checks
    checks += 1
    req = Request(url, method=method, headers={"User-Agent": "NEXORA-Live-Healthcheck/1.0"})
    try:
        return urlopen(req, timeout=TIMEOUT)
    except HTTPError as exc:
        if method == "HEAD" and exc.code in (403, 405, 501):
            return request(url, "GET")
        raise


def check_url(path: str, label: str, *, expected_type: str | None = None) -> bool:
    url = urljoin(BASE_URL, path)
    try:
        with request(url) as response:
            status = response.status
            content_type = response.headers.get("Content-Type", "").lower()
            length = response.headers.get("Content-Length")
            if status < 200 or status >= 400:
                raise RuntimeError(f"HTTP {status}")
            if expected_type and expected_type not in content_type:
                raise RuntimeError(f"type MIME inattendu : {content_type or 'absent'}")
            if length == "0":
                raise RuntimeError("fichier vide")
        print(f"OK {label}: HTTP {status}" + (f", {length} octets" if length else ""))
        return True
    except (HTTPError, URLError, TimeoutError, OSError, RuntimeError) as exc:
        message = f"ECHEC {label}: {type(exc).__name__}: {exc}"
        print(message)
        failures.append(message)
        return False


def read_json(path: str, label: str):
    global checks
    url = urljoin(BASE_URL, path)
    checks += 1
    try:
        req = Request(url, headers={"User-Agent": "NEXORA-Live-Healthcheck/1.0"})
        with urlopen(req, timeout=TIMEOUT) as response:
            if response.status != 200:
                raise RuntimeError(f"HTTP {response.status}")
            data = json.loads(response.read().decode("utf-8"))
        print(f"OK {label}: JSON valide")
        return data
    except (HTTPError, URLError, TimeoutError, OSError, UnicodeDecodeError,
            json.JSONDecodeError, RuntimeError) as exc:
        message = f"ECHEC {label}: {type(exc).__name__}: {exc}"
        print(message)
        failures.append(message)
        return None


def safe_media_path(folder: str, filename: object) -> str | None:
    if not isinstance(filename, str) or not filename.strip():
        return None
    # Les manifestes ne peuvent référencer que des noms de fichiers simples.
    if filename != filename.rsplit("/", 1)[-1] or filename in (".", "..") or "\\" in filename:
        return None
    return f"site/{folder}/{quote(filename)}"


def main() -> int:
    print(f"Surveillance de production : {BASE_URL}")
    for path, label, mime in (
        ("", "page racine", "text/html"),
        ("site/index.html", "accueil NEXORA", "text/html"),
        ("site/ville-demo.html", "simulation de ville", "text/html"),
        ("site/documentaire-test.html", "page documentaire", "text/html"),
    ):
        check_url(path, label, expected_type=mime)

    articles = read_json("site/articles.json", "catalogue des actualités")
    if not isinstance(articles, list) or not articles:
        failures.append("ECHEC catalogue : aucun article publié.")
        articles = []
    else:
        print(f"OK catalogue : {len(articles)} article(s)")
        for index, article in enumerate(articles):
            if not isinstance(article, dict):
                failures.append(f"Article {index}: structure invalide.")
                continue
            if not isinstance(article.get("sources"), list) or not article["sources"]:
                failures.append(f"Article {article.get('id', index)}: aucune source.")
            audio = article.get("audio_url")
            if audio:
                parsed = urlparse(str(audio))
                if parsed.scheme or parsed.netloc or not str(audio).startswith("audio/") or ".." in parsed.path.split("/"):
                    failures.append(f"Article {article.get('id', index)}: chemin audio non autorisé.")
                else:
                    media_path = "site/" + str(audio)
                    check_url(media_path, f"audio article {article.get('id', index)}",
                              expected_type="audio/")

    manifest = read_json("site/documentaire-test.json", "manifeste documentaire")
    if isinstance(manifest, dict):
        for key, folder, mime in (
            ("audio_file", "audio", "audio/"),
            ("video_file", "video", "video/"),
        ):
            filename = manifest.get(key)
            path = safe_media_path(folder, filename)
            if not path:
                failures.append(f"Manifeste : champ {key} invalide.")
            else:
                check_url(path, f"documentaire {key}", expected_type=mime)

        translations = manifest.get("translations", {})
        if not isinstance(translations, dict):
            failures.append("Manifeste : traductions invalides.")
        else:
            for language, media in translations.items():
                if not isinstance(media, dict):
                    failures.append(f"Traduction {language}: manifeste invalide.")
                    continue
                for key, folder, mime in (
                    ("audio", "audio", "audio/"),
                    ("video", "video", "video/"),
                    ("subtitles", "video", "text/vtt"),
                ):
                    path = safe_media_path(folder, media.get(key))
                    if not path:
                        failures.append(f"Traduction {language}: fichier {key} absent ou invalide.")
                    else:
                        check_url(path, f"{language} {key}", expected_type=mime)

    print(f"Bilan : {checks} requête(s) de contrôle, {len(failures)} erreur(s).")
    if failures:
        print("\n".join(failures))
        return 1
    print("SURVEILLANCE PRODUCTION : TOUT EST ACCESSIBLE.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
