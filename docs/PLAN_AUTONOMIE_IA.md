# Plan d'autonomie IA — Observatoire Tech & Gaming

## Vision

Construire un média numérique exploité automatiquement par des logiciels et des agents IA, sans équipe humaine nécessaire pour les opérations quotidiennes ordinaires. L'autonomie signifie que les tâches répétitives sont exécutées par des workflows contrôlés ; elle ne signifie pas que l'IA peut agir sans limites ni responsabilité.

## Ce que le système pourra automatiser

1. **Veille** : interroger des flux RSS et des sources spécialisées autorisées.
2. **Tri** : dédoublonner les sujets, classer les thèmes et écarter les sources trop faibles.
3. **Rédaction** : produire des synthèses en français avec les liens vers les sources.
4. **Contrôle** : vérifier le format, les liens, les champs obligatoires, les doublons et les règles de sécurité.
5. **Médias** : préparer une narration audio ; la vidéo MP4 reste une fonction à développer et tester séparément.
6. **Publication** : publier uniquement après réussite des contrôles automatiques.
7. **Surveillance** : conserver les journaux techniques, détecter les échecs et envoyer des alertes.
8. **Reprise** : réessayer les tâches temporaires, utiliser un fournisseur IA de secours et conserver la dernière version valide du site.

## Architecture modulaire cible

- **Orchestrateur** : déclenche les missions et coordonne les étapes.
- **Agents de veille** : un module par domaine (IA, jeux vidéo, Roblox, matériel, cybersécurité).
- **Agent rédacteur** : transforme les informations sourcées en article.
- **Agent vérificateur** : contrôle les citations, les liens, les dates et les affirmations.
- **Agent média** : prépare audio, images autorisées et, plus tard, vidéos.
- **Agent publication** : assemble le site et déploie les fichiers validés.
- **Agent gardien** : bloque les secrets détectés, les fichiers inattendus et les publications non conformes.
- **Agent de santé** : suit les erreurs, quotas, temps d'exécution et disponibilité.

Les agents sont des programmes spécialisés avec des permissions limitées. Ils ne doivent pas recevoir un accès général à tous les comptes ou secrets.

## Règles impératives

- Aucune clé API, aucun mot de passe et aucune donnée personnelle dans le dépôt public, les articles ou les journaux.
- Les clés restent dans les secrets du fournisseur d'hébergement.
- Les contenus générés doivent afficher qu'ils sont assistés par IA et relier les sources originales.
- Ne pas inventer de faits, de citations, de tests ou de témoignages.
- Une erreur de génération ne doit jamais écraser la dernière publication valide.
- Limiter le nombre de requêtes, les coûts, la durée d'exécution et les tentatives.
- Ne pas publier automatiquement les sujets sensibles, accusations, conseils médicaux/juridiques/financiers ou contenus potentiellement dangereux sans validation responsable.
- Ne jamais créer de comptes, acheter un service, accepter un contrat, contacter des personnes ou modifier des paramètres sensibles sans autorisation humaine explicite.
- Prévoir un bouton ou une procédure d'arrêt d'urgence et une possibilité de retour à la dernière version stable.

## Publication en plusieurs étapes

1. Préparer les articles et médias dans un espace privé distinct.
2. Exécuter les tests et contrôles sur les fichiers préparés.
3. Cinq minutes avant la fenêtre prévue, lancer une vérification finale et assembler un paquet de publication.
4. Si tous les contrôles passent, publier le paquet en une seule version cohérente.
5. Si un contrôle échoue, annuler cette publication et conserver la version précédente.

Le délai de cinq minutes est une cible d'orchestration, pas une garantie : les plateformes peuvent retarder ou interrompre les tâches planifiées.

## Continuité d'hébergement

- GitHub Pages reste l'hébergement principal actuel.
- Un hébergement secondaire devra être préparé et testé séparément.
- Sans nom de domaine personnalisé, l'adresse de secours sera différente de l'adresse GitHub Pages.
- Un domaine personnalisé pourra plus tard pointer vers une couche de distribution indépendante, configurée pour servir le site depuis l'hébergement disponible.
- Le dépôt public actuel ne devient pas privé par la simple création de ce document. Les brouillons confidentiels et fichiers de préparation devront être déplacés dans un dépôt privé distinct.

## État réel au 16 novembre 2026

Déjà présent dans le projet : génération d'articles par IA, bascule Groq/Hugging Face pour les articles et les tâches hebdomadaires, récupération de flux, profils JSON d'agents spécialisés, fenêtre de priorité événementielle (GTA VI), validation stricte du JSON et des sources avant publication, protection contre l'écrasement d'archives JSON corrompues, tests automatiques, filtre de secrets de premier niveau et publication planifiée. Le documentaire hebdomadaire prépare cinq chapitres écrits et des pistes audio séparées ; il ne produit pas de MP4.

Première brique ajoutée : un orchestrateur séquentiel de missions (orchestrateur.py), limité à trois rôles, avec durée bornée, délais réseau, rapports locaux ignorés par Git et aucune exécution de code ni publication automatique. Tests unitaires dédiés.\n\nPas encore réalisé : agents autonomes indépendants qui se contrôlent entre eux, exécution de missions de longue durée (plusieurs heures/jours), chat public connecté à un backend sécurisé, validation factuelle robuste, espace privé de préparation hébergé, assemblage atomique cinq minutes avant publication, hébergement secondaire actif, bascule automatique entre hébergeurs, supervision 24 h/24, génération vidéo MP4 et fusion automatique des pistes audio en un seul fichier.

GitHub Actions n'est pas un serveur permanent : les tâches planifiées peuvent être retardées et les exécutions ont une durée limitée. Le projet ne doit donc pas promettre une disponibilité continue avant d'avoir un hébergement et une supervision adaptés.

## Principe de fonctionnement

**Autonomie maximale pour les tâches ordinaires ; limites strictes pour la sécurité, les coûts, les données et les décisions engageant une personne.** Une personne responsable doit pouvoir surveiller le service, intervenir et l'arrêter.

## Échéance de lancement GTA VI — Thaïlande

Rockstar indique que GTA VI sort à minuit, heure locale, le 19 novembre 2026 sur PS5 et Xbox Series X|S. En Thaïlande (UTC+7), cela correspond à 00 h 00 le jeudi 19 novembre. L'heure locale thaïlandaise est donc le repère de lancement ; la conversion est à revalider sur le compte/store régional avant le jour J.

**Objectif de déploiement : mercredi 18 novembre 2026 à 12 h 00 en Thaïlande (ICT, UTC+7), soit mercredi 18 novembre à 06 h 00 en France métropolitaine (CET).** Cela représente 12 heures avant le lancement thaïlandais visé.

### Priorités avant cette échéance
1. Faire passer les tests Python et vérifier les dernières exécutions GitHub Actions.
2. Vérifier que le site public charge les articles et que les liens fonctionnent sur téléphone.
3. Générer et contrôler au moins un article et un documentaire audio de test ; la vidéo MP4 est une priorité ultérieure si elle ne peut pas être fiabilisée à temps.
4. Vérifier les secrets sans jamais afficher leurs valeurs, les permissions et les journaux.
5. Préparer une copie de secours du site sur un hébergeur secondaire si le compte et la configuration sont disponibles.
6. Déployer une version stable avant l'heure cible, puis surveiller les erreurs.

Cette date est un objectif de projet, pas une garantie de livraison de toutes les fonctions ambitieuses. En cas de défaut, privilégier un site stable plutôt qu'activer des fonctions non testées. Le secours sur la même adresse nécessite un domaine personnalisé ; sans domaine, l'adresse de secours sera différente.
