"""Veille hebdomadaire : propose un thème à partir de titres RSS publics."""
import json
import os
from pathlib import Path
from urllib.parse import quote

import requests
from defusedxml import ElementTree as ET

from ai_providers import generate_text

ROOT = Path(__file__).resolve().parent
FILE = ROOT / "themes.json"

def decouvrir_nouvelle_tendance_tech():
    try:
        url = "https://news.google.com/rss/search?q=" + quote("innovation technologie IA gaming cette semaine") + "&hl=fr&gl=FR&ceid=FR:fr"
        response = requests.get(url, timeout=25, headers={"User-Agent": "UsineIATechGaming/1.0"})
        response.raise_for_status()
        root = ET.fromstring(response.content)
        titles = [(item.findtext("title") or "").strip() for item in root.findall(".//item")[:8]]
        titles = [title for title in titles if title]
        if not titles or not any(os.getenv(key) for key in ("GROQ_API_KEY", "HF_API_KEY", "HF_TOKEN")):
            return False
        raw, provider = generate_text([
            {"role": "system", "content": "Propose un thème précis et non redondant fondé sur les titres. Réponds uniquement en JSON valide."},
            {"role": "user", "content": "Titres récents :\n" + "\n".join(titles) + "\nRéponds en JSON avec name et query."},
        ], max_tokens=500, temperature=0.2, json_mode=True)
        raw = raw.strip()
        if not raw.startswith("{"):
            start, end = raw.find("{"), raw.rfind("}")
            if start < 0 or end <= start:
                raise ValueError("Réponse JSON absente")
            raw = raw[start:end + 1]
        data = json.loads(raw)
        name = str(data.get("name", "")).strip()[:90]
        query = str(data.get("query", "")).strip()[:240]
        if not name or not query:
            return False
        existing = json.loads(FILE.read_text(encoding="utf-8"))
        themes = existing.get("themes", [])
        if any(theme.get("name", "").casefold() == name.casefold() for theme in themes):
            return False
        themes.append({"name": name, "query": query})
        existing["themes"] = themes[:30]
        FILE.write_text(json.dumps(existing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Nouveau thème ajouté via {provider} : {name}")
        return True
    except Exception as exc:  # noqa: BLE001 — la veille est facultative et isolée.
        print(f"Veille hebdomadaire : {type(exc).__name__}")
        return False

if __name__ == "__main__":
    decouvrir_nouvelle_tendance_tech()
