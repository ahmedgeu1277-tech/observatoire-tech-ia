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

**Estimation pondérée recalculée : 56,48 / 100.**

Ce pourcentage est un indicateur d'avancement fonctionnel construit à partir des domaines ci-dessous. Ce n'est ni un pourcentage de lignes de code terminées, ni une garantie de disponibilité, ni une certification de mise en production. Les notes sont des estimations prudentes fondées sur les fonctions présentes et les contrôles exécutés.

| Domaine | Poids | Avancement estimé | Contribution |
|---|---:|---:|---:|
| Média, veille et site public | 23,53 % | 90 % | 21,18 |
| Fournisseurs IA et orchestration d'agents | 17,65 % | 40 % | 7,06 |
| Missions persistantes et autonomie | 17,65 % | 35 % | 6,18 |
| Laboratoire privé et sécurité | 17,65 % | 45 % | 7,94 |
| R&D et conception de produits | 11,76 % | 35 % | 4,12 |
| Tests et amélioration continue | 11,76 % | 85 % | 10,00 |
| **Total** | **100 %** |  | **56,48 %** |

Calcul : somme de (poids × note du domaine) / 100.

## Justification des notes

### Média, veille et site public — 90 %
Le site public, la récupération de sources, la rédaction assistée, les articles, les fichiers audio et les workflows planifiés existent. Un premier documentaire de démonstration a été généré et publié en MP4 H.264/AAC avec narration, diapositives 1280×720 dessinées localement et références aux sources. Le rendu a été vérifié par FFmpeg et le workflow complet a réussi. Cette vidéo reste un documentaire temporaire de test, pas un studio de montage universel. Restent notamment un hébergement secondaire réellement actif, une supervision permanente et une validation factuelle plus forte.

### Fournisseurs IA et orchestration d'agents — 40 %
Le projet possède une couche de fournisseurs IA, un basculement, cinq profils spécialisés et un orchestrateur séquentiel avec trois rôles. Les profils ne sont pas des agents indépendants qui travaillent en continu. Un test réel du 19 novembre a réussi avec Groq. Hugging Face a refusé la génération faute de crédits prépayés ; il ne doit donc pas être considéré comme un secours gratuit disponible.

### Missions persistantes et autonomie — 35 %
Une file SQLite locale conserve les missions et leurs états ; un worker peut lancer la mission suivante. L'orchestrateur limite actuellement une mission à 180 secondes et trois rôles maximum. Une mission en attente peut être annulée immédiatement ; une mission active reçoit un signal d'annulation et s'arrête entre deux appels IA. Un appel déjà lancé peut néanmoins aller jusqu'à son délai maximal (60 secondes). Les missions restées actives depuis plus de cinq minutes sont classées comme interrompues avant le lancement suivant. L'arrêt instantané d'un appel en cours, les missions de plusieurs heures ou deux jours et le fonctionnement permanent ne sont pas encore réalisés.

### Laboratoire privé et sécurité — 45 %
Le dossier local du laboratoire est ignoré par Git, les contrôles Gitleaks, CodeQL, Bandit et Ruff sont présents, et un contrôles statiques complémentaires ont été ajoutés. Il n'existe pas encore de tableau de bord privé hébergé avec authentification et autorisations côté serveur. GitHub Pages reste public.

### R&D et conception de produits — 35 %
L'atelier de sélection de produits note les opportunités selon la douleur client, les preuves de demande, la faisabilité, la différenciation, le coût et l'accès au marché. Des prototypes commencent à exister, mais les entretiens clients, les preuves de marché indépendantes, les tests avec de vrais utilisateurs et la validation économique restent à faire.

### Tests et amélioration continue — 85 %
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

- Sur le commit vérifié `79b57aa7`, les **135 tests Python** ont réussi. Le workflow d'analyse avancée a également réussi : Playwright sur toutes les pages HTML, parcours responsive mobile/tablette/ordinateur, Ruff, Bandit, Gitleaks et CodeQL Python/JavaScript.
- Après le déploiement GitHub Pages, la surveillance de production a effectué **56 contrôles HTTP sans erreur** : page racine, accueil, simulation de ville, page documentaire, catalogue JSON, les 30 fichiers audio d'articles, les médias français du documentaire et les six variantes traduites (anglais, espagnol, allemand, portugais, arabe et chinois), chacune avec audio, vidéo et sous-titres. Les ressources vérifiées ont répondu HTTP 200.
- Le test réel Groq du 22 novembre a réussi. Le test Hugging Face a été ignoré par configuration ; aucune disponibilité gratuite de Hugging Face n'est donc revendiquée.
- La page documentaire propose bien des versions traduites du texte, de la narration, de la vidéo et des sous-titres dans six langues supplémentaires lorsque leur génération réussit. Le sélecteur et les tests vérifient le changement de ces médias, la conservation des liens/noms des sources et le retour complet au français.
- Le site public contient actuellement trois pages fonctionnelles principales : accueil, documentaire et simulation fictive de ville. Le catalogue contient 30 articles, 85 références de source et 30 fichiers audio. La simulation reste une démonstration fictive à indicateurs synthétiques, pas une ville 3D connectée à des données réelles.
- La surveillance du site public est désormais planifiée toutes les six heures, déclenchée lors des changements de contenu et après les statuts de déploiement. Les erreurs réseau temporaires (429, 5xx et interruptions réseau) sont réessayées avec attente progressive.
- **Limite multilingue toujours présente :** la langue du navigateur sélectionne automatiquement la langue de l'interface, mais le corps des articles et les sources conservent leur langue de publication. La traduction intégrale automatique de chaque article n'est pas encore implémentée.
- Ces contrôles valident le commit et le déploiement testés ; ils ne certifient pas une disponibilité permanente ni le fonctionnement sur chaque appareil physique.

L'estimation pondérée est passée à **56,48 / 100** en portant le domaine « Tests et amélioration continue » de 80 % à 85 %. Les autres domaines et leurs limites restent inchangés. Ce score ne signifie pas que le projet complet est terminé.
