"""Veille hebdomadaire : propose un nouveau thème à partir de titres RSS publics."""
import json, os
from pathlib import Path
from urllib.parse import quote
import xml.etree.ElementTree as ET
import requests
from groq import Groq

ROOT=Path(__file__).resolve().parent
FILE=ROOT/"themes.json"
MODEL=os.getenv("GROQ_MODEL","openai/gpt-oss-20b")

def decouvrir_nouvelle_tendance_tech():
    try:
        url="https://news.google.com/rss/search?q="+quote("innovation technologie IA gaming cette semaine")+"&hl=fr&gl=FR&ceid=FR:fr"
        res=requests.get(url,timeout=25,headers={"User-Agent":"UsineIATechGaming/1.0"})
        res.raise_for_status()
        root=ET.fromstring(res.content)
        titles=[(x.findtext("title") or "").strip() for x in root.findall(".//item")[:8]]
        titles=[x for x in titles if x]
        if not titles or not os.getenv("GROQ_API_KEY"): return False
        c=Groq(api_key=os.environ["GROQ_API_KEY"],timeout=45,max_retries=2)
        r=c.chat.completions.create(model=MODEL,messages=[
          {"role":"system","content":"Propose un thème précis et non redondant, fondé sur les titres."},
          {"role":"user","content":"Titres récents :\n"+"\n".join(titles)+"\nRéponds en JSON avec name et query."}],
          response_format={"type":"json_object"},reasoning_effort="low",max_completion_tokens=500)
        d=json.loads((r.choices[0].message.content or "").strip())
        name=str(d.get("name","")).strip()[:90]; query=str(d.get("query","")).strip()[:240]
        if not name or not query: return False
        data=json.loads(FILE.read_text(encoding="utf-8")); items=data.get("themes",[])
        if any(x.get("name","").casefold()==name.casefold() for x in items): return False
        items.append({"name":name,"query":query}); data["themes"]=items[:30]
        FILE.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
        print("Nouveau thème ajouté :",name); return True
    except Exception as e:
        print(f"Veille hebdomadaire : {type(e).__name__}: {e}"); return False

if __name__=="__main__": decouvrir_nouvelle_tendance_tech()
