# Worker de missions et protections du laboratoire

## Lancer un lot de missions

Le worker lit la file SQLite privée, exécute les missions en attente et surveille les nouvelles missions pendant le délai d'inactivité :

```bash
python gestionnaire_missions.py worker --max-runtime-seconds 3600 --max-missions 50 --idle-timeout-seconds 300
```

- Durée totale : 60 secondes à 48 heures maximum ; la valeur par défaut est une heure.
- Missions traitées par lancement : 1 à 50 maximum.
- Après une file vide, le worker attend jusqu'à cinq minutes par défaut et vérifie la file toutes les cinq secondes.
- `Ctrl+C` ou `SIGTERM` demande un arrêt coopératif : l'agent en cours termine son étape, puis le worker s'arrête.
- Chaque mission reste limitée à 180 secondes et trois agents maximum.
- Une seule mission peut être exécutée à la fois par base SQLite. Les missions interrompues sont récupérées après expiration du délai de sécurité.

Le worker est un processus, pas un hébergement. Il ne continue pas lorsque l'ordinateur ou le processus s'arrête. Pour fonctionner longtemps, une machine doit rester allumée, connectée et disposer des dépendances ainsi que d'un fournisseur IA disponible. GitHub Actions n'est pas un serveur permanent.

## Sécurité et confidentialité

- Le dépôt GitHub est public : ne jamais y enregistrer de mot de passe, clé API, donnée personnelle, idée confidentielle ou rapport privé.
- `.laboratoire_prive/` est ignoré par Git. Le contrôle de l'arbre Git du 19 novembre 2026 n'a trouvé aucun fichier suivi dans ce dossier ; l'historique Git public reste toutefois public.
- Sur les systèmes POSIX, le worker limite les permissions du dossier de file à `0700`, de la base SQLite à `0600`, du dossier des rapports à `0700` et des rapports à `0600`. Windows utilise ses ACL système et n'applique pas ces modes POSIX.
- Les missions ne peuvent pas exécuter du code généré, effectuer des actions externes ou publier automatiquement. Les résultats nécessitent une revue humaine.
- Les missions et contextes contenant un secret potentiel sont refusés avant stockage et envoi au fournisseur IA. Ne placez malgré tout aucun secret dans le texte d'une mission ou dans son contexte. Les permissions locales ne remplacent ni le chiffrement du disque ni la protection du compte et de l'appareil.
- Si un secret est publié par erreur, révoquez-le et remplacez-le auprès du fournisseur ; supprimer le fichier du dernier commit ne suffit pas à l'effacer de l'historique Git.
