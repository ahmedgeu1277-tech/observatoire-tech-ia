# Usine IA Tech & Gaming 24-7

Observatoire automatisé francophone consacré à l'IA, au gaming, à Roblox, au matériel et à la cybersécurité.

## Site
GitHub Pages : https://ahmedgeu1277-tech.github.io/observatoire-tech-ia/

Dans Settings → Pages, choisir la branche `main` et le dossier `/ (root)`. Le fichier racine `index.html` charge les articles depuis `site/articles.json`.

## Cycle quotidien
- GitHub Actions lance la veille à 09 h et 18 h UTC.
- Google News RSS récupère des titres, descriptions et liens publics.
- Groq rédige une synthèse française structurée.
- Les profils de `agents_dynamiques/` peuvent effectuer jusqu'à deux analyses spécialisées par publication.
- Un filtre technique recherche les clés API, jetons, clés privées, secrets courants et adresses e-mail détectables.
- Edge TTS crée un court audio quand le service vocal est disponible.
- Les articles sont publiés dans `site/articles.json`, les audios dans `site/audio/` et les résumés sont archivés dans `memoire_tech.txt`.

## Agents et tâches hebdomadaires
Le workflow du dimanche :
- propose un thème de veille dans `themes.json` ;
- crée une fiche d'agent spécialisée en JSON dans `agents_dynamiques/` ;
- prépare un documentaire écrit et, si possible, audio.

Les profils d'agents sont des configurations JSON : ils ne génèrent ni n'exécutent librement du code Python.

## Encyclopédie annuelle
Le générateur `ecrire_livre.py` est manuel. Il utilise `memoire_tech.txt` et, si présent, `coffre_secret_livre.txt`.

## Secrets et permissions
- Settings → Secrets and variables → Actions : vérifier `GROQ_API_KEY`.
- Settings → Actions → General : autoriser les workflows à écrire dans le dépôt.
- Ne jamais placer une clé API dans un fichier du dépôt.
- Aucun composant Discord n'est utilisé.

## Limites et sécurité
- GitHub Actions exécute des tâches planifiées : ce n'est pas un serveur permanent 24 h/24. Les horaires cron peuvent être retardés par GitHub.
- Le filtre automatique est une protection technique de premier niveau, pas un avis juridique ni une certification de conformité.
- Limites anti-ralentissement : six sources maximum par article, deux agents spécialisés maximum, 30 articles conservés et délai réseau de 20 secondes.\n- Priorités d'exécution : sécurité, tests et intégrité des données ; publication essentielle ; audio facultatif ; archives secondaires.\n- Les résumés et audios IA peuvent contenir des erreurs : vérifier les sources originales.
- Respecter les conditions d'âge et d'utilisation des services ; demander l'aide d'un parent ou tuteur lorsque nécessaire.


## Architecture modulaire et continuité
Voir [docs/ARCHITECTURE_SECURITE.md](docs/ARCHITECTURE_SECURITE.md) pour les modules séparés, le basculement IA, les règles de compartimentation et le plan de reprise.
