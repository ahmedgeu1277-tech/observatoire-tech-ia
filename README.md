# Usine IA Tech & Gaming 24-7

Observatoire automatisé francophone consacré à l'IA, au gaming, à Roblox, au matériel et à la cybersécurité.

## Site
GitHub Pages : https://ahmedgeu1277-tech.github.io/observatoire-tech-ia/

Dans Settings → Pages, choisir la branche `main` et le dossier `/ (root)`. Le fichier racine `index.html` charge les articles depuis `site/articles.json`.

## Cycle quotidien
- GitHub Actions planifie deux cycles de veille par jour, à 09 h et 18 h UTC ; GitHub peut retarder les tâches planifiées.
- Google News RSS récupère des titres, descriptions et liens publics.
- Le gestionnaire IA essaie les fournisseurs configurés dans l'ordre (Groq puis Hugging Face par défaut) et bascule si le premier échoue.
- Les profils de `agents_dynamiques/` fournissent des analyses spécialisées ; ce sont des profils pilotés par le programme, pas des agents autonomes indépendants.
- Un filtre technique recherche les secrets courants.
- Edge TTS crée une narration quand le service vocal est disponible.
- Chaque jour, un workflow assemble quatre dossiers, crée des diapositives originales et produit une vidéo MP4 H.264/AAC.
- Les vidéos, audios et copies Markdown datés sont conservés au moins 30 jours dans `site/video/`, `site/audio/` et `site/archives/`. Le nettoyage automatique ne supprime que les fichiers âgés de plus de 30 jours ; les versions récentes ne sont pas effacées à chaque nouvelle publication.
- La page de documentaire présente la dernière édition ; les éditions précédentes restent dans les archives du site.
- Les articles sont publiés dans `site/articles.json` et les résumés dans `memoire_tech.txt`.

## Agents et tâches hebdomadaires
Le workflow du dimanche propose un thème, crée une fiche d'agent spécialisée et prépare un documentaire écrit et audio. Les profils d'agents sont des configurations JSON : ils ne génèrent ni n'exécutent librement du code Python.

## Orchestrateur de missions IA (prototype contrôlé)
- `orchestrateur.py` lance une mission JSON avec jusqu'à trois rôles spécialisés : chercheur, critique et architecte.
- Les rapports sont enregistrés dans `.laboratoire_prive/missions/`, dossier ignoré par Git. Ils ne sont pas publiés sur le site.
- Les missions sont limitées à 180 secondes maximum ; ce n'est pas encore une équipe d'agents persistants.

## Encyclopédie annuelle
Le générateur `ecrire_livre.py` est manuel. Il utilise `memoire_tech.txt` et, si présent, `coffre_secret_livre.txt`.

## Secrets et permissions
- Settings → Secrets and variables → Actions : vérifier `GROQ_API_KEY`.
- Ne jamais placer une clé API dans un fichier du dépôt.
- Aucun composant Discord n'est utilisé.

## Limites et sécurité
- GitHub Actions exécute des tâches planifiées, pas un serveur permanent 24 h/24 ; les horaires peuvent être retardés.
- Le filtre automatique est une protection de premier niveau, pas une certification de conformité.
- Les résumés et audios IA peuvent contenir des erreurs : vérifier les sources originales.
- Respecter les conditions d'âge et d'utilisation des services ; demander l'aide d'un parent ou tuteur lorsque nécessaire.

Voir `docs/ETAT_AVANCEMENT_GLOBAL.md` pour l'état réel du projet et ses limites.
