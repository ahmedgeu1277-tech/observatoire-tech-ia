import os
import json
import random
import asyncio
import importlib.util
from datetime import datetime
import yt_dlp
from groq import Groq
from huggingface_hub import InferenceClient
import edge_tts
import requests
from agent_gardien import verifier_conformite_legale

def lire_regles_apprises():
    if os.path.exists("regles_apprises.txt"):
        with open("regles_apprises.txt", "r", encoding="utf-8") as f:
            return f.read()
    return "Sois objectif, clair et cite toujours tes sources."

def choisir_theme_et_mode():
    with open("themes.json", "r", encoding="utf-8") as f:
        catalogue = json.load(f)["thematiques"]
    theme = random.choice(catalogue)
    aujourd_hui = datetime.now().strftime("%Y-%m-%d")
    if aujourd_hui < theme["date_lancement"]:
        return theme["nom"], "AVANT_SORTIE", theme["recherche_avant"]
    return theme["nom"], "APRES_SORTIE", theme["recherche_apres"]

def agent_radar(recherche):
    options = {'quiet': True, 'extract_flat': True}
    with yt_dlp.YoutubeDL(options) as ydl:
        res = ydl.extract_info(f"ytsearch5:{recherche}", download=False)
        return "\n".join([f"- {v.get('title')}" for v in res.get('entries', [])])

def chef_orchestre_labo(titres, nom_theme, mode):
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    prompt = f"""
Tu es le directeur d'un laboratoire de test Tech, IA et Gaming.
Thème : {nom_theme} (Mode : {mode})
Titres trouvés :
{titres}
Choisis la nouveauté la plus importante. Résume en 2 phrases : ce qui est annoncé vs ce qu'il faut vérifier techniquement.
"""
    rep = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile"
    )
    return rep.choices[0].message.content

def executer_agents_dynamiques(sujet):
    if not os.path.exists("agents_dynamiques"):
        return ""
    rapports = []
    for fichier in os.listdir("agents_dynamiques"):
        if fichier.endswith(".py"):
            chemin = os.path.join("agents_dynamiques", fichier)
            spec = importlib.util.spec_from_file_location(fichier[:-3], chemin)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if hasattr(module, "executer_mission"):
                rapports.append(module.executer_mission(sujet))
    return "\n".join(rapports)

def agent_scenariste_verite(sujet, rapports_specialistes):
    client = InferenceClient(token=os.environ.get("HF_API_KEY"))
    regles = lire_regles_apprises()
    prompt = f"""
Tu es le présentateur d'un laboratoire de décryptage Tech, IA et Gaming réputé pour sa rigueur.
Sujet : {sujet}
Analyses complémentaires : {rapports_specialistes}
Règles apprises : {regles}
Rédige un flash de 85 mots en français en 3 étapes :
1. LA NOUVEAUTÉ : Ce qui vient d'être annoncé ou lancé.
2. LE VERDICT LABO : Est-ce vraiment utile et vérifié, ou juste du marketing ?
3. L'ASTUCE PRATIQUE : Comment en profiter ou le tester aujourd'hui.
Uniquement le texte parlé, sans emojis ni titres.
"""
    rep = client.chat_completion(
        model="Qwen/Qwen2.5-72B-Instruct",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=250
    )
    return rep.choices[0].message.content

def agent_controleur_et_coach(script, sujet):
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    prompt = f"""
Vérifie ce script sur '{sujet}' :
"{script}"
S'il fait moins de 105 mots, est objectif, en bon français et sans emojis, réponds UNIQUEMENT : VALIDE.
Sinon, réécris-le proprement et ajoute à la fin sur une nouvelle ligne : REGLE: [leçon apprise en 1 phrase].
"""
    rep = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile"
    )
    res = rep.choices[0].message.content.strip()
    if res == "VALIDE":
        return script
    if "REGLE:" in res:
        parties = res.split("REGLE:")
        with open("regles_apprises.txt", "a", encoding="utf-8") as f:
            f.write(f"- {parties[1].strip()}\n")
        return parties[0].strip()
    return res

def agent_tri_secret(info_brute):
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    prompt = f"Cette astuce Tech/IA/Gaming est-elle une pépite rare peu connue du grand public ? '{info_brute}'. Réponds UNIQUEMENT : SECRET ou PUBLIC."
    rep = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile"
    )
    if "SECRET" in rep.choices[0].message.content:
        with open("coffre_secret_livre.txt", "a", encoding="utf-8") as f:
            f.write(f"[EXCLUSIF LIVRE] {info_brute}\n")
        return True
    return False

async def agent_voix(texte, nom_audio):
    texte_avec_mention = texte + " Analyse générée par intelligence artificielle."
    comm = edge_tts.Communicate(texte_avec_mention, "fr-FR-HenriNeural")
    await comm.save(nom_audio)

def publier_site_et_discord(script, nom_audio, nom_theme):
    maintenant = datetime.now().strftime("%d/%m/%Y à %H:%M")
    mention = "Analyse générée par l'Observatoire IA (Conformité AI Act)."
    nouvel_article = f"""
  <div class="carte">
    <span class="date">[{nom_theme}] Flash Labo du {maintenant}</span>
    <p>{script}</p>
    <audio controls src="{nom_audio}"></audio>
    <div class="mention-ia">{mention}</div>
  </div>
"""
    with open("index.html", "r", encoding="utf-8") as f:
        html = f.read()
    html = html.replace("<!-- NOUVEAUX_ARTICLES -->", f"<!-- NOUVEAUX_ARTICLES -->\n{nouvel_article}")
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

    url_webhook = os.environ.get("DISCORD_WEBHOOK")
    if url_webhook:
        with open(nom_audio, "rb") as f:
            requests.post(
                url_webhook,
                data={"content": f"**[{nom_theme}] Verdict Labo ({maintenant}) :**\n{script}\n*({mention})*"},
                files={"file": (nom_audio, f)}
            )

async def main():
    nom_theme, mode, requete = choisir_theme_et_mode()
    if datetime.now().weekday() == 1:
        requete += " weekly release update"
    infos = agent_radar(requete)
    sujet = chef_orchestre_labo(infos, nom_theme, mode)
    rapports_dyn = executer_agents_dynamiques(sujet)
    brouillon = agent_scenariste_verite(sujet, rapports_dyn)
    script_final = agent_controleur_et_coach(brouillon, sujet)

    if not verifier_conformite_legale(script_final, type_action="PUBLICATION_WEB_DISCORD"):
        print("Publication annulée par l'Agent Gardien Juridique.")
        return

    with open("memoire_tech.txt", "a", encoding="utf-8") as f:
        f.write(f"[{nom_theme}] {script_final}\n")

    if agent_tri_secret(script_final):
        print("Pépite archivée uniquement pour le livre annuel.")
        return

    horodatage = datetime.now().strftime("%Y%m%d_%H%M")
    nom_audio = f"flash_{horodatage}.mp3"
    await agent_voix(script_final, nom_audio)
    publier_site_et_discord(script_final, nom_audio, nom_theme)

if __name__ == "__main__":
    asyncio.run(main())

