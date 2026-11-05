Je veux que tu crées les maths d'une nouvelle slot pour Stake Engine, dans un nouveau dossier de mon repo. Le board peut changer, mais la méthode, les cibles et les contrôles des maths doivent être **exactement les mêmes** que pour mes slots précédentes (dossiers `maths_multi_rouleaux/` et `maths_wilds_collants/`).

## Sources à utiliser
Lis-les avant de commencer, et vérifie leur version actuelle : si une règle a changé, applique la nouvelle et dis-le-moi.
- **Math SDK officiel de Stake Engine** : https://github.com/engineio/math-sdk. Regarde en particulier :
  - `verify_lookup_format` ;
  - `SUBMISSION_LIMITS` et `RISK_CHECKS` ;
  - le calcul de la mise maximale ;
  - `Ways` / `Lines` / `Cluster` et les `multiplier_strategy`.
- **Doc Stake Engine** : https://github.com/engineio/docs (RTP, max win, hit rate, books, approbation, mode social).
- **Web SDK** : https://github.com/engineio/web-sdk, pour le format des événements que lira le front-end.
- **Méthode** : https://github.com/egorfedorov/Slot-Casino-Game-Developer-Skills-for-Stake-Engine. Utilise :
  - le RTP théorique, simulé et des books ;
  - la calibration sur au moins 1 million de spins et la validation sur 20 millions ;
  - la fiche de validation.
- **Références de jeux** : les slots de Pragmatic Play et de Valkyrie Studio, pour la fréquence et la valeur des bonus et la taille des multis (Gates of Olympus Super Scatter, The Dog House…). Leurs maths ne sont pas publiques : garde-les comme ordres de grandeur. Ne copie jamais le nom, les personnages ou le look d'un jeu existant.
- **Mes dossiers existants**, s'ils sont accessibles : `maths_multi_rouleaux/` (multis de colonne x2 à x500, collants ou non) et `maths_wilds_collants/` (symboles géants, wilds multiplicateurs collants fixes ou qui avancent). Pars du plus proche de ma nouvelle slot et garde la même structure de fichiers.

## Ma nouvelle slot
- **Board** : [ex. 5×3 / 5×4 / 6×5, ways / lines / cluster / scatter pays — ou « garde celui du modèle »]
- **Feature principale** : [ex. multis de colonne / wilds collants / symboles géants / autre]
- **Bonus 1** : [ex. 3 scatters, 10 free spins, feature non collante]
- **Bonus 2** : [ex. 4 scatters ou plus, 10 free spins, feature collante]
- **Autres idées** : [ce que tu veux en plus]

Si une de mes idées empêche d'atteindre les cibles ci-dessous, dis-le-moi et propose une version qui les respecte.

## Cibles des maths : elles ne changent pas
| | Cible |
|---|---|
| RTP | **96,20 %** dans chaque mode (jamais moins de 96,0 % ni plus de 96,5 %, modes à 0,5 % maximum les uns des autres) |
| Équilibre | Spins ≈ 60 à 65 % du RTP, bonus 1 ≈ 30 %, bonus 2 ≈ 6 %. Aucun bonus ne donne tout, et les spins donnent envie de jouer sans trop donner |
| Bonus 1 | Environ 1 spin sur 300 à 350, gain moyen ≈ 90 à 100× la mise |
| Bonus 2 | Environ 1 spin sur 7 500 à 9 000, gain moyen ≈ 450 à 480× la mise |
| Free spins | 10 par bonus, retrigger 3 scatters = +5 free spins |
| Tours gagnants | ≈ 30 à 33 % (au minimum 1 sur 20) |
| Max win | 10 000×, plus fréquent que 1 tour sur 10 millions (vise 1 sur 1 à 3 millions) |
| Bonus buy | Prix ≈ gain moyen du bonus ÷ 0,962, et **500× au plus** (au-delà, la mise maximale passe sous 1 000 $) |
| Modes Stake | `base` (1×), un mode d'achat par bonus |
| Gains | Tous en multiples de 0,1× (exigence de `verify_lookup_format`) |

## Contrôles obligatoires
- Les `SUBMISSION_LIMITS` et les 6 `RISK_CHECKS` du math SDK, calculés par rapport au prix de chaque mode. Les 6 doivent passer.
- Mise maximale de 1 000 $.
- Écart-type du jeu de base ≥ 0,6.
- Gains des books en entiers multiples de 10, et gains non nuls ≥ 10.
- Simulateur de la feuille et jeu du SDK identiques :
  - mêmes bandes ;
  - mêmes gains sur des milliers de grilles ;
  - même gain moyen des sessions de bonus, à 3,5 σ près.

## Méthode
1. **Le classeur** `classeur_maths.xlsx`, généré par `generer_classeur.py` :
   - réglages dans des cellules bleues, avec des plages nommées : grille, paytable, poids des symboles par phase, valeurs et activation de la feature, bonus, retrigger, RTP cible, max win ;
   - un Résumé avec RTP, part de chaque composante, fréquence et gain moyen des bonus, prix d'achat conseillés et contrôles en vert ou rouge ;
   - des formules exactes quand c'est possible.
2. **Le simulateur** `simulateur.py`, qui lit le classeur :
   - calcul exact des spins quand c'est possible : formules, ou toutes les positions des bandes ;
   - Monte-Carlo stratifié par nombre de scatters ;
   - simulation des sessions de bonus et des achats ;
   - contrôles Stake ;
   - écrit l'onglet Simulation et `rapport_validation.md`.
3. **Calage** : règle d'abord la paytable, les poids et les valeurs de la feature pour atteindre les cibles. Ensuite seulement, fixe les prix d'achat.
4. **Export SDK** dans `stake/` :
   - `exporter.py` (classeur → `games/<id>/`) ;
   - le jeu SDK : `game_config.py`, `game_override.py`, `game_executables.py`, `game_events.py`, `gamestate.py`, `run.py` ;
   - `ponderation.py`, qui calibre les poids des books pour que chaque mode soit à 96,20 % ;
   - `verifier_sdk.py`.
5. **Génère les books** avec le SDK : 20 000 par mode pour tester, 100 000 ou plus pour publier. Vérifie le RTP de chaque mode et les 6 risk checks.

## Pièges déjà rencontrés : évite-les
- **Gains** : arrondis à 0,1×, sinon le SDK refuse les books.
- **Achat à plus de 500×** : ça fait baisser la mise maximale.
- **Pondération des books** :
  - applique les tilts seulement aux books `basegame` ;
  - garde le taux de tours gagnants naturel du classeur ;
  - vérifie le sens de la bissection (`evaluer(x) - cible`).
- **Max win** :
  - prends sa fréquence dans la simulation, jamais pile 1 sur 10 millions ;
  - traite-la comme une probabilité totale (`p_max_total`), pour ne pas compter deux fois les books au max win.
- **`run.py`** : n'appelle que `PrintJSON` pour les statistiques (la feuille xlsx du SDK a besoin de l'optimiseur).
- **Bandes générées au hasard** : graine fixe, et toutes les bandes d'un même jeu de la même longueur. Pour un réglage fin, change la paytable ou les multis plutôt que les poids, qui reconstruisent les bandes.

## Ce que je veux dans le nouveau dossier `maths_[nom]/`
| Fichier | Contenu |
|---|---|
| `README.md` | Le jeu par défaut, le tableau d'équilibre, « Quel fichier prendre » |
| `classeur_maths.xlsx`, `generer_classeur.py`, `simulateur.py`, `rapport_validation.md` | La feuille de maths, réutilisable pour d'autres slots du même type |
| `stake/` | Export, jeu SDK, pondération, vérification |
| `sortie/` | `config_fe_<id>.json` et les statistiques du SDK |
| `SPEC_MATHS.md` | Spec pour le front-end : règles, paytable, feature, bonus, événements et leurs champs, exemples de vrais tours (gain exact), règles d'approbation Stake |
| `PROMPT_PROJET.md` | Le prompt pour le projet qui fera le front-end, avec une section vide « Mes idées pour la slot » à la fin |
| `INSTALLATION_MAC.md` | Installation sur Mac (Python 3.12, venv, math SDK, génération des books) |

## Comment procéder
1. **Avant de coder**, lis les sources et mes dossiers existants. Ensuite, résume-moi :
   - le board et la feature que tu proposes ;
   - comment tu comptes atteindre les cibles ;
   - ce qui change par rapport au modèle de départ.
2. **Construis le classeur et le simulateur**, cale les maths, puis montre-moi le tableau d'équilibre.
3. **Exporte vers le SDK**, génère les books, et montre-moi :
   - RTP par mode ;
   - risk checks ;
   - mise maximale ;
   - résultat de `verifier_sdk.py`.
4. **Écris la doc** : README, SPEC, PROMPT_PROJET, INSTALLATION_MAC.
5. **Commite et pousse** sur ma branche de travail. Ne crée pas de pull request sans que je le demande.

Tout en français, avec des explications simples : je ne suis pas mathématicien.
