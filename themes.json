import os
import asyncio
from groq import Groq
import edge_tts
from agent_gardien import verifier_conformite_legale

async def creer_documentaire_tech():
    if not os.path.exists("memoire_tech.txt"):
        return
    with open("memoire_tech.txt", "r", encoding="utf-8") as f:
        archives = f.read()[-8000:]
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    plan_rep = client.chat.completions.create(
        messages=[{"role": "user", "content": f"Crée 5 titres de chapitres pour un documentaire Tech et Gaming de 20 min basé sur : {archives}. Un titre par ligne."}],
        model="llama-3.3-70b-versatile"
    )
    chapitres = plan_rep.choices[0].message.content.strip().split("\n")[:5]
    script_total = "Bienvenue dans le grand dossier hebdomadaire de l'Observatoire Tech et Gaming, généré avec l'assistance d'une intelligence artificielle. "
    for idx, titre in enumerate(chapitres, 1):
        rep = client.chat.completions.create(
            messages=[{"role": "user", "content": f"Rédige le chapitre {idx} ('{titre}') d'un documentaire objectif de 650 mots en français basé sur : {archives}. Sans emojis."}],
            model="llama-3.3-70b-versatile"
        )
        script_total += rep.choices[0].message.content + "\n\n"
        await asyncio.sleep(5)

    if verifier_conformite_legale(script_total[:3000], type_action="DOCUMENTAIRE_LONG"):
        with open("script_docu_semaine.txt", "w", encoding="utf-8") as f:
            f.write(script_total)
        comm = edge_tts.Communicate(script_total, "fr-FR-HenriNeural")
        await comm.save("documentaire_tech_20min.mp3")

if __name__ == "__main__":
    asyncio.run(creer_documentaire_tech())

