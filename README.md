# Usine IA Tech & Gaming 24-7

Observatoire automatisé francophone consacré à l'IA, au gaming, à Roblox, au matériel et à la cybersécurité.

## Site
GitHub Pages : https://ahmedgeu1277-tech.github.io/observatoire-tech-ia/

Dans Settings → Pages, choisir la branche `main` et le dossier `/ (root)`. Le fichier racine `index.html` charge les articles depuis `site/articles.json`.

## Cycle quotidien
- GitHub Actions planifie deux cycles de veille par jour, à 09 h et 18 h UTC ; GitHub peut retarder les tâches planifiées et ce n'est pas un serveur permanent.
- Google News RSS récupère des titres, descriptions et liens publics.
- Le gestionnaire IA essaie les fournisseurs configurés dans l'ordre (Groq puis Hugging Face par défaut) et bascule si le premier échoue.
- Les profils de `agents_dynamiques/` peuvent fournir jusqu'à deux analyses spécialisées par publication, en utilisant le basculement Groq/Hugging Face ; ce sont des profils pilotés par le programme, pas des agents autonomes indépendants.
- Un filtre technique recherche les clés API, jetons, clés privées, secrets courants et adresses e-mail détectables.
- Edge TTS crée une narration quand le service vocal est disponible.
- Le workflow de documentaire assemble quatre dossiers publiés, crée des diapositives originales avec Pillow et produit une vidéo MP4 H.264/AAC avec FFmpeg.
- Les articles sont publiés dans `site/articles.json`, les audios dans `site/audio/`, la vidéo temporaire dans `site/video/` et les résumés dans `memoire_tech.txt`.

## Agents et tâches hebdomadaires
Le workflow du dimanche :
- propose un thème de veille dans `themes.json` ;
- crée une fiche d'agent spécialisée en JSON dans `agents_dynamiques/` ;
- prépare un documentaire écrit et audio ; le workflow de test peut aussi produire une vidéo MP4 narrée.

Les profils d'agents sont des configurations JSON : ils ne génèrent ni n'exécutent librement du code Python.

## Orchestrateur de missions IA (prototype contrôlé)
- `orchestrateur.py` permet de lancer une mission JSON avec jusqu'à trois rôles spécialisés : chercheur, critique et architecte.
- Chaque agent produit uniquement une analyse textuelle ; aucun code n'est exécuté, aucun compte externe n'est piloté et aucune publication n'est automatique.
- Les rapports sont enregistrés dans `.laboratoire_prive/missions/`, dossier ignoré par Git. Ils ne sont pas publiés sur le site.
- Les missions sont limitées à 180 secondes maximum, avec au moins 60 secondes prévues par agent ; les appels réseau ont leurs propres délais d'expiration.
- Cette première brique est un orchestrateur séquentiel borné, pas encore une équipe d'agents persistants ni un service de chat public.

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
- Limites anti-ralentissement : six sources maximum par article, deux agents spécialisés maximum, 30 articles conservés et délai réseau de 20 secondes.
- Priorités d'exécution : sécurité, tests et intégrité des données ; publication essentielle ; audio facultatif ; archives secondaires.
- Les résumés et audios IA peuvent contenir des erreurs : vérifier les sources originales. Une réponse IA mal formée ou sans référence valide est désormais refusée au lieu d'être transformée en faux article.
- Le thème Gaming adapte automatiquement sa requête avant et après le lancement de GTA VI, du 18 au 26 novembre 2026 (horodatages UTC).
- Respecter les conditions d'âge et d'utilisation des services ; demander l'aide d'un parent ou tuteur lorsque nécessaire.


## Architecture modulaire et continuité
Voir [docs/ARCHITECTURE_SECURITE.md](docs/ARCHITECTURE_SECURITE.md) pour les modules séparés, le basculement IA, les règles de compartimentation et le plan de reprise.

## Publication cloisonnée et hébergement de secours
Voir [docs/PLAN_PUBLICATION_SECOURS.md](docs/PLAN_PUBLICATION_SECOURS.md) : dépôt privé de préparation, assemblage contrôlé cinq minutes avant publication, et hébergement secondaire avec domaine personnalisé. Le secours sur la même adresse n'est pas encore activé.

## Vision d'autonomie IA
Voir [docs/PLAN_AUTONOMIE_IA.md](docs/PLAN_AUTONOMIE_IA.md) pour la cible : veille, rédaction, vérification, médias, publication, surveillance et reprise automatisées, avec des limites strictes de sécurité. Cette architecture complète n'est pas encore entièrement construite.


## Atelier R&D et produits commercialisables
Voir [docs/ATELIER_PRODUITS.md](docs/ATELIER_PRODUITS.md). Le module `atelier_produits.py` transforme une opportunité décrite et notée en fiche de décision locale. Son score est une présélection, pas une étude de marché ; aucune vente, publication ou exécution de code n'est automatique.


## Auto-évaluation et amélioration continue
Voir [docs/AUTO_AMELIORATION.md](docs/AUTO_AMELIORATION.md). `auto_amelioration.py` exécute des contrôles bornés et prépare un backlog priorisé. Un workflow quotidien conserve le rapport ; il ne modifie ni ne déploie automatiquement le code.

## File locale de missions IA
Voir [docs/FILE_MISSIONS.md](docs/FILE_MISSIONS.md). `gestionnaire_missions.py` ajoute une file SQLite persistante pour préparer, lister, annuler les missions en attente et exécuter la suivante. Les données restent dans `.laboratoire_prive/`, ignoré par Git. Un seul worker est autorisé ; une mission active n'est pas annulable en direct et reste limitée par l'orchestrateur à 180 secondes maximum.

## Atelier de création numérique multi-format

Voir [docs/ATELIER_CREATION_MULTI_FORMAT.md](docs/ATELIER_CREATION_MULTI_FORMAT.md). Le module `atelier_creation.py` prépare des squelettes de sites, applications web, jeux 2D navigateur, dossiers vidéo/audio et logiciels Python. Il ne produit pas encore des applications ou médias finis.

## Hébergement, anti-abus et stockage

Voir [docs/SECURITE_HEBERGEMENT_STOCKAGE.md](docs/SECURITE_HEBERGEMENT_STOCKAGE.md) pour les limites GitHub Pages, l'architecture nécessaire à une vraie limitation par IP et la mesure de stockage.

## Générateur de projets Roblox
Voir docs/GENERATEUR_ROBLOX.md. Le module studio_roblox.py génère un squelette Rojo de jeu obby avec scripts serveur/client et monnaie gérée côté serveur. Il ne se connecte pas à Roblox, n'exécute pas le code Luau et ne publie aucun jeu.
 
## Validation statique des projets Roblox
Voir docs/VALIDATEUR_ROBLOX.md. Le module validateur_roblox.py analyse les fichiers Luau et la configuration Rojo sans exécuter le code ; ses limites sont documentées.

## État d'avancement global
Voir docs/ETAT_AVANCEMENT_GLOBAL.md pour la grille pondérée, les preuves, les limites et les prochaines étapes. L'estimation actuelle est de 52,75 % selon cette grille, sans signifier que le produit complet est prêt pour la production.
