"""Contrôles techniques de publication ; ce module ne remplace pas un avis juridique."""
import re
from datetime import datetime, timezone
from pathlib import Path

LOG_FILE = Path("journal_conformite_legale.txt")
SECRET_PATTERNS = [
    re.compile(r"gsk_[A-Za-z0-9]{20,}"), re.compile(r"hf_[A-Za-z0-9]{20,}"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"), re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
]
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)

def verifier_conformite_legale(proposition_action, type_action="PUBLICATION"):
    contenu = str(proposition_action or "")
    problemes = []
    if any(p.search(contenu) for p in SECRET_PATTERNS):
        problemes.append("possible clé API ou jeton secret")
    if EMAIL_RE.search(contenu):
        problemes.append("adresse e-mail")
    if problemes:
        with LOG_FILE.open("a", encoding="utf-8") as log:
            log.write(f"[{datetime.now(timezone.utc).isoformat()}] [{type_action}] REFUS : {'; '.join(problemes)}\n")
        print(f"Publication bloquée : {'; '.join(problemes)}")
        return False
    return True
