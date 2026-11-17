"""Générateur manuel d'encyclopédie annuelle à partir des archives."""
import os
from pathlib import Path

from groq import Groq

from agent_gardien import verifier_conformite_legale

ROOT=Path(__file__).resolve().parent
MODEL=os.getenv("GROQ_MODEL","openai/gpt-oss-20b")

def generer_encyclopedie_annuelle():
    memory=ROOT/"memoire_tech.txt"
    if not memory.exists() or not memory.read_text(encoding="utf-8").strip():
        print("Livre non créé : aucune mémoire disponible."); return None
    public=memory.read_text(encoding="utf-8")[-24000:]
    secret=ROOT/"coffre_secret_livre.txt"
    extras=secret.read_text(encoding="utf-8")[-8000:] if secret.exists() else ""
    if not os.getenv("GROQ_API_KEY"): raise RuntimeError("Secret GROQ_API_KEY absent.")
    c=Groq(api_key=os.environ["GROQ_API_KEY"],timeout=90,max_retries=2)
    r=c.chat.completions.create(model=MODEL,messages=[
      {"role":"system","content":"Tu écris un guide documentaire en français, sans inventer de faits."},
      {"role":"user","content":f"""Rédige « Encyclopédie des outils et tendances Tech & IA ».
Organise par thèmes. Distingue faits sourcés, hypothèses et conseils. N'affirme pas qu'une information est secrète sans preuve.
Notes publiques :\n{public}\nNotes complémentaires :\n{extras}"""}],
      reasoning_effort="low",max_completion_tokens=6000)
    text=(r.choices[0].message.content or "").strip()
    if len(text)<1000 or not verifier_conformite_legale(text,"LIVRE_ANNUEL"):
        raise RuntimeError("Texte vide, trop court ou bloqué par le filtre de sécurité.")
    out=ROOT/"ENCYCLOPEDIE_TECH_IA.md"
    out.write_text("# Encyclopédie Tech & IA\n\nOuvrage assisté par IA. Vérifiez les sources originales.\n\n"+text,encoding="utf-8")
    print("Livre créé :",out); return str(out)

if __name__=="__main__": generer_encyclopedie_annuelle()
