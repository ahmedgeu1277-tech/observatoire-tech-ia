# Validateur statique de projets Roblox

Le module validateur_roblox.py examine un dossier Roblox/Rojo sans exécuter les scripts Luau.

## Utilisation

python validateur_roblox.py .laboratoire_prive/prototypes/SafeObby

Le rapport vérifie les fichiers indispensables, la configuration Rojo, les chemins, certains appels dangereux connus et l'absence de modification de la monnaie côté client.

## Limites

Ce contrôle repose sur des motifs textuels. Il peut manquer une vulnérabilité, produire un faux positif et ne vérifie pas le comportement réel du jeu. Il ne remplace ni Luau Analysis, ni les tests de jeu dans Roblox Studio, ni une revue de sécurité humaine. Un rapport réussi ne signifie pas que le jeu est certifié sûr.
