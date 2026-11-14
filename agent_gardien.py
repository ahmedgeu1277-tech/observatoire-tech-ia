import os
from groq import Groq
import yt_dlp

def verifier_actualite_loi():
    options = {'quiet': True, 'extract_flat': True}
    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            res = ydl.extract_info("ytsearch2:AI Act Europe RGPD loi numerique", download=False)
            return " | ".join([v.get('title', '') for v in res.get('entries', [])])
    except Exception:
        return "AI Act UE, RGPD, Code Propriete Intellectuelle, LCEN France."

def verifier_conformite_legale(proposition_action, type_action="PUBLICATION"):
    print("[Agent Gardien Juridique] Vérification lois FR / UE / Internationales...")
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    contexte_legal = verifier_actualite_loi()
    prompt = f"""
Tu es un juriste expert en droit numérique français, européen (RGPD, AI Act) et international (propriété intellectuelle, droit d'auteur).
Actualités juridiques : {contexte_legal}
Type d'action : {type_action}
Contenu ou code à vérifier :
"{proposition_action}"

Vérifie strictement ces 5 obligations légales :
1. TRANSPARENCE IA (AI Act UE) : Le contenu respecte-t-il l'obligation de transparence IA sans tromper le public ?
2. VIE PRIVÉE (RGPD) : Aucune donnée personnelle (nom réel, e-mail, adresse, IP) n'est collectée ou publiée ?
3. PROPRIÉTÉ INTELLECTUELLE (France/International) : Analyse originale sans plagiat ni contournement de sécurité ?
4. DIFFAMATION (Loi LCEN France) : Aucune accusation grave sans preuve contre une personne ou une marque ?
5. FAISABILITÉ & ÉTHIQUE : Action techniquement réalisable gratuitement et respectueuse des règles des plateformes ?

Si UNE SEULE règle n'est pas respectée, réponds UNIQUEMENT par :
"NON : [règle légale concernée et explication courte]"
Si tout est 100 % conforme, réponds UNIQUEMENT par :
"OUI"
"""
    rep = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile"
    )
    verdict = rep.choices[0].message.content.strip()
    if verdict.startswith("NON"):
        print(f"[Agent Gardien] ACTION BLOQUÉE -> {verdict}")
        with open("journal_conformite_legale.txt", "a", encoding="utf-8") as log:
            log.write(f"[REFUS LÉGAL] {verdict} | Action : {proposition_action[:120]}...\n")
        return False
    print("[Agent Gardien] 100 % Conforme aux lois FR/UE/Internationales.")
    return True

