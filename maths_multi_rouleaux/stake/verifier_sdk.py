#!/usr/bin/env python3
"""
Vérifie que le simulateur du classeur et le jeu du math SDK donnent les mêmes résultats.

    <math-sdk>/env/bin/python verifier_sdk.py <math-sdk> ../classeur_maths.xlsx [game_id] [nb_grilles]

1. Gains exacts : grilles aléatoires + multis de colonne aléatoires, évalués par le simulateur
   (Moteur.gains) et par le SDK (Ways.get_ways_data + evaluate_ways du jeu) : même gain à 0,01 près.
2. Sessions de chaque bonus (collant ou non) jouées par le SDK (bandes exportées) : gain moyen
   comparé au calcul exact du classeur (écart en sigmas).
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
    game_id = sys.argv[3] if len(sys.argv) > 3 else "0_0_colonnes"
    n = int(sys.argv[4]) if len(sys.argv) > 4 else 3000
    sys.path.insert(0, sdk)
    sys.path.insert(0, os.path.join(sdk, "games", game_id))
    os.chdir(sdk)
    import simulateur
    from game_config import GameConfig
    from gamestate import GameState

    p = simulateur.load_params(classeur)
    config = GameConfig()
    gs = GameState(config)
    ok = True

    # ---- 1. gains exacts
    m = simulateur.Moteur(p, np.random.default_rng(5))
    g = m.tirage(n, "fs1")
    cols = m.multis(n, "fs1") + m.multis(n, "fs1")        # parfois 2 multis cumulés (comme en collant)
    notre, _ = m.gains(g, cols)
    ecarts = 0
    for i in range(n):
        gs.board = [[gs.create_symbol(p["codes"][g[i, row, reel]]) for row in range(p["rows"])] for reel in range(p["R"])]
        gs.columns = [float(x) for x in cols[i]]
        gs.columns = [int(x) if x.is_integer() else x for x in gs.columns]
        from src.calculations.ways import Ways
        data = Ways.get_ways_data(config, gs.board)
        sdk_win = sum(round(w["win"] * gs.column_multiplier(w["kind"]), 2) for w in data["wins"])
        if abs(sdk_win - notre[i]) > 0.011 * (1 + len(data["wins"])) + 1e-6 * notre[i]:
            ecarts += 1
            if ecarts <= 3:
                print(f"  écart grille {i}: SDK {sdk_win} / classeur {notre[i]:.4f}")
    ok &= ecarts == 0
    print(f"GAINS EXACTS : {n} grilles avec multis de colonne -> {'OK' if not ecarts else f'{ecarts} ÉCARTS'}")

    # ---- 2. sessions de bonus jouées par le SDK
    e = simulateur.analytique(p)
    gs.betmode, gs.criteria = "base", "basegame"
    for k, b in enumerate(p["bonus"], 1):
        gains = []
        for i in range(max(2000, n // 2)):
            gs.reset_seed(50_000 * k + i)
            gs.reset_book()
            gs.gametype = config.basegame_type
            gs.bonus = k
            gs.tot_fs = b["fs"]
            gs.columns = [0] * p["R"]
            gs.run_freespin()
            gains.append(min(gs.win_manager.freegame_wins, p["max_win"]))
        gains = np.array(gains)
        attendu = e[f"bonus{k}"]["gain"]
        err = gains.std() / np.sqrt(len(gains))
        z = (gains.mean() - attendu) / err
        bon = abs(z) <= 3.5
        ok &= bon
        print(f"BONUS {k} ({'collant' if b['collant'] else 'non collant'}) : SDK {gains.mean():.1f}x sur {len(gains)} sessions"
              f" / exact {attendu:.1f}x (écart {z:+.1f} σ, plafond compris) -> {'OK' if bon else 'ÉCART'}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
