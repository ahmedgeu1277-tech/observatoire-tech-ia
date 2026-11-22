# NEXORA — Tech, IA & Gaming

Média indépendant consacré à l'actualité de la technologie, de l'intelligence artificielle et du gaming.

## Site public

https://ahmedgeu1277-tech.github.io/observatoire-tech-ia/

Le site présente des articles et des documentaires issus de sources publiques. Les contenus générés avec l'aide de l'IA peuvent comporter des erreurs : consultez les sources originales avant de prendre une décision.

## Fonctionnalités actuellement présentes

- Collecte planifiée de sources publiques et génération d'articles assistée par IA.
- Narration audio lorsque le fournisseur vocal est disponible.
- Génération de documentaires vidéo à partir de contenus éditoriaux.
- Démonstration publique d'une ville fictive : quatre quartiers, vue WebGL 3D légère avec repli isométrique 2D, et indicateurs synthétiques sans exposition des données internes.
- Application web installable (PWA) : pages essentielles et catalogue d'articles mis en cache pour consultation hors ligne après une première visite. Les gros fichiers audio/vidéo ne sont volontairement pas mis en cache afin de préserver le stockage des téléphones et tablettes.
- Recherche textuelle et filtres par thème sur les articles ; six défis éducatifs avec progression et rang personnel enregistrés localement (sans classement mondial).
- Tableau de bord privé local avec file de missions, portefeuille R&D et feuille de route persistante de sept chantiers avec priorités, statuts et échéances modifiables, conservée hors du dépôt public.
- Générateur local de squelettes de projets : site, application web, jeu navigateur, vidéo, audio, logiciel Python et projets Godot 2D/3D. Il crée des fichiers de départ sans exécuter le code ni publier les projets.
- Archivage des publications récentes et nettoyage programmé des anciennes archives.
- File locale de missions IA avec trois rôles spécialisés maximum, durée limitée, annulation coopérative, relance manuelle plafonnée à trois tentatives et exécution manuelle de lots de trois missions maximum.
- Tests automatisés, contrôles de qualité/sécurité et surveillance du site réellement publié dans GitHub Actions.

Les tâches GitHub Actions sont ponctuelles et planifiées : elles ne constituent pas un serveur permanent 24 h/24.

## Langues

Le sélecteur de la page d'accueil propose sept langues pour l'interface : français, anglais, espagnol, allemand, portugais, arabe et chinois. La langue du navigateur est détectée au premier accès, puis le choix est mémorisé ; l'arabe active l'affichage de droite à gauche. Les articles conservent leur langue de publication. La page documentaire propose des variantes traduites (texte, narration, vidéo et sous-titres) en six langues supplémentaires lorsque leur génération a réussi. Les noms et liens des sources restent dans leur langue d'origine. Cette fonction ne traduit pas automatiquement chaque article ni toutes les pages.

## Ce qui n'est pas encore disponible

- Un service privé hébergé avec authentification et stockage persistant.
- Des agents indépendants fonctionnant en continu ou des missions autonomes de plusieurs jours.
- Une plateforme complète de création logicielle/vidéo utilisable depuis mobile et PC ; les modèles Godot sont des squelettes de départ, pas un éditeur de jeu intégré.
- Une supervision permanente garantissant la disponibilité des fournisseurs IA.

Les prototypes et outils du dépôt ne doivent pas être présentés comme des services finalisés.

## Sécurité et confidentialité

**Ce dépôt GitHub est public.** Tout fichier suivi par Git, y compris le code et la documentation, peut être consulté et copié par le public. Ne placez ici aucune clé API, donnée personnelle, découverte confidentielle, note privée ou prototype qui doit rester secret.

Les secrets de fournisseurs doivent être configurés dans les paramètres GitHub Actions, jamais dans le code. Le dossier local `.laboratoire_prive/` est ignoré par Git, mais cette règle ne rend pas confidentiels les fichiers déjà suivis ni leur historique.

Le site GitHub Pages est public et ne convient pas au stockage de données privées. Une suppression dans le dernier commit ne retire pas automatiquement les anciennes versions de l'historique Git.

Aucune intégration Discord n'est utilisée.

## Développement et vérification

Les workflows de contrôle sont définis dans `.github/workflows/`. Les résultats récents sont consultables dans l'onglet Actions du dépôt.

Consultez [l'état d'avancement détaillé](docs/ETAT_AVANCEMENT_GLOBAL.md) pour les limites connues et les tâches restantes. Le pourcentage d'avancement est une estimation, pas une certification de mise en production.
