# État d'avancement global du projet

Dernière évaluation fonctionnelle détaillée : 18 novembre 2026. Audit GitHub complémentaire : 19 novembre 2026.

## Audit complémentaire du 19 novembre 2026

- Le dépôt GitHub est toujours **public** : tous les fichiers suivis et leur historique sont consultables. Le dossier ignoré `.laboratoire_prive/` ne protège pas les fichiers déjà commités. Aucun élément confidentiel ne doit y être ajouté.
- Les workflows « Tests automatiques et contrôle qualité », « Analyse avancée - sécurité, qualité et site » et « pages build and deployment » ont terminé avec succès sur le commit `0017a074` le 19 novembre 2026. Les contrôles avancés ont inclus Ruff, Bandit, Gitleaks, CodeQL Python et JavaScript ainsi que les tests navigateur Playwright. Cela confirme ces exécutions précises, pas le bon fonctionnement permanent de tous les services.
- L'interface de la page d'accueil propose maintenant sept langues : français, anglais, espagnol, allemand, portugais, arabe et chinois. Le choix est mémorisé dans le navigateur et l'arabe active l'affichage de droite à gauche. Les articles et documentaires ne sont pas automatiquement traduits : leur langue d'origine est conservée.
- Le dernier contrôle réel des fournisseurs a confirmé Groq fonctionnel et Hugging Face bloqué par une demande de crédits prépayés. Le workflow utilise donc Groq par défaut ; Hugging Face reste une option explicite, mais n'est pas garanti gratuit.

## Résultat

**Estimation pondérée recalculée : 55,89 / 100.**

Ce pourcentage est un indicateur d'avancement fonctionnel construit à partir des domaines ci-dessous. Ce n'est ni un pourcentage de lignes de code terminées, ni une garantie de disponibilité, ni une certification de mise en production. Les notes sont des estimations prudentes fondées sur les fonctions présentes et les contrôles exécutés.

| Domaine | Poids | Avancement estimé | Contribution |
|---|---:|---:|---:|
| Média, veille et site public | 23,53 % | 90 % | 21,18 |
| Fournisseurs IA et orchestration d'agents | 17,65 % | 40 % | 7,06 |
| Missions persistantes et autonomie | 17,65 % | 35 % | 6,18 |
| Laboratoire privé et sécurité | 17,65 % | 45 % | 7,94 |
| R&D et conception de produits | 11,76 % | 35 % | 4,12 |
| Tests et amélioration continue | 11,76 % | 80 % | 9,41 |
| **Total** | **100 %** |  | **55,89 %** |

Calcul : somme de (poids × note du domaine) / 100.

## Justification des notes

### Média, veille et site public — 90 %
Le site public, la récupération de sources, la rédaction assistée, les articles, les fichiers audio et les workflows planifiés existent. Un premier documentaire de démonstration a été généré et publié en MP4 H.264/AAC avec narration, diapositives 1280×720 dessinées localement et références aux sources. Le rendu a été vérifié par FFmpeg et le workflow complet a réussi. Cette vidéo reste un documentaire temporaire de test, pas un studio de montage universel. Restent notamment un hébergement secondaire réellement actif, une supervision permanente et une validation factuelle plus forte.

### Fournisseurs IA et orchestration d'agents — 40 %
Le projet possède une couche de fournisseurs IA, un basculement, cinq profils spécialisés et un orchestrateur séquentiel avec trois rôles. Les profils ne sont pas des agents indépendants qui travaillent en continu. Un test réel du 19 novembre a réussi avec Groq. Hugging Face a refusé la génération faute de crédits prépayés ; il ne doit donc pas être considéré comme un secours gratuit disponible.

### Missions persistantes et autonomie — 35 %
Une file SQLite locale conserve les missions et leurs états ; un worker peut lancer la mission suivante. L'orchestrateur limite actuellement une mission à 180 secondes et trois rôles maximum. Les missions restées actives depuis plus de cinq minutes sont maintenant classées comme interrompues avant le lancement suivant. L'arrêt forcé d'une mission déjà en cours, les missions de plusieurs heures ou deux jours et le fonctionnement permanent ne sont pas encore réalisés.

### Laboratoire privé et sécurité — 45 %
Le dossier local du laboratoire est ignoré par Git, les contrôles Gitleaks, CodeQL, Bandit et Ruff sont présents, et un contrôles statiques complémentaires ont été ajoutés. Il n'existe pas encore de tableau de bord privé hébergé avec authentification et autorisations côté serveur. GitHub Pages reste public.

### R&D et conception de produits — 35 %
L'atelier de sélection de produits note les opportunités selon la douleur client, les preuves de demande, la faisabilité, la différenciation, le coût et l'accès au marché. Des prototypes commencent à exister, mais les entretiens clients, les preuves de marché indépendantes, les tests avec de vrais utilisateurs et la validation économique restent à faire.

### Tests et amélioration continue — 80 %
La suite compte 109 tests Python réussis lors du dernier contrôle automatisé du 18 novembre. Le dernier workflow avancé a réussi : Ruff, Bandit, Gitleaks, CodeQL Python et JavaScript, ainsi que les tests Playwright des trois pages et les parcours responsive de l'accueil et du documentaire à 390, 768 et 1 440 px. Le diagnostic du dépôt a vérifié 25 articles, 85 sources et 24 fichiers audio, cinq profils d'agents et l'absence de données de ville dans le site public. La boucle d'auto-évaluation produit un rapport et un backlog ; elle ne réécrit pas le code de production et ne déploie pas de corrections de façon autonome.

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

- 55,89 % est une estimation pondérée selon cette grille ; cela ne signifie pas que toutes les fonctionnalités sont prêtes à être utilisées.
- Aucun travail ne continue en arrière-plan après la fin d'une exécution GitHub Actions, sauf les workflows effectivement planifiés.
- Aucune vente, dépense ou publication externe n'est automatique.
- Les rapports et prototypes privés ne doivent pas être ajoutés au site public.
