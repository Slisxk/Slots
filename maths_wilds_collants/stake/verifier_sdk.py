#!/usr/bin/env python3
"""
Vérifie que le simulateur du classeur et le jeu du math SDK donnent les mêmes résultats.

    <math-sdk>/env/bin/python verifier_sdk.py <math-sdk> ../classeur_maths.xlsx [game_id] [nb_grilles]

1. Bandes : celles du jeu SDK (reels/*.csv) sont identiques à celles du simulateur.
2. Gains exacts : grilles des bandes avec wilds multiplicateurs, évaluées par le simulateur (Moteur.gains)
   et par le SDK (Ways.get_ways_data, multis des wilds) : même gain à 0,01 près.
3. Sessions de chaque bonus (wilds collants fixes ou qui avancent) jouées par le SDK : gain moyen comparé
   à la simulation du classeur (écart en sigmas).
"""
import os
import sys

import numpy as np

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ICI, ".."))


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    sdk, classeur = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
    game_id = sys.argv[3] if len(sys.argv) > 3 else "0_0_wilds"
    n = int(sys.argv[4]) if len(sys.argv) > 4 else 3000
    sys.path.insert(0, sdk)
    sys.path.insert(0, os.path.join(sdk, "games", game_id))
    os.chdir(sdk)
    import simulateur
    from game_config import GameConfig
    from gamestate import GameState
    from src.calculations.ways import Ways

    p = simulateur.load_params(classeur)
    config = GameConfig()
    gs = GameState(config)
    ok = True

    # ---- 1. bandes identiques
    m = simulateur.Moteur(p, np.random.default_rng(5))
    noms = {"base": "BR0", **{f"fs{k}": f"FR{k}" for k in range(1, len(p["bonus"]) + 1)}}
    pareil = all([p["codes"][x] for x in m.bandes[ph][r]] == list(config.reels[nom][r])
                 for ph, nom in noms.items() for r in range(p["R"]))
    ok &= pareil
    print(f"BANDES : simulateur = SDK -> {'OK' if pareil else 'DIFFÉRENTES'}")

    # ---- 2. gains exacts (beaucoup de wilds : grilles des bandes du bonus 1 + wilds ajoutés)
    rng = np.random.default_rng(9)
    g = m.tirage(n, "fs1")
    wi = p["types"].index("WILD")
    ajout = (rng.random(g.shape) < 0.08)
    ajout[:, :, 0] &= rng.random(ajout[:, :, 0].shape) < 0.3          # quelques wilds au rouleau 1 (wilds qui avancent)
    g = np.where(ajout, wi, g)
    mult = m.multis(g, "fs1")
    notre, _ = m.gains(g, mult)
    ecarts = 0
    for i in range(n):
        board = []
        for r in range(p["R"]):
            col = []
            for w in range(p["rows"]):
                s = gs.create_symbol(p["codes"][g[i, w, r]])
                if g[i, w, r] == wi:
                    s.assign_attribute({"multiplier": int(mult[i, w, r])})
                col.append(s)
            board.append(col)
        sdk_win = Ways.get_ways_data(config, board, multiplier_strategy="symbol")["totalWin"]
        if abs(sdk_win - notre[i]) > 0.011:
            ecarts += 1
            if ecarts <= 3:
                print(f"  écart grille {i}: SDK {sdk_win} / classeur {notre[i]:.2f}")
    ok &= ecarts == 0
    print(f"GAINS EXACTS : {n} grilles avec wilds multiplicateurs -> {'OK' if not ecarts else f'{ecarts} ÉCARTS'}")

    # ---- 3. sessions de bonus jouées par le SDK
    gs.betmode, gs.criteria = "base", "basegame"
    for k, b in enumerate(p["bonus"], 1):
        gains = []
        for i in range(max(2000, n)):
            gs.reset_seed(70_000 * k + i)
            gs.reset_book()
            gs.bonus, gs.sticky, gs.tot_fs = k, {}, b["fs"]
            gs.run_freespin()
            gains.append(min(gs.win_manager.freegame_wins, p["max_win"]))
        gains = np.array(gains)
        ref, _ = simulateur.Moteur(p, np.random.default_rng(100 + k)).sessions(k, 100_000, p["max_win"])
        err = np.sqrt(gains.var() / len(gains) + ref.var() / len(ref))
        z = (gains.mean() - ref.mean()) / err
        bon = abs(z) <= 3.5
        ok &= bon
        print(f"BONUS {k} (wilds {b['wilds']}) : SDK {gains.mean():.1f}x sur {len(gains)} sessions / classeur {ref.mean():.1f}x"
              f" (écart {z:+.1f} σ) -> {'OK' if bon else 'ÉCART'}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
