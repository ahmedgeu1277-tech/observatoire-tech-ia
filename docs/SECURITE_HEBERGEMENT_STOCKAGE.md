# Hébergement, limitation de trafic et sécurité opérationnelle

## État réel aujourd'hui

Le site est publié sur GitHub Pages depuis un dépôt public. Il s'agit d'un site statique : les pages HTML/JS ne constituent pas un serveur et ne peuvent pas imposer une limite fiable par adresse IP. Une limite codée uniquement en JavaScript serait contournable et ne protégerait pas l'hébergement contre une saturation.

GitHub indique des limites d'usage pour Pages, notamment une taille publiée maximale de 1 Go et une limite de bande passante souple de 100 Go/mois. GitHub peut appliquer ses propres réponses HTTP 429, mais le projet ne contrôle pas un quota individuel par IP. Voir la documentation officielle : https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits.

## Architecture nécessaire pour une vraie limite IP

Pour appliquer une politique par IP, il faut placer le site derrière un CDN/WAF ou un proxy edge que le propriétaire contrôle, puis faire passer le trafic par ce proxy. Une solution possible est Cloudflare avec un domaine dont les DNS sont contrôlés par le propriétaire :

1. connecter et vérifier le domaine ;
2. faire pointer le DNS vers le CDN/proxy et activer le proxy ;
3. créer des règles WAF / rate limiting adaptées aux routes sensibles ;
4. configurer des limites distinctes pour les pages statiques et les API (ne pas pénaliser tous les visiteurs derrière un NAT) ;
5. appliquer des réponses 429, une fenêtre de refroidissement et des journaux sans données personnelles inutiles ;
6. tester depuis plusieurs clients et vérifier que l'origine ne peut pas être contournée.

Cloudflare documente ses limites de plateforme Pages ici : https://developers.cloudflare.com/pages/platform/limits/. Les règles de limitation doivent être configurées dans le compte et sur le domaine ; aucune règle n'est active dans ce dépôt. Le compte, le domaine et les changements DNS ne peuvent pas être créés ni activés par ce code.

## Mesures déjà présentes ou à confirmer

- Tests automatiques et analyse de code : workflows GitHub Actions.
- Scan de secrets : Gitleaks.
- Analyse de code : CodeQL, Ruff et Bandit.
- Tests navigateur : Playwright.
- Données privées locales : dossier `.laboratoire_prive/` ignoré par Git.
- Site public : ne doit contenir aucun secret, donnée privée, jeton ou prototype confidentiel.

Les workflows de qualité doivent échouer si Ruff ou Bandit détectent des problèmes ; ne pas utiliser `continue-on-error: true` pour masquer un résultat rouge.

## Contrôles encore nécessaires avant une mise en production exposée

- Activer une authentification multifacteur sur le compte GitHub et vérifier les méthodes de récupération.
- Activer la protection de branche et exiger les contrôles requis.
- Épingler les actions tierces sur des SHA vérifiés et réviser les mises à jour.
- Ajouter des sauvegardes chiffrées indépendantes et tester une restauration.
- Déployer le CDN/WAF et valider les règles de limitation IP.
- Héberger tout backend derrière authentification, autorisation par rôle, validation d'entrée, CSRF/CORS appropriés, limites de taille et quotas.
- Ajouter tests de charge autorisés, tests de restauration, alertes et procédures d'incident.
- Réaliser une revue indépendante avant d'y stocker des données personnelles ou d'ouvrir un service public.

Aucune architecture ne garantit l'absence de bug ou l'impossibilité d'un piratage. L'objectif est de réduire la surface d'attaque, détecter les incidents et limiter leur impact.

## Stockage mesuré le 17 novembre 2026

Mesure calculée à partir de l'arbre GitHub de la branche `main` :

- 105 fichiers suivis.
- 10 572 927 octets de fichiers suivis, soit environ 10,08 Mio.
- Le dossier public `site/` représente environ 9,78 Mio.
- L'API GitHub indique `size = 13 409` Ko pour le dépôt (environ 13,1 Mio, mesure GitHub du dépôt, différente de la somme des fichiers).
- Ces chiffres ne comprennent pas un stockage futur pour les projets générés localement, les caches, les artefacts Actions, ni des médias créés plus tard.
- Le dossier privé local `.laboratoire_prive/` n'est pas dans Git et sa taille ne peut pas être déduite du dépôt.

Ne pas utiliser GitHub comme disque dur pour les vidéos brutes, les modèles IA ou les gros binaires. Stocker les médias lourds dans un stockage objet séparé avec quotas, politique de rétention et sauvegardes.
