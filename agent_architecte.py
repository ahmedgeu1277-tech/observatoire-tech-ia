import os
from groq import Groq
from agent_gardien import verifier_conformite_legale

def creer_nouvel_agent_autonome():
    print("[Agent Architecte] Analyse des besoins pour créer un nouvel agent...")
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    os.makedirs("agents_dynamiques", exist_ok=True)
    agents_existants = os.listdir("agents_dynamiques")
    memoire = ""
    if os.path.exists("memoire_tech.txt"):
        with open("memoire_tech.txt", "r", encoding="utf-8") as f:
            memoire = f.read()[-4000:]

    prompt_idee = f"""
Agents dynamiques existants : {agents_existants}
Tendances récentes de notre observatoire : {memoire}
Propose UNE nouvelle spécialité d'agent utile et légale (ex: comparateur_outils_gratuits, detecteur_astuces_gaming, vulgarisateur_ia).
Réponds uniquement par un nom de fichier en minuscules sans accents finissant par .py (ex: agent_outils_gratuits.py).
"""
    rep_nom = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt_idee}],
        model="llama-3.3-70b-versatile"
    )
    nom_fichier = rep_nom.choices[0].message.content.strip().replace(" ", "_")
    if not nom_fichier.endswith(".py") or nom_fichier in agents_existants:
        print("Aucun nouvel agent nécessaire lors de ce cycle.")
        return

    prompt_code = f"""
Écris le code Python complet pour '{nom_fichier}'.
Il doit définir exactement : `def executer_mission(contexte_tech):`
Cette fonction utilise `from groq import Groq` et `import os` pour analyser `contexte_tech` selon la spécialité '{nom_fichier}', et retourne un rapport objectif de 50 mots en français.
Réponds UNIQUEMENT avec le code Python pur, sans balises markdown.
"""
    rep_code = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt_code}],
        model="llama-3.3-70b-versatile"
    )
    code_genere = rep_code.choices[0].message.content.strip().replace("```python", "").replace("```", "")

    if not verifier_conformite_legale(code_genere, type_action="CREATION_AGENT"):
        return

    try:
        compile(code_genere, nom_fichier, "exec")
        chemin = os.path.join("agents_dynamiques", nom_fichier)
        with open(chemin, "w", encoding="utf-8") as f:
            f.write(code_genere)
        print(f"[Agent Architecte] Nouvel agent créé et validé : {chemin}")
    except SyntaxError as e:
        print(f"[Sécurité] Code rejeté (erreur syntaxe) : {e}")

