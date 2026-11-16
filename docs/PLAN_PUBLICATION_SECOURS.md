# Publication cloisonnée et hébergement de secours

## État actuel vérifié

- Le dépôt `ahmedgeu1277-tech/observatoire-tech-ia` est **public**.
- Le site est actuellement servi par GitHub Pages à l'adresse `https://ahmedgeu1277-tech.github.io/observatoire-tech-ia/`.
- Le workflow `robot.yml` génère les contenus puis les ajoute dans un seul commit Git. Le public voit donc la version une fois ce commit déployé, mais la préparation n'est pas privée.
- Aucun nom de domaine personnalisé ni second hébergeur n'est configuré dans le dépôt.

**Conséquence de sécurité :** ne pas déposer de brouillons confidentiels, de fichiers secrets ou de versions non publiées dans ce dépôt public. Les secrets API doivent rester dans GitHub Actions Secrets et ne jamais être copiés dans les artefacts ou les fichiers du site.

## Architecture cible

### 1. Zone privée de préparation
Un dépôt de préparation distinct, réglé en privé, conserve les brouillons et les fichiers de travail. Il ne contient aucun site public et ses Actions n'ont pas de permission de publication. Les accès sont limités au strict nécessaire.

### 2. Modules séparés
Les contenus sont produits par étapes indépendantes :
- collecte des sources ;
- rédaction ;
- audio/vidéo ;
- contrôle des liens et des droits ;
- analyse anti-fuite ;
- assemblage du site.

Chaque étape ne reçoit que les fichiers nécessaires. Les clés API restent dans les secrets du dépôt privé et ne sont jamais intégrées aux artefacts.

### 3. Fenêtre de publication de cinq minutes
- T-5 min : figer la version candidate et calculer son empreinte SHA-256.
- T-4 min : vérifier les fichiers attendus, les liens, les formats et les limites de taille.
- T-3 min : rechercher les secrets, données personnelles non destinées au public et fichiers interdits.
- T-2 min : tester le site assemblé et vérifier les pages essentielles.
- T-1 min : produire un manifeste de publication et bloquer toute modification de cette version.
- T : transférer l'ensemble validé en une seule version de publication. Si un contrôle échoue, ne rien publier et conserver la version publique précédente.

Cette fenêtre est une cible d'automatisation, pas une garantie absolue contre les fuites. La vérification automatique ne remplace pas une relecture humaine.

### 4. Hébergement de secours et même adresse
Un deuxième hébergeur statique indépendant, par exemple Cloudflare Pages, peut conserver une copie du site. Pour que les visiteurs utilisent **exactement la même adresse** si GitHub Pages tombe, il faut d'abord un nom de domaine personnalisé contrôlé indépendamment de GitHub, avec le DNS configuré pour basculer vers l'hébergeur de secours.

L'adresse actuelle en `github.io` appartient au domaine de GitHub : on ne peut pas la faire pointer vers un autre hébergeur. Sans domaine personnalisé, le secours aura nécessairement une autre adresse.

Le deuxième hébergeur n'est pas encore activé : cela nécessite un compte auprès du fournisseur, la configuration DNS du domaine et des identifiants de déploiement stockés comme secrets. Ne pas prétendre qu'un basculement automatique existe avant un test réel.

## Plan de mise en place, dans l'ordre

1. Créer un dépôt de préparation **privé** et vérifier qu'il est réellement privé.
2. Déplacer la génération des brouillons dans ce dépôt privé ; ne pas envoyer les artefacts de préparation vers le dépôt public.
3. Ajouter le pipeline T-5 avec tests, scan anti-fuite, manifeste SHA-256 et arrêt automatique en cas d'échec.
4. Ajouter un déploiement public en une seule version, avec permissions d'écriture uniquement dans le job de publication.
5. Configurer un hébergeur statique secondaire indépendant.
6. Acquérir/configurer un domaine personnalisé et son DNS ; sans cela, le même lien ne peut pas être garanti.
7. Simuler une panne de GitHub et vérifier que le domaine sert toujours la copie de secours.

## Limites importantes

- Le dépôt public actuel expose son code et son historique. Le passage en préparation privée ne rend pas rétroactivement privé ce qui a déjà été publié.
- Un déploiement atomique réduit le risque d'afficher un site partiellement mis à jour ; il n'empêche pas à lui seul une fuite de données.
- Une copie de secours hébergée chez un autre fournisseur protège l'accès au site, mais pas la génération si celle-ci dépend encore de GitHub Actions.
- Les offres gratuites, quotas et conditions d'âge des hébergeurs peuvent changer. Pour un compte nécessitant l'âge adulte, demander à un parent ou tuteur de gérer la création et la configuration.
