"""Documentaire hebdomadaire écrit, avec audio facultatif."""
import asyncio, os
from datetime import datetime, timezone
from pathlib import Path
from groq import Groq
from agent_gardien import verifier_conformite_legale

ROOT=Path(__file__).resolve().parent
MODEL=os.getenv("GROQ_MODEL","openai/gpt-oss-20b")

async def creer_documentaire_tech():
    memory=ROOT/"memoire_tech.txt"
    if not memory.exists() or not memory.read_text(encoding="utf-8").strip():
        print("Documentaire ignoré : mémoire encore vide."); return None
    if not os.getenv("GROQ_API_KEY"): return None
    notes=memory.read_text(encoding="utf-8")[-16000:]
    c=Groq(api_key=os.environ["GROQ_API_KEY"],timeout=60,max_retries=2)
    plan=c.chat.completions.create(model=MODEL,messages=[
      {"role":"user","content":f"Donne cinq titres de chapitres pour un documentaire Tech & IA basé uniquement sur ces notes. Un titre par ligne.\n{notes}"}],
      reasoning_effort="low",max_completion_tokens=500)
    titles=[x.strip(" -•0123456789.\t") for x in (plan.choices[0].message.content or "").splitlines() if x.strip()][:5]
    if not titles: return None
    parts=["# Documentaire hebdomadaire Tech & IA","","Script assisté par IA. Vérifier les sources originales.",""]
    for i,title in enumerate(titles,1):
        r=c.chat.completions.create(model=MODEL,messages=[
          {"role":"system","content":"Tu rédiges en français et n'inventes aucun fait."},
          {"role":"user","content":f"Rédige environ 350 mots pour le chapitre « {title} ». Utilise uniquement les notes et signale les incertitudes.\n{notes}"}],
          reasoning_effort="low",max_completion_tokens=1000)
        body=(r.choices[0].message.content or "").strip()
        if body: parts.extend([f"## Chapitre {i} — {title}",body,""])
    script="\n".join(parts)
    if len(script)<1000 or not verifier_conformite_legale(script,"DOCUMENTAIRE"): return None
    folder=ROOT/"archives"; folder.mkdir(exist_ok=True)
    stamp=datetime.now(timezone.utc).strftime("%Y%m%d")
    md=folder/f"documentaire_tech_{stamp}.md"; md.write_text(script,encoding="utf-8")
    try:
        import edge_tts
        audio=ROOT/"site"/"audio"; audio.mkdir(parents=True,exist_ok=True)
        mp3=audio/f"documentaire_tech_{stamp}.mp3"
        await edge_tts.Communicate(script[:12000]+" Documentaire assisté par intelligence artificielle.","fr-FR-HenriNeural").save(str(mp3))
        print("Audio créé :",mp3)
    except Exception as e: print(f"Audio non créé : {type(e).__name__}: {e}")
    print("Documentaire créé :",md); return str(md)

if __name__=="__main__": asyncio.run(creer_documentaire_tech())
