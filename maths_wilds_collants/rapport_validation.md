# Rapport de validation des maths

Contrôles repris de la doc et du math SDK officiels de Stake Engine (github.com/engineio).

## 1. Périmètre
- Classeur : `classeur_maths.xlsx` (empreinte 691e2a0b5d4d)
- Date : 2026-11-03 15:09
- Grille : 5 rouleaux x 4 lignes (1,024 ways), symboles géants de 1 à 3 cases

## 2. Décomposition du RTP

| Composante | Fréquence | Gain moyen | RTP |
|---|---|---|---|
| Spins du jeu de base (calcul exact sur toutes les positions des bandes) | chaque spin | 0.6004 x | 60.035% |
| Bonus 1 « Free spins » (wilds MARCHE) | 1 sur 305 (exact) | 92.5 x (simulé) | 30.338% |
| Bonus 2 « Super free spins » (wilds FIXE) | 1 sur 7,683 (exact) | 449.1 x (simulé) | 5.846% |
| **Total estimé** | | | **96.219%** |

## 3. Simulation complète
- 2,113,181 spins de base (strates du nombre de scatters), graine 2026
- RTP simulé 95.811% ± 0.880% ; fréquence de gain 32.25% ; écart-type 20.5x
- Max win : 1 tour sur 1,685,591

## 4. Contrôles

| Contrôle | Valeur | Règle | Statut |
|---|---|---|---|
| RTP estimé (spins exacts + bonus simulés) | 96.219% | entre 96.00% et 96.50% (ta règle ; SDK : 96,0 à 96,7 %) | OK |
| RTP simulé (plafond compris) | 95.811% ± 0.880% | écart à l'estimation < 3 marges | OK |
| Part des spins (hors bonus) | 62.4% | 55% à 70% : les spins rapportent sans tout donner | OK |
| Part du bonus 1 | 31.5% | au plus 35% : aucun bonus ne donne tout | OK |
| Bonus 1 : fréquence | 1 sur 305 | entre 1/100 et 1/1 000 000 | OK |
| Part du bonus 2 | 6.1% | au plus 35% : aucun bonus ne donne tout | OK |
| Bonus 2 : fréquence | 1 sur 7,683 | entre 1/100 et 1/1 000 000 | OK |
| Fréquence de gain | 32.2% (1 sur 3.1) | 1 sur 3 à 1 sur 8 (checklist) ; jamais moins de 1 sur 20 (doc) | OK |
| Max win atteignable | 1 sur 1,685,591 | plus fréquent que 1 sur 10 000 000 (doc « Math Requirements ») | OK |
| Écart-type du jeu de base | 20.5x | au moins 0,6 (soumission SDK) | OK |
| Contrôles de risque Studio (base) | tous OK | RISK_CHECKS du SDK : chaque échec baisse la mise max autorisée | OK |
| Achat bonus 1 : RTP simulé | 95.71% ± 0.66% | à 0,5 % du jeu de base (doc) ; la pondération du SDK le règle exactement | OK |
| Achat bonus 1 : prix | 97x | 500x au plus pour garder la mise maximale de 1 000 $ (math SDK) | OK |
| Achat bonus 1 : contrôles de risque Studio | tous OK | RISK_CHECKS du SDK ; sinon la pondération rend les plus gros gains de ce mode plus rares | OK |
| Achat bonus 2 : RTP simulé | 96.64% ± 0.68% | à 0,5 % du jeu de base (doc) ; la pondération du SDK le règle exactement | OK |
| Achat bonus 2 : prix | 465x | 500x au plus pour garder la mise maximale de 1 000 $ (math SDK) | OK |
| Achat bonus 2 : contrôles de risque Studio | tous OK | RISK_CHECKS du SDK ; sinon la pondération rend les plus gros gains de ce mode plus rares | OK |

## 5. Décision
- Statut : **VALIDÉ**
- La validation finale se fait sur les fichiers générés par le SDK (RTP pondéré des books).
