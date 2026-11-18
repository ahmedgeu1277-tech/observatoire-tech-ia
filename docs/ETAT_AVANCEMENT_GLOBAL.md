# État d'avancement global du projet

Dernière évaluation : 18 novembre 2026, après intégration et publication réussie du premier documentaire vidéo MP4.

## Résultat

**Estimation pondérée : 52,75 / 100.**

Ce pourcentage est un indicateur d'avancement fonctionnel construit à partir des domaines ci-dessous. Ce n'est ni un pourcentage de lignes de code terminées, ni une garantie de disponibilité, ni une certification de mise en production. Les notes sont des estimations prudentes fondées sur les fonctions présentes et les contrôles exécutés.

| Domaine | Poids | Avancement estimé | Contribution |
|---|---:|---:|---:|
| Média, veille et site public | 20 % | 90 % | 18,00 |
| Fournisseurs IA et orchestration d'agents | 15 % | 40 % | 6,00 |
| Missions persistantes et autonomie | 15 % | 35 % | 5,25 |
| Laboratoire privé et sécurité | 15 % | 45 % | 6,75 |
| R&D et conception de produits | 10 % | 35 % | 3,50 |
| Création logicielle et Roblox | 15 % | 35 % | 5,25 |
| Tests et amélioration continue | 10 % | 80 % | 8,00 |
| **Total** | **100 %** |  | **52,75 %** |

Calcul : somme de (poids × note du domaine) / 100.

## Justification des notes

### Média, veille et site public — 90 %
Le site public, la récupération de sources, la rédaction assistée, les articles, les fichiers audio et les workflows planifiés existent. Un premier documentaire de démonstration a été généré et publié en MP4 H.264/AAC avec narration, diapositives 1280×720 dessinées localement et références aux sources. Le rendu a été vérifié par FFmpeg et le workflow complet a réussi. Cette vidéo reste un documentaire temporaire de test, pas un studio de montage universel. Restent notamment un hébergement secondaire réellement actif, une supervision permanente et une validation factuelle plus forte.

### Fournisseurs IA et orchestration d'agents — 40 %
Le projet possède une couche de fournisseurs IA, un basculement, cinq profils spécialisés et un orchestrateur séquentiel avec trois rôles. Les profils ne sont pas des agents indépendants qui travaillent en continu. Le diagnostic récent a signalé l'indisponibilité de Groq pendant un essai ; la stabilité réelle des deux fournisseurs doit encore être mesurée sur plusieurs cycles.

### Missions persistantes et autonomie — 35 %
Une file SQLite locale conserve les missions et leurs états ; un worker peut lancer la mission suivante. L'orchestrateur limite actuellement une mission à 180 secondes et trois rôles maximum. L'arrêt d'une mission déjà en cours, les missions de plusieurs heures ou deux jours, les reprises automatiques robustes et le fonctionnement permanent ne sont pas encore réalisés.

### Laboratoire privé et sécurité — 45 %
Le dossier local du laboratoire est ignoré par Git, les contrôles Gitleaks, CodeQL, Bandit et Ruff sont présents, et un validateur statique des projets Roblox a été ajouté. Il n'existe pas encore de tableau de bord privé hébergé avec authentification et autorisations côté serveur. GitHub Pages reste public.

### R&D et conception de produits — 35 %
L'atelier de sélection de produits note les opportunités selon la douleur client, les preuves de demande, la faisabilité, la différenciation, le coût et l'accès au marché. Des prototypes commencent à exister, mais les entretiens clients, les preuves de marché indépendantes, les tests avec de vrais utilisateurs et la validation économique restent à faire.

### Création logicielle et Roblox — 35 %
Un générateur crée un squelette de jeu Roblox obby au format Rojo, avec scripts serveur/client et monnaie gérée côté serveur. Un validateur statique contrôle certains fichiers et motifs dangereux sans exécuter le code. Le projet sait aussi générer une vidéo éditoriale MP4 narrée à partir de dossiers publiés. Il n'y a toujours pas de connexion directe à Roblox Studio, de génération IA complète d'un jeu, de test de gameplay automatisé ni de publication Roblox.

### Tests et amélioration continue — 80 %
La suite compte 99 tests Python réussis lors des contrôles du 18 novembre. Les workflows exécutent Ruff, Bandit, Gitleaks, CodeQL et des tests Playwright de navigation et d'affichage ; les exécutions de sécurité et de qualité associées au moteur vidéo ont réussi. La boucle d'auto-évaluation produit un rapport et un backlog ; elle ne réécrit pas le code de production et ne déploie pas de corrections de façon autonome.

## Conditions pour augmenter le score

1. Vérifier plusieurs cycles réels Groq et Hugging Face sans exposer les clés.
2. Ajouter un tableau de bord local des missions avec arrêt fiable et reprise après interruption.
3. Construire une interface privée avec authentification réelle sur un backend séparé du site public.
4. Étendre le générateur Roblox, compiler/analyser Luau et tester un parcours de jeu réel dans Roblox Studio.
5. Tester les prototypes avec des utilisateurs et collecter des preuves de demande.
6. Permettre aux agents de proposer des corrections dans des branches isolées, puis exiger tests, revue et retour arrière avant toute fusion.

## Limites importantes

- 52,75 % signifie que le seuil de la feuille de route est atteint selon cette grille ; cela ne signifie pas que toutes les fonctionnalités sont prêtes à être utilisées.
- Aucun travail ne continue en arrière-plan après la fin d'une exécution GitHub Actions, sauf les workflows effectivement planifiés.
- Aucune vente, dépense, publication externe ou action sur un compte Roblox n'est automatique.
- Les rapports et prototypes privés ne doivent pas être ajoutés au site public.
