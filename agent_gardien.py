"""Contrôles techniques avant publication ; ne constitue pas une certification juridique."""
import re
from datetime import datetime, timezone
from pathlib import Path

LOG_FILE = Path("journal_conformite_legale.txt")

# Détection en première ligne de secrets courants. Aucun secret n'est journalisé.
SECRET_PATTERNS = [
    re.compile(r"gsk_[A-Za-z0-9]{20,}"),
    re.compile(r"hf_[A-Za-z0-9]{20,}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"AIza[0-9A-Za-z_-]{30,}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    re.compile(r"(?i)\b(?:api[_-]?key|access[_-]?token|client[_-]?secret|password)\s*[:=]\s*['\"]?[^\s'\"]{12,}"),
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{20,}"),
]
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)


def verifier_conformite_legale(proposition_action, type_action="PUBLICATION"):
    contenu = str(proposition_action or "")
    problemes = []
    if any(pattern.search(contenu) for pattern in SECRET_PATTERNS):
        problemes.append("possible secret, jeton ou clé privée")
    if EMAIL_RE.search(contenu):
        problemes.append("adresse e-mail potentiellement personnelle")
    if problemes:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a", encoding="utf-8") as log:
            log.write(
                f"[{datetime.now(timezone.utc).isoformat()}] "
                f"[{type_action}] REFUS : {'; '.join(problemes)}\n"
            )
        print(f"Publication bloquée : {'; '.join(problemes)}")
        return False
    return True
