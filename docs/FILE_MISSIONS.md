# File de missions locale

Le module `gestionnaire_missions.py` ajoute une file persistante SQLite à l'orchestrateur.

## Utilisation

- Ajouter une mission : `python gestionnaire_missions.py add mission.json` (champs facultatifs `priority`: `low`, `normal`, `high`, `critical` ; `due_at`: date ISO 8601 avec fuseau horaire).
- Lister : `python gestionnaire_missions.py list`
- Consulter le détail d'une mission : `python gestionnaire_missions.py show ID` (charge utile, état, dates, résultat ou type d'erreur).
- Exécuter la prochaine : `python gestionnaire_missions.py run-next`
- Annuler une mission encore en attente : `python gestionnaire_missions.py cancel ID`

Le fichier SQLite et les rapports restent dans `.laboratoire_prive/`, ignoré par Git. La commande `show` ne renvoie que la mission demandée et ne rend pas la file accessible depuis le site public. Le contenu de mission est validé par `orchestrateur.valider_mission` : trois rôles maximum, durée totale plafonnée à 180 secondes, texte limité et aucun programme ou commande arbitraire.

## Limites

- Un seul worker doit utiliser la file à la fois.
- Une mission en cours n'est pas interrompue par `cancel` ; cette commande annule uniquement les missions en attente.
- Si le processus s'arrête brutalement, une mission peut rester marquée `running`. Au redémarrage, appeler `recover_interrupted()` pour la marquer `interrupted`, puis examiner le rapport avant de la relancer.
- Les agents ne font que produire des analyses textuelles. Pas d'exécution de code généré, d'accès aux comptes, de dépense, de vente ou de publication.
- La file locale n'est pas un service web, ni un agent actif en permanence. GitHub Actions n'est pas un serveur permanent.

Cette brique apporte une file durable et des états de mission ; elle ne constitue pas encore une autonomie de plusieurs heures ou jours.
