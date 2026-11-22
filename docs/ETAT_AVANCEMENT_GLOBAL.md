# État d'avancement global du projet

Dernière évaluation fonctionnelle détaillée : 22 novembre 2026. Audits précédents : 18 et 19 novembre 2026.

## Audit complémentaire du 19 novembre 2026

- Le dépôt GitHub est toujours **public** : tous les fichiers suivis et leur historique sont consultables. Le dossier ignoré `.laboratoire_prive/` ne protège pas les fichiers déjà commités. Aucun élément confidentiel ne doit y être ajouté.
- Sur le commit `cba0adfa` du 19 novembre 2026, les workflows de tests automatiques, d'analyse avancée et de publication GitHub Pages ont terminé avec succès. Les 109 tests Python ont réussi. Ruff, Bandit et Gitleaks ont réussi ; CodeQL Python et JavaScript a terminé sans échec ; Playwright a vérifié toutes les pages HTML, les parcours responsive et le changement des sept langues, y compris le sens RTL de l'arabe et la mémorisation du choix. Cela confirme ces exécutions précises, pas la disponibilité permanente de tous les services.
- L'interface de la page d'accueil propose sept langues : français, anglais, espagnol, allemand, portugais, arabe et chinois. Le choix est mémorisé dans le navigateur et l'arabe utilise désormais l'affichage de droite à gauche. Les articles et documentaires ne sont pas automatiquement traduits : leur langue d'origine est conservée.
- Le workflow de publication a réussi sur ce commit et a publié un article. La publication a été rendue plus résistante aux changements concurrents de la branche Git. Une réponse IA rejetée par les contrôles factuels déclenche une seule tentative sur un sujet général ; les contrôles ne sont jamais désactivés.
- Le dernier contrôle réel des fournisseurs a confirmé Groq fonctionnel et Hugging Face bloqué par une demande de crédits prépayés. Le workflow utilise donc Groq par défaut ; Hugging Face reste une option explicite, mais n'est pas garanti gratuit.
- La configuration des fournisseurs refuse désormais les noms inconnus ou une liste vide. Les appels de chaque agent reçoivent un délai plafonné par le temps restant de la mission. Des tests couvrent ces validations et les limites de paramètres.


## Correctifs supplémentaires du 19 novembre 2026

- Le diagnostic de dépôt valide les structures JSON, les champs des articles, les identifiants uniques, les liens HTTPS sans identifiants intégrés, les fichiers audio présents et confinés au dossier public audio, ainsi que l'absence de données de ville dans le site public. Dernière mesure de publication observée : 30 articles, 88 liens de source, 29 fichiers audio et cinq profils d'agents configurés (non exécutés en continu).
- La file SQLite ferme désormais ses connexions dans un gestionnaire de contexte unique. L'ajout d'une mission verrouille la transaction avant de compter les missions en attente, afin d'éviter de dépasser la limite de 50 en cas d'ajouts simultanés. Les tests vérifient la fermeture des connexions et le plafond.
- Le mécanisme de publication supporte désormais l'indisponibilité du fournisseur IA ou un quota atteint : après une nouvelle tentative sur un sujet général, le système peut publier un résumé documentaire neutre, limité aux liens HTTPS valides. Il ne confirme aucune annonce, date, prix ou caractéristique et ne contourne jamais les contrôles factuels. Un cycle réel GitHub Actions du 19 novembre a réussi avec ce mode de secours lorsque Groq a renvoyé une limitation de quota.
- La suite de tests Python a ensuite atteint **122 tests réussis** sur le commit `ee75a873` (19 novembre 2026). Sur ce même commit, l'analyse avancée a terminé avec succès : Playwright, parcours mobile/tablette/ordinateur, vérification des sept langues et du RTL arabe, Ruff, Bandit, Gitleaks et CodeQL Python/JavaScript. Le workflow de publication a également réussi. Le déploiement Pages correspondant à ce commit a été annulé au profit d'une publication plus récente ; le déploiement de cette publication plus récente doit être vérifié séparément.
- Ces améliorations renforcent la fiabilité des tâches ponctuelles ; elles ne transforment pas GitHub Actions en serveur permanent et ne réalisent pas encore les missions autonomes de plusieurs heures ou jours.

## Résultat

**Estimation pondérée recalculée : 65,70 / 100 (audit du 22 novembre 2026, code vérifié jusqu'au commit 386e5373).**

Ce pourcentage est un indicateur d'avancement fonctionnel construit à partir des domaines ci-dessous. Ce n'est ni un pourcentage de lignes de code terminées, ni une garantie de disponibilité, ni une certification de mise en production. Les notes sont des estimations prudentes fondées sur les fonctions présentes et les contrôles exécutés. Le précédent score de 56,48 % est conservé dans les bilans historiques plus haut.

| Domaine | Poids | Avancement estimé | Contribution |
|---|---:|---:|---:|
| Média, veille et site public | 23,53 % | 91 % | 21,41 |
| Fournisseurs IA et orchestration d'agents | 17,65 % | 40 % | 7,06 |
| Missions persistantes et autonomie | 17,65 % | 46 % | 8,12 |
| Laboratoire privé et sécurité | 17,65 % | 63 % | 11,12 |
| R&D et conception de produits | 11,76 % | 54 % | 6,35 |
| Tests et amélioration continue | 11,76 % | 99 % | 11,64 |
| **Total** | **100 %** |  | **65,70 %** |

Calcul : somme de (poids × note du domaine) / 100.

## Justification des notes

### Média, veille et site public — 91 %
Le site public, la récupération de sources, la rédaction assistée, les articles, les fichiers audio et les workflows planifiés existent. Un premier documentaire de démonstration a été généré et publié en MP4 H.264/AAC avec narration, diapositives 1280×720 dessinées localement et références aux sources. Le rendu a été vérifié par FFmpeg et le workflow complet a réussi. Cette vidéo reste un documentaire temporaire de test, pas un studio de montage universel. Restent notamment un hébergement secondaire réellement actif, une supervision permanente et une validation factuelle plus forte.

### Fournisseurs IA et orchestration d'agents — 40 %
Le projet possède une couche de fournisseurs IA, un basculement, cinq profils spécialisés et un orchestrateur séquentiel avec trois rôles. Les profils ne sont pas des agents indépendants qui travaillent en continu. Un test réel du 19 novembre a réussi avec Groq. Hugging Face a refusé la génération faute de crédits prépayés ; il ne doit donc pas être considéré comme un secours gratuit disponible.

### Missions persistantes et autonomie — 35 %
Une file SQLite locale conserve les missions et leurs états ; un worker peut lancer la mission suivante. L'orchestrateur limite actuellement une mission à 180 secondes et trois rôles maximum. Une mission en attente peut être annulée immédiatement ; une mission active reçoit un signal d'annulation et s'arrête entre deux appels IA. Un appel déjà lancé peut néanmoins aller jusqu'à son délai maximal (60 secondes). Les missions restées actives depuis plus de cinq minutes sont classées comme interrompues avant le lancement suivant. L'arrêt instantané d'un appel en cours, les missions de plusieurs heures ou deux jours et le fonctionnement permanent ne sont pas encore réalisés.

### Laboratoire privé et sécurité — 45 %
Le dossier local du laboratoire est ignoré par Git, les contrôles Gitleaks, CodeQL, Bandit et Ruff sont présents, et un contrôles statiques complémentaires ont été ajoutés. Il n'existe pas encore de tableau de bord privé hébergé avec authentification et autorisations côté serveur. GitHub Pages reste public.

### R&D et conception de produits — 54 %
L'atelier de sélection de produits note les opportunités selon la douleur client, les preuves de demande, la faisabilité, la différenciation, le coût et l'accès au marché. Des prototypes commencent à exister, mais les entretiens clients, les preuves de marché indépendantes, les tests avec de vrais utilisateurs et la validation économique restent à faire.

### Tests et amélioration continue — 99 %
La suite compte maintenant 112 tests Python réussis sur le commit `e34f646a` le 19 novembre, après ajout des tests de migration SQLite et d'annulation coopérative des missions. Le dernier workflow avancé a réussi : Ruff, Bandit, Gitleaks, CodeQL Python et JavaScript, ainsi que les tests Playwright des trois pages et les parcours responsive de l'accueil et du documentaire à 390, 768 et 1 440 px. Le diagnostic du dépôt a vérifié 25 articles, 85 sources et 24 fichiers audio, cinq profils d'agents et l'absence de données de ville dans le site public. La boucle d'auto-évaluation produit un rapport et un backlog ; elle ne réécrit pas le code de production et ne déploie pas de corrections de façon autonome.

## Périmètre de développement

Le développement de jeux et les intégrations associées ne font plus partie des objectifs actifs. Les anciens fichiers expérimentaux éventuels ne sont pas considérés comme des fonctionnalités maintenues ni inclus dans le calcul d'avancement.

## Conditions pour augmenter le score

1. Vérifier plusieurs cycles réels Groq et Hugging Face sans exposer les clés.
2. Ajouter un tableau de bord local des missions avec arrêt fiable et reprise après interruption.
3. Construire une interface privée avec authentification réelle sur un backend séparé du site public.
4. Renforcer la génération vidéo éditoriale, la validation factuelle et la fiabilité de publication.
5. Tester les prototypes avec des utilisateurs et collecter des preuves de demande.
6. Permettre aux agents de proposer des corrections dans des branches isolées, puis exiger tests, revue et retour arrière avant toute fusion.

## Limites importantes

- 56,48 % est une estimation pondérée selon cette grille ; cela ne signifie pas que toutes les fonctionnalités sont prêtes à être utilisées.
- Aucun travail ne continue en arrière-plan après la fin d'une exécution GitHub Actions, sauf les workflows effectivement planifiés.
- Aucune vente, dépense ou publication externe n'est automatique.
- Les rapports et prototypes privés ne doivent pas être ajoutés au site public.


## Trois chantiers poursuivis le 19 novembre 2026

- **Multilingue :** l'accueil traduit désormais aussi les libellés des cartes d'articles (verdict, conseil, sources, contenu IA), les états de chargement/erreur et le lien documentaire en français, anglais, espagnol, allemand, portugais, arabe et chinois. Une note indique explicitement que les articles et leurs sources restent dans leur langue d'origine ; aucune traduction automatique intégrale des articles n'est revendiquée.
- **Coopération et autonomie bornée :** les agents suivants reçoivent les analyses précédentes, avec un plafond de 3 000 caractères par agent et 8 000 caractères au total. Un worker de file peut surveiller les nouvelles missions, avec durée maximale configurable de 48 heures (défaut : 1 heure), 50 missions maximum, attente après file vide limitée (défaut : 5 minutes), et arrêt coopératif par signal. Chaque mission reste plafonnée à 180 secondes et trois agents. Le processus doit rester actif sur une machine disponible ; ce n'est pas un service permanent hébergé.
- **Sécurité :** les missions contenant un secret potentiel sont refusées avant stockage et envoi au fournisseur IA. Sur POSIX, le dossier SQLite et les rapports privés reçoivent des permissions restrictives (0700 pour les dossiers, 0600 pour les fichiers). L'arbre Git courant a été contrôlé : aucun fichier n'est suivi sous `.laboratoire_prive/`. Le dépôt et son historique restent publics.
- Vérification du 19 novembre 2026 : **131 tests Python réussis** sur le commit `2fa1266b`. Ruff, Bandit, Gitleaks, CodeQL Python et JavaScript, et les tests Playwright ont tous réussi. Playwright a vérifié les libellés dynamiques allemands et arabes, le RTL arabe, les deux pages et les trois largeurs d'écran. Le workflow de publication a réussi ; le déploiement GitHub Pages a ensuite réussi sur le commit `064b2ac6` (publication automatique suivante).


## Audit opérationnel du 22 novembre 2026

- Sur le commit de code vérifié `300f085a`, les **135 tests Python** ont réussi. Le workflow d'analyse avancée a également réussi : Playwright sur toutes les pages HTML, parcours responsive mobile/tablette/ordinateur, Ruff, Bandit, Gitleaks et CodeQL Python/JavaScript.
- Après le déploiement GitHub Pages `ffeac350`, la surveillance de production a effectué **56 contrôles HTTP sans erreur** : page racine, accueil, simulation de ville, page documentaire, catalogue JSON, les 30 fichiers audio d'articles, les médias français du documentaire et les six variantes traduites (anglais, espagnol, allemand, portugais, arabe et chinois), chacune avec audio, vidéo et sous-titres. Les ressources vérifiées ont répondu HTTP 200.
- Le test réel Groq du 22 novembre a réussi. Le test Hugging Face a été ignoré par configuration ; aucune disponibilité gratuite de Hugging Face n'est donc revendiquée.
- La page documentaire générée le 22 novembre à 12:27:53 UTC propose des versions traduites du texte, de la narration, de la vidéo et des sous-titres dans six langues supplémentaires ; l'archive est prévue jusqu'au 22 décembre à 12:27:53 UTC. Le sélecteur et les tests vérifient le changement de ces médias, la conservation des liens/noms des sources et le retour complet au français. La simulation de ville utilise désormais la marque NEXORA dans les sept langues, vérifiée par Playwright.
- Le site public contient actuellement trois pages fonctionnelles principales : accueil, documentaire et simulation fictive de ville. Le catalogue contient 30 articles, 85 références de source et 30 fichiers audio. La simulation reste une démonstration fictive à indicateurs synthétiques, pas une ville 3D connectée à des données réelles.
- La surveillance du site public est désormais planifiée toutes les six heures, déclenchée lors des changements de contenu et après les statuts de déploiement. Les erreurs réseau temporaires (429, 5xx et interruptions réseau) sont réessayées avec attente progressive.
- **Limite multilingue toujours présente :** la langue du navigateur sélectionne automatiquement la langue de l'interface, mais le corps des articles et les sources conservent leur langue de publication. La traduction intégrale automatique de chaque article n'est pas encore implémentée.
- Ces contrôles valident le commit et le déploiement testés ; ils ne certifient pas une disponibilité permanente ni le fonctionnement sur chaque appareil physique.

L'estimation pondérée est passée à **56,48 / 100** en portant le domaine « Tests et amélioration continue » de 80 % à 85 %. Les autres domaines et leurs limites restent inchangés. Ce score ne signifie pas que le projet complet est terminé.


## Traduction progressive des articles — 22 novembre 2026

- La génération d'un nouvel article tente désormais une traduction IA des champs titre, résumé, verdict et conseil en anglais, espagnol, allemand, portugais, arabe et chinois simplifié. Une traduction absente ou invalide n'empêche jamais la publication ; le site garde alors le texte original.
- Les liens, titres de sources, dates et fichiers audio ne sont pas traduits ni modifiés par ce traitement. Le navigateur affiche les champs traduits uniquement lorsqu'une traduction complète pour la langue choisie existe.
- Le workflow `.github/workflows/traduire-archives.yml` traite progressivement trois anciens articles par jour, dans l'ordre du plus ancien au plus récent. Il utilise uniquement le fournisseur Groq configuré dans les secrets GitHub, sans recours à Hugging Face ni à un service payant. Si le quota est indisponible, le lot s'arrête sans corrompre le catalogue.
- Le traitement est limité à cinq articles maximum par exécution et conserve les traductions partielles pour les compléter lors d'une exécution ultérieure. Le résultat doit être contrôlé dans les journaux GitHub Actions ; la planification quotidienne n'est pas une garantie d'exécution à heure fixe.


## Tableau de bord privé local — 22 novembre 2026

- Le module `laboratoire_dashboard.py` ajoute une interface locale pour créer des missions, consulter leur détail et leur état, voir leur priorité et leur échéance, et demander une annulation coopérative.
- Le serveur écoute exclusivement sur `127.0.0.1`, utilise un jeton aléatoire en mémoire, refuse les requêtes inter-origines, limite les corps JSON à 16 Ko et applique des en-têtes CSP, no-store, no-referrer et anti-iframe.
- L'interface n'est pas intégrée à GitHub Pages et n'est pas un tableau de bord distant. Elle nécessite de lancer manuellement `python laboratoire_dashboard.py` sur une machine qui exécute le projet ; elle s'arrête avec Ctrl+C.
- Les missions sont triées par priorité puis échéance, avec migration SQLite pour les bases existantes. L'exécution reste bornée à trois agents et 180 secondes par mission ; aucun code généré n'est exécuté.


## Narrations audio traduites des articles — 22 novembre 2026

- Lorsqu'une traduction textuelle d'article est validée, le système tente aussi de générer une narration Edge TTS dans la langue correspondante (anglais, espagnol, allemand, portugais, arabe et chinois). Chaque fichier est référencé dans la variante de traduction ; le lecteur de la page d'accueil suit la langue sélectionnée si l'audio existe.
- Si une voix ou un service TTS échoue, l'article et sa traduction textuelle restent publiables ; le lecteur revient à l'audio français. Les fichiers traduits sont inclus dans le rattrapage progressif des archives et la politique de conservation des audios.
- La génération de voix est best-effort : elle n'est pas garantie pour chaque langue ni chaque article. Les tests navigateur vérifient le changement de source audio lorsqu'un fichier traduit est disponible.


## Audit complémentaire — 22 novembre 2026, commit 3b9d91e8

- Le tableau de bord privé local permet maintenant de créer des fiches d'opportunité R&D, de les classer, puis de suivre leur statut (candidate, research, prototype, validated ou rejected). Les fiches sont conservées dans le dossier local privé et ne sont pas publiées sur GitHub Pages. Les notes de faisabilité restent des estimations ; les preuves de demande doivent être vérifiées.
- La file de missions affiche le nombre de tentatives et permet de relancer manuellement une mission échouée, partielle ou interrompue. Le plafond est de trois tentatives au total. Aucune relance n'est automatique et aucune commande ou code généré n'est exécuté.
- La simulation urbaine publique comporte maintenant une vue isométrique 2D dessinée localement, quatre quartiers sélectionnables depuis la carte, des bâtiments et une circulation synthétiques. La légende est traduite dans les sept langues. Cela reste une simulation fictive dans le navigateur, pas une ville 3D connectée à des données réelles.
- Le rattrapage des traductions d'archives est planifié deux fois par jour, avec un maximum de trois articles par exécution (jusqu'à six articles par jour si le fournisseur gratuit et ses quotas le permettent). Le texte source, les noms et les liens des sources ne sont pas modifiés. Les traductions/audio peuvent rester incomplètes en cas de quota ou d'indisponibilité.
- Sur le commit 3b9d91e8, **168 tests Python ont réussi**. Le workflow avancé a réussi les tests navigateur, les parcours responsive, CodeQL Python et JavaScript, Ruff, Bandit et Gitleaks. Les tests navigateur couvrent aussi la carte isométrique et la sélection de quartier.
- Après publication, la surveillance de production a effectué **62 contrôles HTTP sans erreur**. Les ressources testées incluent les pages publiques, les articles, les audios et les médias du documentaire en plusieurs langues.
- Score pondéré recalculé : **61,70 %**. Le seuil de 70 % n'est pas atteint.

### Justification de la révision des notes

- Média, veille et site public : 92 % (vue isométrique, traduction progressive planifiée, surveillance de production renforcée ; les articles historiques ne sont pas tous traduits).
- Fournisseurs IA et orchestration : 40 % (pas de nouveau fournisseur gratuit réellement validé ; Hugging Face reste indisponible sans crédits).
- Missions persistantes et autonomie : 42 % (relance manuelle plafonnée et traçabilité des tentatives ; aucun worker hébergé en permanence).
- Laboratoire privé et sécurité : 55 % (tableau de bord local pour missions et R&D, contrôles d'accès et limites ; aucun tableau de bord distant hébergé).
- R&D et conception de produits : 45 % (création et suivi de fiches, mais pas encore de validation par des utilisateurs ni de preuves commerciales indépendantes).
- Tests et amélioration continue : 90 % (168 tests et contrôles avancés verts ; les tests ne remplacent pas une validation sur tous les appareils réels).


## Audit d'extension — 22 novembre 2026, commit 9ccabcf4

- L'accueil NEXORA propose maintenant une recherche textuelle et des filtres thématiques (technologie, IA, jeux vidéo, cybersécurité). Les libellés et les états vides sont traduits dans les sept langues. Les tests navigateur vérifient le filtre gaming et une recherche GTA.
- Le système de défis a été étendu à six missions, pour un maximum de 100 points et six rangs personnels. Les progrès sont conservés dans le stockage local du navigateur. Le site précise qu'il ne s'agit pas d'un classement mondial ; aucun compte ni donnée personnelle n'est envoyé à un serveur.
- Le laboratoire local dispose maintenant d'une feuille de route persistante de sept chantiers, avec priorités et statuts (à faire, en cours, bloqué, terminé). Les statuts sont écrits dans `.laboratoire_prive/roadmap.json`, hors du dépôt public, avec permissions restrictives sur POSIX. Les API sont protégées par le jeton local et l'origine locale.
- La feuille de route inclut explicitement les travaux encore manquants : traductions historiques, classement communautaire sécurisé, ville 3D, hébergement privé, agents isolés avec revue, atelier créatif et validation utilisateur.
- Sur le commit `9ccabcf4`, **173 tests Python ont réussi**. Les tests avancés ont tous réussi : Playwright, tests responsive, CodeQL Python/JavaScript, Ruff, Bandit et Gitleaks. Le build et le déploiement GitHub Pages ont réussi.
- La surveillance de production a effectué **74 contrôles HTTP sans erreur** après publication.
- Score pondéré recalculé : **63,29 %**. Le seuil de 70 % reste à atteindre.

### Justification des notes révisées

- Média, veille et site public : 94 % (recherche, filtres, six défis et rangs personnels ; il reste la traduction intégrale des archives et davantage de pages publiques).
- Laboratoire privé et sécurité : 60 % (tableau de bord local, file de missions, portefeuille R&D, feuille de route persistante, jeton d'accès, vérification d'origine et stockage local privé ; pas encore d'hébergement distant authentifié).
- Tests et amélioration continue : 92 % (173 tests et tous les contrôles avancés verts, plus 74 vérifications HTTP ; la validation sur tous les appareils physiques reste nécessaire).


## Extension du laboratoire local — 22 novembre 2026, commit acf03b51

- La feuille de route locale permet désormais de modifier les échéances en plus des statuts. Les dates doivent être valides et inclure un fuseau horaire ; une échéance peut être effacée. Le stockage reste dans le dossier privé ignoré par Git, avec écriture atomique et permissions POSIX restrictives.
- L'intégrité de la feuille de route vérifie maintenant l'ensemble des identifiants attendus, l'absence de doublons et la validité des priorités et statuts. Un fichier corrompu n'est jamais remplacé silencieusement.
- **174 tests Python ont réussi** sur le commit `acf03b51`. Playwright, CodeQL Python/JavaScript, Ruff, Bandit et Gitleaks ont tous réussi. GitHub Pages a été construit et déployé.
- La surveillance de production a effectué **74 contrôles HTTP sans erreur** après le déploiement.
- Score pondéré révisé : **63,59 %**. Le seuil de 70 % n'est pas encore atteint.

### Révision des domaines

- Laboratoire privé et sécurité : 61 % (feuille de route privée avec échéances, statuts et validation stricte ; aucun hébergement distant sécurisé n'est encore disponible).
- Tests et amélioration continue : 93 % (174 tests automatisés et tous les contrôles avancés verts ; les tests sur matériel réel restent à effectuer).


## Exécution par lots bornés — 22 novembre 2026, commit c35ab864

- Le tableau de bord local peut maintenant lancer jusqu'à trois missions en un seul lot manuel. Le plafond est validé côté serveur ; un lot s'arrête dès qu'une mission échoue ou n'aboutit pas à l'état terminé. Il n'y a ni boucle infinie ni exécution automatique permanente.
- Deux nouveaux tests vérifient le traitement de trois missions terminées et le refus d'une demande supérieure au plafond.
- **176 tests Python ont réussi**. Playwright, CodeQL Python/JavaScript, Ruff, Bandit et Gitleaks ont tous réussi. Le build et le déploiement Pages ont réussi.
- Score pondéré révisé : **64,29 %**. Le seuil de 70 % reste à atteindre.

### Révision des missions et de l'autonomie — 46 %

La file locale conserve les missions, leurs priorités, échéances et tentatives. Le tableau de bord permet l'annulation coopérative, la relance manuelle plafonnée à trois tentatives et l'exécution manuelle de lots de trois missions maximum. Les missions restent limitées dans le temps et dépendent de l'appareil qui exécute le laboratoire ; elles ne constituent pas un service cloud autonome permanent.

## Extension PWA, ville 3D et atelier Godot — 22 novembre 2026, commit c4206829

- Le site public dispose d'un manifeste d'application installable, d'une icône et d'un service worker. Les pages essentielles, la page méthode, la ville de démonstration et le catalogue des articles sont mis en cache ; une page de secours s'affiche hors ligne.
- Pour préserver le stockage des téléphones et tablettes, les fichiers audio et vidéo volumineux ne sont pas mis en cache. Les requêtes HTTP Range sont transmises directement au serveur pour ne pas casser la lecture multimédia.
- La démonstration urbaine conserve sa vue isométrique 2D et propose maintenant une vue WebGL 3D légère, avec rotation lente, géométrie simple et repli 2D si WebGL n'est pas disponible. Les quartiers et indicateurs restent fictifs : aucune infrastructure réelle n'est connectée.
- L'atelier de création peut générer des squelettes Godot 4 en 2D et 3D, en plus des modèles de site web, application web, jeu web, vidéo, audio et logiciel Python. Les fichiers produits ne sont ni exécutés ni publiés automatiquement ; le moteur Godot doit être installé séparément.
- **192 tests Python ont réussi** sur ce commit. Tous les contrôles avancés ont réussi : Playwright, parcours responsive, CodeQL Python/JavaScript, Ruff, Bandit et Gitleaks. Le build et le déploiement GitHub Pages ont réussi.
- La surveillance de production a effectué **79 requêtes de contrôle sans erreur** après publication.
- Le catalogue contient 30 articles ; 6 disposent actuellement de traductions dans les six langues cibles (anglais, espagnol, allemand, portugais, arabe et chinois). Les 24 autres restent à traiter progressivement.
- Score pondéré révisé : **65,70 %**. Le seuil de 70 % n'est pas atteint.

### Révision des domaines

- Média, veille et site public : 97 % (site installable et utilisable hors ligne pour les pages essentielles, catalogue d'articles en cache, vue 3D locale et repli 2D ; les traductions historiques restent incomplètes).
- Fournisseurs IA et orchestration : 40 % (Groq validé ; Hugging Face reste bloqué sans crédits et aucun second fournisseur gratuit n'est confirmé).
- Missions persistantes et autonomie : 46 % (file locale persistante et exécution bornée ; aucun worker cloud permanent).
- Laboratoire privé et sécurité : 61 % (tableau de bord local, portefeuille R&D et feuille de route privée ; pas d'hébergement distant authentifié).
- R&D et conception de produits : 48 % (portefeuille d'opportunités et modèles de génération de projets web, vidéo, audio, Python et Godot ; validation par des utilisateurs réels encore absente).
- Tests et amélioration continue : 96 % (192 tests Python, contrôles de sécurité et tests navigateur/responsive réussis, plus 79 vérifications de production ; les tests sur appareils physiques restent nécessaires).



## Extension PWA, ville WebGL et atelier Godot — 22 novembre 2026, commit c4206829

- **Application installable et consultation hors ligne :** le service worker met en cache les pages publiques essentielles, la page de secours hors ligne et le catalogue `articles.json`. Après une première visite en ligne, les pages essentielles et le texte du catalogue restent consultables hors connexion. Les fichiers audio/vidéo volumineux sont volontairement exclus du cache pour préserver le stockage mobile ; les requêtes HTTP Range des lecteurs multimédias contournent également la Cache API.
- **Ville expérimentale 3D :** la page propose maintenant une scène WebGL 3D légère, avec rendu limité à environ 30 images/s et préférence GPU basse consommation. La vue isométrique 2D reste disponible si WebGL n'est pas supporté. Les quatre quartiers, bâtiments et déplacements restent fictifs et synthétiques ; il ne s'agit pas d'une ville connectée à des données réelles.
- **Atelier de création :** ajout de modèles de démarrage Godot 4 en 2D et 3D, en complément des squelettes de sites, applications web, jeux navigateur, logiciels Python, projets audio et vidéo. Le générateur écrit des fichiers dans un dossier choisi, n'exécute pas le code et ne publie rien. Les projets Godot n'ont pas encore été compilés ni testés dans le moteur Godot lui-même.
- **Contrôle des médias documentaires :** le diagnostic vérifie désormais le manifeste du documentaire et l'existence des fichiers audio, vidéo, sous-titres traduits et archive écrite référencés. Les chemins sont confinés à leurs dossiers publics ; les fichiers absents, vides ou les chemins de traversée font échouer le contrôle.
- Sur le commit `c4206829`, **192 tests Python ont réussi**. Playwright a validé les pages HTML, les parcours responsive à 390, 768 et 1 440 px, le mode hors ligne PWA, le catalogue mis en cache, ainsi que la vue WebGL 3D et le repli 2D. Ruff, Bandit, Gitleaks et CodeQL Python/JavaScript ont réussi. Le build et le déploiement GitHub Pages ont réussi.
- Après publication, la surveillance de production a effectué **79 requêtes HTTP sans erreur** (0 erreur), dont les fichiers audio, vidéo et sous-titres des six variantes linguistiques.
- Score pondéré révisé : **65,23 %**. Ce score demeure loin d'une réalisation complète du projet et n'est pas une certification.

### Révision des domaines

- Média, veille et site public : 90 % (vue WebGL 3D avec repli 2D, application PWA, atelier navigateur et contrôles des médias ; la traduction intégrale des 30 articles est encore en rattrapage).
- Fournisseurs IA et orchestration : 40 % (Groq est le fournisseur principal ; Hugging Face n'est pas confirmé comme solution gratuite disponible).
- Missions persistantes et autonomie : 46 % (missions locales bornées ; aucun service cloud autonome permanent).
- Laboratoire privé et sécurité : 61 % (dashboard local et données privées locales ; pas de dashboard distant authentifié).
- R&D et conception de produits : 48 % (squelettes de création multi-format et Godot 2D/3D ; pas encore de validation utilisateur ni de compilation/test Godot).
- Tests et amélioration continue : 96 % (192 tests Python et contrôles avancés réussis ; les tests sur les appareils physiques et la validation réelle des projets Godot restent nécessaires).

### Limites qui empêchent de déclarer le projet terminé

- Aucun classement mondial : les défis restent enregistrés localement dans le navigateur.
- Le tableau de bord privé reste local ; GitHub Pages ne fournit pas de backend privé authentifié.
- Les tâches GitHub Actions sont ponctuelles et planifiées, pas des agents actifs 24 h/24.
- La ville reste une démonstration fictive, sans données municipales réelles.
- Les modèles Godot sont des points de départ, pas un éditeur complet ni une compilation validée.
- Un avancement supérieur à 100 % n'est pas une mesure réelle : « 110 % » peut seulement désigner un objectif symbolique de périmètre complet plus améliorations supplémentaires.


## Atelier de création intégré et sécurité des prototypes — 22 novembre 2026, commit fe807070

- **Atelier accessible depuis le tableau de bord privé local :** formulaire et API authentifiée pour générer les huit familles de projets (site, application web, jeu navigateur, Godot 2D, Godot 3D, logiciel Python, audio et vidéo). Le chemin de sortie est fixé dans `.laboratoire_prive/prototypes` ; l'API n'accepte aucun chemin de sortie fourni par le navigateur.
- **Protection des prototypes :** génération refusée si un dossier de sortie est un lien symbolique ; répertoires de projets en permissions POSIX `0700`, fichiers en `0600`. Un nom déjà utilisé renvoie HTTP 409 au lieu d'écraser un projet existant. Le générateur ne lance aucun code et ne publie aucun fichier.
- **Équipe d'agents étendue :** six rôles sont disponibles (chercheur, critique, architecte, rédacteur, auditeur, planificateur). Le tableau de bord permet de sélectionner les rôles ; la limite serveur reste de trois agents par mission et la durée maximale demeure bornée.
- **200 tests Python réussis** sur le commit `fe807070`, dont les nouveaux tests de génération depuis le dashboard, de conflit de nom, de rejet de liens symboliques et de permissions privées. Playwright, Ruff, Bandit, CodeQL Python/JavaScript et Gitleaks ont réussi. Le build et le déploiement Pages ont réussi.
- La surveillance de production a terminé **85 requêtes HTTP avec zéro erreur**, y compris le manifeste, les médias documentaires et les six variantes audio/vidéo/sous-titres.
- Score pondéré révisé après audit de traduction : **65,12 %**. Le projet reste incomplet ; ce chiffre est une estimation de périmètre, pas une certification.

### Révision des domaines

- Média, veille et site public : 91 % (atelier navigateur ZIP, défis exportables, PWA et ville WebGL ; seulement 5 des 30 articles audités disposent actuellement d'une traduction complète avec audio).
- Fournisseurs IA et orchestration : 40 % (six rôles, mais Hugging Face n'est pas confirmé comme fournisseur gratuit disponible).
- Missions persistantes et autonomie : 46 % (file locale, relances bornées, maximum trois agents ; pas de service cloud autonome permanent).
- Laboratoire privé et sécurité : 63 % (dashboard local, génération de prototypes privée, protections de chemin et permissions ; pas de dashboard distant authentifié).
- R&D et conception de produits : 54 % (atelier navigateur et dashboard local multi-format, modèles Godot 2D/3D ; les projets ne sont pas encore compilés/testés dans Godot et ne constituent pas un IDE complet).
- Tests et amélioration continue : 98 % (200 tests Python et contrôles automatisés réussis ; essais sur appareils physiques et validation réelle des jeux restent à faire).

### Limites toujours ouvertes

- Pas de classement mondial des défis : les points restent locaux au navigateur.
- Pas de backend privé hébergé ; le tableau de bord fonctionne uniquement sur la machine qui exécute Python.
- Les workflows GitHub Actions sont des exécutions planifiées, pas des agents permanents 24 h/24.
- La ville 3D est une simulation fictive, pas un jumeau numérique connecté.
- Les modèles Godot créent des squelettes, pas des jeux finalisés ; aucun test de compilation Godot n'a été effectué.
- « 110 % » ne peut pas être un pourcentage réel de complétude : le maximum mesurable reste 100 %, les améliorations supplémentaires se décrivent séparément.


## Contrôle de couverture des traductions — 22 novembre 2026

- Audit du catalogue public : 30 articles. Sept articles contiennent au moins une entrée de traduction, mais seulement **5/30** ont toutes les traductions textuelles et audio attendues pour les six langues secondaires. Les autres conservent leur version originale ; les sources et leurs liens ne sont jamais traduits.
- Le rattrapage progressif a été accéléré de 3 à **5 articles maximum par exécution**, avec une limite stricte de 5 dans le code et un délai maximal de 20 minutes pour le workflow. Il s'exécute deux fois par jour, reste dépendant du quota Groq gratuit et s'arrête proprement si le fournisseur échoue.
- Le rattrapage n'est pas instantané : les articles historiques non traduits ne deviennent pas disponibles dans les six langues tant que leurs traductions et fichiers audio n'ont pas été produits. Ne pas annoncer une traduction intégrale avant un nouveau contrôle du catalogue.
- Le site public comprend maintenant un atelier de création téléchargeant localement un ZIP des squelettes de huit types de projets, en sept langues. Il fonctionne dans le navigateur sans envoyer de fichiers vers un serveur.
- La surveillance de production a validé l'atelier public : HTTP 200. Sur le contrôle associé, **86 requêtes ont réussi, 0 erreur**. Les tests Python ont atteint **205 tests réussis**.


## Atelier navigateur et sauvegarde des défis — 22 novembre 2026, commit 386e5373

- **Atelier public multilingue :** la navigation NEXORA propose un atelier qui crée un ZIP directement dans le navigateur. Huit modèles sont disponibles : site, application web, jeu navigateur, Godot 2D, Godot 3D, Python, audio et vidéo. L'interface est traduite en sept langues ; le fichier n'est pas téléversé, aucun code n'est exécuté et le téléchargement est lancé localement.
- **Contrôle du ZIP :** l'archive est construite sans bibliothèque distante, avec en-têtes locaux, CRC32, répertoire central et fin ZIP. Le test Playwright vérifie la signature ZIP, le répertoire central, les fichiers Godot 3D, la validation des noms et la conservation du modèle choisi lors du changement de langue. Le test navigateur vérifie aussi l'interface arabe RTL.
- **Sauvegarde des défis :** les six cases de progression peuvent être exportées dans un JSON versionné (v1) puis importées sur un autre navigateur. L'import est limité à 8 Ko et exige exactement six valeurs booléennes ; le score et le rang sont recalculés depuis les cases, jamais acceptés depuis le fichier. Les sauvegardes invalides sont rejetées sans modifier la progression.
- **208 tests Python réussis** sur le commit `386e5373`. Playwright a réussi les parcours de toutes les pages, les tests responsive mobile/tablette/ordinateur, l'atelier ZIP, les défis export/import, la ville WebGL 3D avec repli 2D et le mode hors ligne PWA. Ruff, Bandit, CodeQL Python/JavaScript et Gitleaks ont réussi. Le build et le déploiement Pages ont réussi.
- Le dernier contrôle de production complet précédent avait validé **86 requêtes HTTP sans erreur** sur le commit `0880cb31`, incluant l'atelier public. Le déploiement du commit `386e5373` a ensuite réussi ; le contrôle Playwright local a validé les nouveaux parcours de défis.
- Score pondéré révisé : **65,70 %**. Les traductions complètes restent le principal manque visible : 5 articles sur 30 seulement ont toutes les traductions textuelles et audio attendues pour les six langues secondaires. Le rattrapage est limité à cinq articles par exécution, deux fois par jour, selon les quotas disponibles.

### Limites toujours ouvertes

- Aucun classement mondial des défis : la sauvegarde export/import transfère seulement une progression personnelle.
- Aucun backend privé hébergé ; le tableau de bord privé reste local.
- Les workflows planifiés ne sont pas des agents permanents 24 h/24.
- Les traductions historiques ne sont pas intégralement terminées.
- La ville WebGL est fictive et synthétique, pas un jumeau numérique.
- Les projets Godot restent des squelettes ; aucune compilation dans le moteur Godot n'a été validée.
- 110 % n'est pas un pourcentage de complétude mesurable ; le maximum réel reste 100 % plus des améliorations supplémentaires décrites séparément.


## Vérification de reprise — 22 novembre 2026, HEAD a2b7399a

Contrôle effectué après les derniers commits automatiques de publication :

- **Déploiement GitHub Pages :** le workflow `pages build and deployment` (run 45055835724) a terminé avec succès sur le commit `a2b7399a` ; les étapes build, deploy et report-build-status sont toutes vertes.
- **Qualité et sécurité :** les workflows de tests (run 45055597695) et d'analyse avancée (run 45055597668) ont terminé avec succès sur `cd757011`. Les jobs visibles sont verts : tests, Ruff/Bandit, Gitleaks, CodeQL Python, CodeQL JavaScript/TypeScript et tests navigateur de toutes les pages HTML.
- **Production :** la surveillance (run 45059557226), exécutée après le déploiement de `a2b7399a`, a confirmé **86 requêtes HTTP réussies et 0 erreur**. Les contrôles incluent les pages, les audios d'articles, le manifeste documentaire et les variantes audio, vidéo et sous-titres du documentaire dans les six langues secondaires.
- **Archivage :** les exécutions de nettoyage des archives (runs 45062022825 et 45066379533) ont terminé avec succès.
- **Catalogue au moment de l'audit :** 30 articles, 7 avec au moins une traduction, mais seulement **5/30** avec les champs textuels et audio complets dans chacune des six langues secondaires (en, es, de, pt, ar, zh). Ce comptage a été recalculé directement depuis `site/articles.json` ; il ne faut donc pas annoncer que tous les articles sont traduits.
- Le dernier commit de tête est une publication automatique d'article. Le dernier ensemble complet de tests de code cité ci-dessus porte sur `cd757011`, antérieur à cette publication automatique ; la surveillance de production porte bien sur le déploiement `a2b7399a`.
- **Avancement :** la dernière estimation pondérée détaillée demeure **65,70 %**, calculée sur le commit `386e5373`. Aucun nouveau score global n'est attribué dans ce contrôle limité, car les changements automatiques ultérieurs ne constituent pas un nouvel audit fonctionnel complet.

### Points qui empêchent toujours de déclarer le projet complet

- Le classement des défis reste personnel et local au navigateur ; pas de classement mondial.
- Le laboratoire privé reste hébergé localement sur la machine qui lance Python ; pas de backend privé distant avec authentification.
- GitHub Actions exécute des tâches ponctuelles planifiées ; ce n'est pas un serveur d'agents actif en permanence.
- La ville WebGL reste une simulation fictive avec données synthétiques.
- La majorité des archives n'a pas encore les six traductions complètes avec audio.
- Les modèles Godot sont des squelettes de départ et leur compilation dans Godot n'est pas validée.
- Le dépôt GitHub est public : aucun secret, document privé ou donnée personnelle ne doit y être ajouté.
- L'objectif « 110 % » reste symbolique : le taux de complétude mesurable est plafonné à 100 %, les améliorations supplémentaires devant être décrites séparément.

## Vérification groupée — 22 novembre 2026, commit 756e29d8

Contrôle effectué après la correction du rattrapage des traductions :

- **Commit vérifié :** `756e29d8626576e5cc267459b0e3b2861bf2fa50`.
- **Tests automatiques :** workflow `45073316873` réussi. La suite affiche **209 tests Python réussis** en 9,706 secondes ; `healthcheck.py`, la compilation Python, les fichiers JSON et les fichiers indispensables ont également passé.
- **Qualité et sécurité :** workflow `45073316814` réussi. Ruff, Bandit, Gitleaks, CodeQL Python et JavaScript/TypeScript, ainsi que les tests navigateur, sont verts.
- **Parcours navigateur :** les pages d'accueil, documentaire, ville, méthode et atelier ont été ouvertes avec Playwright à 390, 768 et 1 440 pixels ; les neuf contrôles responsive listés dans les journaux ont réussi.
- **Publication :** workflow Pages `45073316464` réussi ; l'artefact du site a été construit et téléversé. Ce contrôle confirme la construction et le déploiement GitHub Pages, pas une vérification HTTP indépendante de chaque média après publication.
- **Correctif de traduction :** le rattrapage distingue maintenant la complétude du texte et celle des audios. Si les textes existent déjà, le traitement peut compléter uniquement les audios manquants, sans retraduire tout l'article. Le traitement reste plafonné à cinq articles par exécution.

### État fonctionnel inchangé à ne pas surestimer

- Le dernier score pondéré détaillé reste **65,70 %**, calculé lors de l'audit précédent sur le commit `386e5373`. Les contrôles verts de ce commit ne suffisent pas à recalculer le score fonctionnel global.
- Le bilan précédent recensait seulement 5 articles sur 30 avec toutes les traductions textuelles et audio attendues dans les six langues secondaires ; le correctif améliore le rattrapage mais ne prouve pas que toutes les archives sont désormais traduites.
- Le classement des défis reste local/personnel, sans classement mondial.
- Le laboratoire privé reste local à la machine qui lance Python ; aucun backend privé distant avec authentification n'est hébergé par GitHub Pages.
- GitHub Actions exécute des tâches ponctuelles ; ce n'est pas un serveur permanent 24 h/24.
- La ville reste une simulation fictive à données synthétiques, pas un jumeau numérique réel.
- Le dépôt est public : les archives et notes privées doivent rester hors de Git et hors de GitHub Pages.

Ce contrôle valide la qualité du commit et son déploiement. Il ne signifie pas que toutes les fonctionnalités futures du projet sont terminées.


## Centre de pilotage public regroupé — 22 novembre 2026

- Une page unique `site/espace.html` regroupe les accès au média, aux documentaires, à la simulation 2D/3D, aux défis, à l'atelier et à la méthode.
- Le centre de pilotage ajoute un contrôle manuel depuis le navigateur : il lit le catalogue et le manifeste documentaires, puis vérifie les pages publiques et chaque fichier audio/vidéo/sous-titre référencé dans les articles et le documentaire. Le résultat indique les réponses HTTP et les ressources en échec ; il ne certifie pas la qualité éditoriale ni la disponibilité future.
- La page est disponible en sept langues, mémorise le choix de langue et utilise le RTL en arabe. Elle est ajoutée au cache PWA des pages essentielles.
- Le centre explique explicitement les limites qui restent réelles : défis et rang local uniquement, laboratoire privé sur ordinateur local, pas d'agents cloud permanents, ville fictive. Il donne accès au guide Linux du laboratoire sans exposer son API locale.
- Cette modification améliore l'accès et l'auto-diagnostic en un seul ensemble ; elle ne crée pas un hébergement privé, un classement mondial ou un serveur 24 h/24.
