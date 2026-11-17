# Atelier de création numérique multi-format

## Périmètre

L'atelier n'est pas limité à Roblox. Le générateur `atelier_creation.py` prépare six familles de prototypes :

| Type | Livrables de départ | Ce que cela ne fait pas encore |
|---|---|---|
| Site web | HTML, CSS, README | Hébergement, CMS, backend |
| Application web | HTML, CSS, JS | Comptes, base de données, API sécurisée |
| Jeu web 2D | Canvas, JavaScript | Moteur complet, assets, gameplay avancé |
| Vidéo | Concept, script, storyboard | Montage/rendu MP4 et droits des médias |
| Audio | Script et plan de mixage | Enregistrement, synthèse et mastering |
| Logiciel Python | Entrée et test smoke | Application complète et installateur |

Exemple :
```bash
python atelier_creation.py MonSite --type site
python atelier_creation.py MonJeu --type jeu-web
python atelier_creation.py MonVideo --type video
```

Les modèles sont des points de départ, pas des produits finis. Le générateur ne lance aucun code, n'accède à aucun compte externe et ne publie rien. Roblox reste un adaptateur spécifique via `studio_roblox.py`; d'autres moteurs (Godot, Unity, Unreal) nécessitent des intégrations, SDK, licences et tests dédiés.

## Architecture cible

1. **Orchestrateur** : transforme un brief en tâches bornées et affecte des rôles (produit, UX, code, médias, tests, sécurité).
2. **Adaptateurs de création** : web, mobile, jeux 2D/3D, vidéo, audio, logiciels et automatisations.
3. **Espace de travail isolé** : un dossier/branche par projet, quotas CPU/mémoire/stockage, aucune clé API dans le contexte du modèle.
4. **Boucle qualité** : tests unitaires, analyse statique, tests navigateur, tests de gameplay/médias adaptés, contrôle licences et validation humaine.
5. **Livraison** : artefact et rapport ; aucune publication ou action commerciale automatique.

## Sécurité de l'exécution

- Ne jamais exécuter directement du code généré ou téléchargé par un agent.
- Exécuter uniquement dans un bac à sable jetable, sans secrets, avec réseau sortant bloqué par défaut, utilisateur non privilégié, limites de temps, mémoire, CPU et taille de fichier.
- Valider les chemins, refuser les liens symboliques et empêcher les écritures hors du dossier de projet.
- Produire un diff, tester, scanner les dépendances et conserver un retour arrière.
- Ne jamais donner à un agent un jeton GitHub d'administration ou des identifiants personnels.
- Les actions externes (publication, paiement, suppression, messages, accès aux comptes) restent soumises à autorisation explicite.

## Limites actuelles

Le dépôt contient un générateur Roblox spécialisé et un atelier de démarrage multi-format. Il ne possède pas encore un moteur universel capable de créer automatiquement un jeu 3D complet, une vidéo finalisée, une application mobile native et de les déployer sur toutes les plateformes. Chaque format nécessite ses propres outils, environnements et tests.
