"""Génère les variantes traduites des documentaires (voix, vidéo et sous-titres)."""
from __future__ import annotations

import asyncio
import json
import re
import subprocess
from pathlib import Path

from ai_providers import generate_text
from video_documentaire import generer_video

LANGUAGES = {
    "en": {"name": "English", "voice": "en-US-AriaNeural"},
    "es": {"name": "Español", "voice": "es-ES-ElviraNeural"},
    "de": {"name": "Deutsch", "voice": "de-DE-KatjaNeural"},
    "pt": {"name": "Português", "voice": "pt-PT-RaquelNeural"},
    "ar": {"name": "العربية", "voice": "ar-SA-ZariyahNeural"},
    "zh": {"name": "中文", "voice": "zh-CN-XiaoxiaoNeural"},
}


def _timecode(seconds: float) -> str:
    millis = max(0, int(seconds * 1000))
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    secs, millis = divmod(millis, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02}.{millis:03}"


def _translate_payload(language: str, title: str, intro: str, chapters: list[dict]) -> dict:
    payload = {"title": title, "intro": intro, "chapters": [
        {"title": c["title"], "summary": c["summary"], "verdict": c["verdict"], "tip": c["tip"]}
        for c in chapters
    ]}
    messages = [
        {"role": "system", "content": (
            "You are a professional documentary translator. Translate every human-readable field into "
            f"{LANGUAGES[language]['name']}. Return only valid JSON with exactly the same keys and array order. "
            "Preserve facts, uncertainty, names of games/products, model numbers and technical terms. "
            "Do not add facts, sources, URLs, publisher names or commentary. Do not translate proper product names."
        )},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}
    ]
    result, _provider = generate_text(messages, max_tokens=3500, temperature=0.1, json_mode=True, timeout=90)
    translated = json.loads(result)
    if not isinstance(translated, dict) or not isinstance(translated.get("chapters"), list):
        raise ValueError("Réponse de traduction invalide.")
    if len(translated["chapters"]) != len(chapters):
        raise ValueError("Le nombre de chapitres traduits ne correspond pas.")
    for key in ("title", "intro"):
        if not isinstance(translated.get(key), str) or not translated[key].strip():
            raise ValueError(f"Champ traduit manquant : {key}")
    for item in translated["chapters"]:
        if not isinstance(item, dict) or any(not isinstance(item.get(k), str) or not item[k].strip()
                                              for k in ("title", "summary", "verdict", "tip")):
            raise ValueError("Chapitre traduit incomplet.")
    return translated


def generer_variantes_multilingues(title: str, intro: str, dossiers: list[dict],
                                    audio_dir: Path, video_dir: Path,
                                    stamp: str) -> dict:
    """Produit six versions audio/vidéo et un fichier JSON de textes traduits."""
    audio_dir, video_dir = Path(audio_dir), Path(video_dir)
    audio_dir.mkdir(parents=True, exist_ok=True)
    video_dir.mkdir(parents=True, exist_ok=True)
    results = {}
    base_chapters = [{
        "title": str(d["title"]),
        "summary": str(d["summary"]),
        "verdict": str(d.get("verdict", "")),
        "tip": str(d.get("tip", "")),
    } for d in dossiers]

    for code, config in LANGUAGES.items():
        try:
            translated = _translate_payload(code, title, intro, base_chapters)
            spoken_parts = [translated["title"], translated["intro"]]
            slides = [("Introduction", translated["title"], translated["intro"])]
            for index, chapter in enumerate(translated["chapters"], 1):
                spoken = (chapter["title"] + ". " + chapter["summary"] + " " +
                          chapter["verdict"] + " " + chapter["tip"])
                spoken_parts.append(spoken)
                slides.append((f"Chapter {index}", chapter["title"],
                               chapter["summary"] + " " + chapter["verdict"] + " " + chapter["tip"]))

            audio_name = f"documentaire-{code}-{stamp}.mp3"
            video_name = f"documentaire-{code}-{stamp}.mp4"
            vtt_name = f"documentaire-{code}-{stamp}.vtt"
            audio_path, video_path = audio_dir / audio_name, video_dir / video_name

            async def speak():
                import edge_tts
                text = " ".join(spoken_parts)
                await asyncio.wait_for(
                    edge_tts.Communicate(text[:24000], config["voice"], rate="-5%").save(str(audio_path)),
                    timeout=240,
                )

            asyncio.run(speak())
            if not audio_path.is_file() or audio_path.stat().st_size < 1000:
                raise RuntimeError("Fichier audio traduit absent ou incomplet.")
            generer_video(audio_path, slides, video_path)

            probe = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)],
                check=True, capture_output=True, text=True, timeout=30,
            )
            duration = float(probe.stdout.strip())
            captions = [translated["title"] + ". " + translated["intro"]]
            captions.extend(c["title"] + ". " + c["summary"] + " " + c["verdict"] + " " + c["tip"]
                            for c in translated["chapters"])
            weights = [max(1, len(x)) for x in captions]
            total = sum(weights)
            cursor = 0.0
            vtt = ["WEBVTT", ""]
            for caption, weight in zip(captions, weights):
                end = min(duration, cursor + duration * weight / total)
                vtt.extend([f"{_timecode(cursor)} --> {_timecode(end)}", caption, ""])
                cursor = end
            (video_dir / vtt_name).write_text("\n".join(vtt), encoding="utf-8")
            results[code] = {
                "name": config["name"], "audio": audio_name, "video": video_name,
                "subtitles": vtt_name, "text": translated,
            }
            print(f"INFO : variante {code} générée.")
        except Exception as exc:
            # Une langue indisponible ne doit pas empêcher le documentaire français.
            print(f"AVERTISSEMENT : variante {code} non générée ({type(exc).__name__}).")
    return results
