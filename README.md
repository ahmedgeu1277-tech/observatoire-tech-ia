# Usine IA Tech & Gaming 24-7

Observatoire automatisé en français sur l'IA, les jeux vidéo, Roblox, le matériel et la cybersécurité.

## Fonctionnement
- GitHub Actions lance le programme deux fois par jour (09 h et 18 h UTC).
- Le programme récupère des actualités publiques via Google News RSS.
- Groq rédige une synthèse prudente à partir des titres et descriptions récupérés.
- Les articles sont enregistrés dans `site/articles.json`.
- Le site public affiche les articles et leurs liens sources.

## Configuration
1. Dans GitHub, ouvrir Settings → Secrets and variables → Actions.
2. Vérifier que le secret `GROQ_API_KEY` existe. Ne jamais le copier dans le code.
3. Dans Settings → Actions → General, autoriser les workflows à écrire dans le dépôt (Read and write permissions).
4. Dans Settings → Pages, choisir Deploy from a branch, branche `main`, dossier `/ (root)` ou `/site`.
   - Si tu choisis `/ (root)`, le fichier `index.html` de la racine charge `site/articles.json`.
   - Si tu choisis `/site`, le fichier `site/index.html` charge `site/articles.json`.
5. Dans Actions, lancer « Usine IA Tech & Gaming 24-7 » avec Run workflow.

## Limites
- GitHub Actions n'est pas un serveur permanent : il exécute le programme aux horaires prévus.
- Le site est public si GitHub Pages est activé sur un dépôt public.
- Les résumés IA peuvent contenir des erreurs. Vérifie les sources.
- Respecte les conditions d'âge et d'utilisation de GitHub et de Groq. Demande l'aide d'un parent ou tuteur pour les comptes et services qui l'exigent.
