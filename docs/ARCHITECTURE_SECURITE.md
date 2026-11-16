# Architecture modulaire, sécurité et continuité

## Objectif
Aucun fournisseur externe ne doit être indispensable à toutes les fonctions. Une panne doit dégrader une fonction précise, pas faire tomber tout le site.

## Modules séparés
- `sources_specialisees.py` : collecte les flux spécialisés. Les erreurs d'un flux sont isolées.
- `main.py` : orchestre la veille et la publication ; ne stocke pas de clés.
- `ai_providers.py` : interface commune vers les modèles IA. L'ordre des fournisseurs se règle avec `AI_PROVIDER_ORDER` (par défaut `groq,huggingface`). Si Groq n'est pas configuré ou échoue, Hugging Face peut prendre le relais.
- `agent_gardien.py` : contrôle technique avant publication.
- `documentaire_test.py` et les workflows documentaires : tâche indépendante du cycle d'articles.
- `site/` : contenu public uniquement ; aucun secret ne doit y être placé.

## Pannes et reprise
- Google Actualités peut échouer sans empêcher l'utilisation des flux spécialisés.
- Un flux spécialisé en panne est ignoré ; les autres sont interrogés.
- Un fournisseur IA peut échouer ; le fournisseur suivant est essayé.
- Les analyses d'agents sont facultatives : leur échec ne doit pas bloquer l'article principal.
- Si toutes les sources ou tous les fournisseurs IA sont indisponibles, aucune publication inventée n'est créée : le job échoue clairement.
- GitHub Actions reste le moteur d'exécution actuel. Les tâches planifiées peuvent être retardées et ce dépôt n'est pas un serveur permanent.

## Compartimentation des secrets
- Les clés restent dans GitHub Actions Secrets, jamais dans le dépôt, les pages web, les articles ou les logs.
- Utiliser des clés différentes par fournisseur et par environnement ; révoquer immédiatement une clé exposée.
- Ne donner à chaque workflow que les secrets et permissions dont il a besoin.
- Le workflow de publication a besoin d'un accès d'écriture au dépôt pour publier. Les workflows de tests et de nettoyage devraient garder des permissions minimales.
- Ne jamais exécuter du code non vérifié provenant d'une source externe avec des secrets disponibles.
- Ne pas transmettre les clés API aux agents, aux prompts, aux contenus récupérés ou aux pages web.

## Limiter l'impact d'une compromission
- Le site public ne contient que des données destinées à être publiques.
- Les secrets ne sont pas enregistrés dans `site/` ni dans les archives.
- Limiter les données collectées et la durée de conservation.
- Garder des sauvegardes indépendantes du dépôt principal et tester la restauration.
- Examiner les journaux sans y inscrire de jetons, clés, prompts privés ou données personnelles.
- Protéger le compte GitHub avec une authentification forte et limiter les collaborateurs.
- Épingler les actions GitHub à des versions vérifiées (idéalement des SHA complets) et mettre à jour les dépendances de façon contrôlée.

## Limites connues à traiter
- Le dépôt et GitHub Pages sont encore des dépendances centrales pour le code et le site public. Cette architecture ne les rend pas indépendants.
- Les flux officiels disponibles varient selon le sujet ; une liste vide est possible.
- Le basculement Groq/Hugging Face est une redondance de fournisseur, pas une garantie de qualité identique ni de disponibilité gratuite.
- Une sauvegarde dans le même compte GitHub ne protège pas d'une compromission du compte. Prévoir une copie chiffrée indépendante.
- Le contrôle de secrets actuel est une première barrière, pas une certification de sécurité.

## Plan d'évolution
1. Ajouter des adaptateurs indépendants pour chaque catégorie de sources et chaque fournisseur IA.
2. Déplacer tests, génération et publication dans des jobs séparés avec permissions minimales.
3. Mettre les archives dans un stockage indépendant, chiffré et versionné, avec accès séparé.
4. Prévoir un second hébergement statique exportable pour le site si GitHub Pages est indisponible.
5. Ajouter des tests de panne simulée, de restauration et de fuite de secrets avant toute extension.
