# Observatoire Tech & IA

Site éditorial consacré à l'actualité publique de la technologie, de l'intelligence artificielle et du jeu vidéo.

## Site public

https://ahmedgeu1277-tech.github.io/observatoire-tech-ia/

Le site présente des articles et des documentaires issus de sources publiques. Les contenus générés avec l'aide de l'IA peuvent comporter des erreurs : consultez les sources originales avant de prendre une décision.

## Fonctionnalités actuellement présentes

- Collecte planifiée de sources publiques et génération d'articles assistée par IA.
- Narration audio lorsque le fournisseur vocal est disponible.
- Génération de documentaires vidéo à partir de contenus éditoriaux.
- Archivage des publications récentes et nettoyage programmé des anciennes archives.
- Tests automatisés et contrôles de qualité/sécurité dans GitHub Actions.

Les tâches GitHub Actions sont ponctuelles et planifiées : elles ne constituent pas un serveur permanent 24 h/24.

## Langues

Le site et la chaîne éditoriale sont actuellement principalement en français. Une interface multilingue complète et des traductions vérifiées ne sont pas encore disponibles. Ne considérez pas les autres langues comme prises en charge tant qu'elles ne sont pas proposées explicitement sur le site.

## Ce qui n'est pas encore disponible

- Un service privé hébergé avec authentification et stockage persistant.
- Des agents indépendants fonctionnant en continu ou des missions autonomes de plusieurs jours.
- Une connexion directe à Roblox Studio, des tests de gameplay automatisés ou la publication automatique de jeux.
- Une plateforme complète de création logicielle/vidéo utilisable depuis mobile et PC.
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
