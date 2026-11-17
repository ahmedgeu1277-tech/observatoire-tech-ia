# Générateur de projets Roblox — prototype

Le module studio_roblox.py crée un squelette de jeu de type obby au format de projet Rojo. Le but est de fournir une première « pioche numérique » : un outil qui prépare une base de projet réutilisable.

## Utilisation

python studio_roblox.py "Mon Obby" --output .laboratoire_prive/prototypes

Le dossier généré contient une configuration Rojo, des scripts Luau serveur/client et une configuration partagée. Les statistiques et pièces sont contrôlées côté serveur ; le client ne peut pas écrire directement dans la monnaie.

## Limites vérifiées

- Le générateur écrit des fichiers, mais n'exécute aucun code.
- Il ne se connecte pas à Roblox, ne pilote pas Roblox Studio et ne publie aucun jeu.
- Rojo et son plugin Roblox Studio sont requis pour synchroniser le dossier avec Studio.
- Le modèle ne crée pas automatiquement les plateformes du parcours : elles sont construites dans Studio.
- Le code doit être testé dans une expérience privée avant tout partage ou publication.

C'est un premier générateur déterministe, pas encore un créateur de jeux IA autonome. L'intégration de génération assistée, de tests de gameplay et de synchronisation contrôlée reste à développer.

Après génération, lancer le contrôle statique : python validateur_roblox.py .laboratoire_prive/prototypes/Mon_Obby. Ce contrôle est une première barrière, pas une certification.
