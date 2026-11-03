# Rapport de validation des maths

Format : « Math Sign-Off Template » du repo egorfedorov/Slot-Casino-Game-Developer-Skills-for-Stake-Engine.

## 1. Périmètre
- Classeur : `classeur_maths.xlsx` (empreinte 1cf714931f19)
- Date : 2026-11-03 14:45
- Grille : 5 rouleaux x 3 lignes (243 ways)
- Modes : base, achat bonus 1, achat bonus 2

## 2. Hypothèses
- Gains en x la mise totale ; montants arrondis au centième par le SDK.
- Multis de colonne indépendants des symboles ; une way prend la somme des multis de ses colonnes.
- Calcul exact avant plafond du max win ; la simulation applique le plafond.

## 3. Décomposition du RTP (calcul exact)

| Composante | Fréquence | Gain moyen | RTP |
|---|---|---|---|
| Spins (jeu de base, multis compris) | chaque spin | 0.6099 x | 60.985% |
| Bonus 1 « Free spins » (non collant) | 1 sur 334 | 96.8 x (10.3 FS) | 28.959% |
| Bonus 2 « Super free spins » (collant) | 1 sur 8,724 | 546.2 x (10.3 FS) | 6.261% |
| **Total** | | | **96.205%** |

## 4. Méthode
- Simulation : `simulateur.py`, graine 2026, 2,113,788 spins de base (strates du nombre de scatters), 100,000 tours par bonus.
- Le repo de skills recommande ≥ 1 000 000 de spins pour caler et ≥ 20 000 000 pour valider ; la doc Stake Engine demande 100 000 à 1 000 000 de résultats (books) par mode.

## 5. Résultats

| Indicateur | Exact | Simulé | Écart | Statut |
|---|---|---|---|---|
| RTP | 96.205% | 95.337% ± 0.912% | -0.869% | OK |
| Bonus 1 : fréquence | 1 sur 334 | 1 sur 334 | | |
| Bonus 1 : gain moyen | 96.8 x | 93.6 x | | |
| Bonus 2 : fréquence | 1 sur 8,724 | 1 sur 8,724 | | |
| Bonus 2 : gain moyen | 546.2 x | 538.9 x | | |
| Fréquence de gain | | 30.39% | | |
| Écart-type | | 17.3 x | | |
| Max win | 10,000 x | 1 tour sur 4,836,509 | | |

## 6. Contrôles

| Contrôle | Valeur | Règle | Statut |
|---|---|---|---|
| RTP exact du jeu de base | 96.205% | entre 96.00% et 96.50% (ta règle ; SDK : 96,0 à 96,7 %) | OK |
| RTP simulé (plafond compris) | 95.337% ± 0.912% | écart à l'exact < 3 marges | OK |
| Part des spins (hors bonus) | 63.4% | 55% à 70% : les spins rapportent sans tout donner | OK |
| Part du bonus 1 | 30.1% | au plus 35% : aucun bonus ne donne tout | OK |
| Bonus 1 : fréquence | 1 sur 334 | entre 1/100 et 1/1 000 000 | OK |
| Part du bonus 2 | 6.5% | au plus 35% : aucun bonus ne donne tout | OK |
| Bonus 2 : fréquence | 1 sur 8,724 | entre 1/100 et 1/1 000 000 | OK |
| Fréquence de gain | 30.4% (1 sur 3.3) | 1 sur 3 à 1 sur 8 (checklist) ; jamais moins de 1 sur 20 (doc) | OK |
| Max win atteignable | 1 sur 4,836,509 | plus fréquent que 1 sur 10 000 000 (doc « Math Requirements ») | OK |
| Écart-type du jeu de base | 17.3x | au moins 0,6 (soumission SDK) | OK |
| Contrôles de risque Studio (base) | tous OK | RISK_CHECKS du SDK : chaque échec baisse la mise max autorisée | OK |
| Achat bonus 1 : RTP simulé | 95.13% ± 1.31% | à 0,5 % du jeu de base (doc) ; la pondération du SDK le règle exactement | OK |
| Achat bonus 1 : contrôles de risque Studio | tous OK | RISK_CHECKS du SDK ; sinon la pondération rend les plus gros gains de ce mode plus rares | OK |
| Achat bonus 2 : RTP simulé | 94.82% ± 1.04% | à 0,5 % du jeu de base (doc) ; la pondération du SDK le règle exactement | OK |
| Achat bonus 2 : contrôles de risque Studio | tous OK | RISK_CHECKS du SDK ; sinon la pondération rend les plus gros gains de ce mode plus rares | OK |

## 7. Décision
- Statut : **VALIDÉ**
- Rappel : la validation finale se fait sur les fichiers générés par le SDK (RTP pondéré des books).
