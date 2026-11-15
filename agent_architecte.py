"""Agent architecte : crée des profils d'agents en JSON, jamais du code exécutable."""
import json, os, re
from pathlib import Path
from groq import Groq

ROOT=Path(__file__).resolve().parent
PROFILE_DIR=ROOT/"agents_dynamiques"
MODEL=os.getenv("GROQ_MODEL","openai/gpt-oss-20b")

def creer_nouvel_agent_autonome():
    key=os.getenv("GROQ_API_KEY")
    if not key:
        print("Architecte ignoré : GROQ_API_KEY absent."); return None
    PROFILE_DIR.mkdir(parents=True,exist_ok=True)
    existing=sorted(p.stem for p in PROFILE_DIR.glob("*.json"))
    prompt=f"""Propose un profil d'agent spécialisé utile pour un observatoire Tech, IA, gaming et cybersécurité.
Aucun code, script, commande ou accès à un compte. Analyse uniquement des sources publiques fournies.
Agents existants : {existing}
Réponds en JSON avec name, role, mission, instructions. name : minuscules et underscores."""
    try:
        c=Groq(api_key=key,timeout=45,max_retries=2)
        r=c.chat.completions.create(model=MODEL,messages=[{"role":"user","content":prompt}],
            response_format={"type":"json_object"},reasoning_effort="low",max_completion_tokens=900)
        d=json.loads((r.choices[0].message.content or "").strip())
        name=re.sub(r"[^a-z0-9_]","_",str(d.get("name","")).lower()).strip("_")
        if not name or len(name)>40 or name in existing: return None
        profile={"name":name,"role":str(d.get("role","Analyste"))[:120],
          "mission":str(d.get("mission",""))[:500],"instructions":str(d.get("instructions",""))[:1000],
          "safety":"Sources fournies uniquement ; aucune publication autonome ; aucun code exécutable."}
        if not profile["mission"] or not profile["instructions"]: return None
        path=PROFILE_DIR/f"{name}.json"
        path.write_text(json.dumps(profile,ensure_ascii=False,indent=2),encoding="utf-8")
        print(f"Profil d'agent créé : {path}"); return str(path)
    except Exception as e:
        print(f"Architecte : {type(e).__name__}: {e}"); return None

if __name__=="__main__": creer_nouvel_agent_autonome()
