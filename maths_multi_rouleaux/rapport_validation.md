# Rapport de validation des maths

Format : « Math Sign-Off Template » du repo egorfedorov/Slot-Casino-Game-Developer-Skills-for-Stake-Engine.

## 1. Périmètre
- Classeur : `classeur_maths.xlsx` (empreinte a39ce22df12b)
- Date : 2026-11-03 14:26
- Grille : 5 rouleaux x 3 lignes (243 ways)
- Modes : base, achat bonus 1

## 2. Hypothèses
- Gains en x la mise totale ; montants arrondis au centième par le SDK.
- Multis de colonne indépendants des symboles ; une way prend la somme des multis de ses colonnes.
- Calcul exact avant plafond du max win ; la simulation applique le plafond.

## 3. Décomposition du RTP (calcul exact)

| Composante | Fréquence | Gain moyen | RTP |
|---|---|---|---|
| Spins (jeu de base, multis compris) | chaque spin | 0.6112 x | 61.123% |
| Bonus 1 « Free spins » (non collant) | 1 sur 334 | 96.3 x (10.3 FS) | 28.796% |
| Bonus 2 « Super free spins » (collant) | 1 sur 8,724 | 546.4 x (10.3 FS) | 6.263% |
| **Total** | | | **96.183%** |

## 4. Méthode
- Simulation : `simulateur.py`, graine 2026, 2,113,788 spins de base (strates du nombre de scatters), 100,000 tours par bonus.
- Le repo recommande ≥ 1 000 000 de spins pour orienter le calage et ≥ 20 000 000 pour valider.

## 5. Résultats

| Indicateur | Exact | Simulé | Écart | Statut |
|---|---|---|---|---|
| RTP | 96.183% | 96.552% ± 0.996% | +0.370% | OK |
| Bonus 1 : fréquence | 1 sur 334 | 1 sur 334 | | |
| Bonus 1 : gain moyen | 96.3 x | 97.3 x | | |
| Bonus 2 : fréquence | 1 sur 8,724 | 1 sur 8,724 | | |
| Bonus 2 : gain moyen | 546.4 x | 535.8 x | | |
| Fréquence de gain | | 30.39% | | |
| Écart-type | | 18.9 x | | |
| Max win | 10,000 x | 1 tour sur 2,485,065 | | |

## 6. Contrôles

| Contrôle | Valeur | Règle | Statut |
|---|---|---|---|
| RTP exact du jeu de base | 96.183% | cible 96.20% ± 0,20 % | OK |
| RTP simulé (plafond compris) | 96.552% ± 0.996% | écart à l'exact < 3 marges | OK |
| Part des spins (hors bonus) | 63.5% | 55 % à 70 % : les spins rapportent sans tout donner | OK |
| Part du bonus 1 | 29.9% | au plus 30 % : aucun bonus ne donne tout | OK |
| Bonus 1 : fréquence | 1 sur 334 | entre 1/100 et 1/1 000 000 | OK |
| Part du bonus 2 | 6.5% | au plus 30 % : aucun bonus ne donne tout | OK |
| Bonus 2 : fréquence | 1 sur 8,724 | entre 1/100 et 1/1 000 000 | OK |
| Fréquence de gain | 30.4% (1 sur 3.3) | 1 sur 3 à 1 sur 8 (règle d'approbation) | OK |
| Max win atteignable | 1 sur 2,485,065 | au moins 1 sur 20 000 000 (règle d'approbation) | OK |
| 3 étoiles : etl40b (base) | 0.392 | ≤ 0,9 | OK |
| 3 étoiles : cvar (base) | 316 | ≤ 800 | OK |
| Achat bonus 1 : RTP simulé | 95.15% ± 1.34% | à 0,5 % du jeu de base (règle d'approbation) ; corrigé exactement par la pondération | OK |
| Achat bonus 1 : 3 étoiles etl40b | 2.374 | ≤ 0,9 (sinon la pondération réduit la queue) | ÉCHEC |

## 7. Décision
- Statut : **À REVOIR** (Achat bonus 1 : 3 étoiles etl40b)
- Rappel : la validation finale se fait sur les fichiers générés par le SDK (RTP pondéré des books).
