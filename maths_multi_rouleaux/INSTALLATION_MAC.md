# Utiliser ce dossier sur ton Mac

Ce dossier contient tout : la feuille de maths, le simulateur, le jeu pour le math SDK de Stake Engine, la spec et le prompt pour faire le front-end.

## 1. Ce qu'il faut installer (une seule fois)

Ouvre le Terminal (Applications › Utilitaires › Terminal), puis :

```bash
# Homebrew (gestionnaire de paquets), s'il n'est pas déjà installé
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Python 3.12 et git
brew install python@3.12 git

# Un environnement Python pour le simulateur, avec ses deux bibliothèques
python3.12 -m venv ~/venv-slots
source ~/venv-slots/bin/activate
pip install numpy openpyxl
```

À chaque nouvelle fenêtre de Terminal, réactive l'environnement avec `source ~/venv-slots/bin/activate`.

Pour ouvrir le classeur : **Microsoft Excel** ou **LibreOffice** (gratuit : `brew install --cask libreoffice`). Évite Numbers : il gère mal certaines formules du classeur.

## 2. Régler les maths

1. Ouvre `classeur_maths.xlsx`. Modifie seulement les cellules **bleues sur fond jaune** (Config, Paytable, Poids, Multis). Le **Résumé** se recalcule tout de suite : RTP exact, part des spins et de chaque bonus, contrôles.
2. Enregistre et ferme le classeur, puis lance la simulation dans le Terminal :
   ```bash
   cd chemin/vers/maths_multi_rouleaux     # astuce : tape « cd » puis glisse le dossier dans le Terminal
   python simulateur.py classeur_maths.xlsx            # ≈ 5 min
   python simulateur.py classeur_maths.xlsx --exact    # calcul exact seulement, instantané
   ```
   Les résultats s'écrivent dans l'onglet **Simulation** et dans `rapport_validation.md`.

Tu n'as rien à changer si tu gardes les maths telles quelles : elles sont déjà calées (96,20 %) et validées.

## 3. Générer les fichiers à publier sur Stake Engine

```bash
# Le math SDK officiel, à côté de ce dossier
cd chemin/vers/le/dossier/parent
git clone https://github.com/engineio/math-sdk.git
cd math-sdk && make setup PYTHON=python3.12 && env/bin/pip install openpyxl && cd ..

# Exporter le jeu, le copier dans le SDK, vérifier, générer
python maths_multi_rouleaux/stake/exporter.py maths_multi_rouleaux/classeur_maths.xlsx --nom "Mon Jeu"
cp -R maths_multi_rouleaux/stake/games/0_0_colonnes math-sdk/games/
math-sdk/env/bin/python maths_multi_rouleaux/stake/verifier_sdk.py math-sdk maths_multi_rouleaux/classeur_maths.xlsx
cd math-sdk && env/bin/python games/0_0_colonnes/run.py --books 100000
```

- `verifier_sdk.py` doit afficher « OK » partout : le SDK et le classeur donnent les mêmes gains.
- `run.py` prend un moment (il fabrique 100 000 tours par mode). À la fin, il doit afficher « Risk checks: 6 of 6 pass » et aucun message « Studio won't accept this math ».
- Les fichiers à déposer sur Stake Engine sont dans `math-sdk/games/0_0_colonnes/library/publish_files/` : `index.json`, et pour chaque mode (`base`, `bonus`, `super`) un `books_<mode>.jsonl.zst` et un `lookUpTable_<mode>_0.csv`.
- La config du front-end est dans `math-sdk/games/0_0_colonnes/library/configs/config_fe_0_0_colonnes.json`.

Si tu changes le nom ou l'identifiant du jeu (`--game-id 12_3_monjeu`), remplace `0_0_colonnes` par cet identifiant dans les commandes.

## 4. Faire le front-end

Ouvre une nouvelle conversation (Claude Code sur ton Mac, dans un dossier vide pour le jeu), colle le contenu de `PROMPT_SLOT.md`, et joins :
1. `SPEC_MATHS.md` ;
2. `config_fe_0_0_colonnes.json` ;
3. si tu les as générés, les fichiers `books_*.jsonl.zst` pour tester avec de vrais tours.

Le front-end se fait avec le web SDK officiel (Node 22) : https://github.com/engineio/web-sdk.
