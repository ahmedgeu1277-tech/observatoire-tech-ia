# Auto-évaluation et amélioration continue

## Objectif
Les logiciels et agents du projet doivent être testés régulièrement comme par un utilisateur réel : démarrer, suivre des parcours, vérifier les résultats, repérer les blocages et prioriser les améliorations. Le système ne doit pas attendre une opinion à chaque cycle de diagnostic.

## Boucle actuelle
`auto_amelioration.py` lance trois contrôles allowlistés : tests unitaires, compilation Python et healthcheck. Il n'accepte aucune commande fournie par un modèle, n'utilise pas de shell et limite chaque contrôle à 180 secondes. Il produit un backlog priorisé et un rapport conservé comme artefact GitHub Actions pendant 14 jours.

## Extension prévue des parcours utilisateurs
Ajouter progressivement des tests Playwright sur les parcours du site : ouverture mobile, navigation entre pages, recherche, lecture audio, liens, accessibilité clavier, erreurs console, chargement lent et pages absentes. Les parcours doivent utiliser des données de test et ne jamais se connecter à un compte personnel réel.

## Auto-amélioration : niveaux
1. **Observer automatiquement** : erreurs, temps de chargement, échecs de tests, liens cassés et accessibilité.
2. **Diagnostiquer** : reproduire le problème et proposer une correction avec preuve.
3. **Corriger en zone isolée** : branche ou environnement de test sans secrets ni accès de production.
4. **Valider** : tests unitaires, tests de parcours, sécurité, revue des dépendances et comparaison avant/après.
5. **Déployer prudemment** : uniquement après validation des contrôles et règles de protection du dépôt. Les changements touchant sécurité, confidentialité, coûts, droits, paiements ou données privées exigent une validation humaine.

L'utilisateur n'a pas à donner son avis sur chaque contrôle ou diagnostic. Les décisions irréversibles, les dépenses, l'accès à des données privées, les publications et les changements sensibles restent protégés.

## Limites actuelles
Le module actuel automatise l'évaluation et la création d'un backlog ; il ne réécrit pas le logiciel. Le workflow s'exécute une fois par jour ou manuellement, pas en permanence. Le test d'interface Playwright existant doit encore être étendu à des parcours complets et au format mobile.
