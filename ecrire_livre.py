"""Générateur manuel d'encyclopédie annuelle à partir des archives."""
import os
from pathlib import Path

from agent_gardien import verifier_conformite_legale
from ai_providers import generate_text

ROOT=Path(__file__).resolve().parent
def generer_encyclopedie_annuelle():
    memory=ROOT/"memoire_tech.txt"
    if not memory.exists() or not memory.read_text(encoding="utf-8").strip():
        print("Livre non créé : aucune mémoire disponible."); return None
    public=memory.read_text(encoding="utf-8")[-24000:]
    secret=ROOT/"coffre_secret_livre.txt"
    extras=secret.read_text(encoding="utf-8")[-8000:] if secret.exists() else ""
    result, provider=generate_text([
      {"role":"system","content":"Tu écris un guide documentaire en français, sans inventer de faits."},
      {"role":"user","content":f"""Rédige « Encyclopédie des outils et tendances Tech & IA ».
Organise par thèmes. Distingue faits sourcés, hypothèses et conseils. N'affirme pas qu'une information est secrète sans preuve.
Notes publiques :\n{public}\nNotes complémentaires :\n{extras}"""}],
      reasoning_effort="low",max_completion_tokens=6000)
    text=(r.choices[0].message.content or "").strip()
    if len(text)<1000 or not verifier_conformite_legale(text,"LIVRE_ANNUEL"):
        raise RuntimeError("Texte vide, trop court ou bloqué par le filtre de sécurité.")
    out=ROOT/"ENCYCLOPEDIE_TECH_IA.md"
    out.write_text(f"# Encyclopédie Tech & IA\n\nOuvrage assisté par {provider}. Vérifiez les sources originales.\n\n"+text,encoding="utf-8")
    print("Livre créé :",out); return str(out)

if __name__=="__main__": generer_encyclopedie_annuelle()
