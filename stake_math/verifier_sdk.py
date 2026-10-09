#!/usr/bin/env python3
"""
Vérifie que le simulateur de la feuille (simulateur.py) calcule exactement les mêmes gains
que le math SDK de Stake Engine (Lines.get_lines / Ways.get_ways_data + transformation du globe).

À lancer avec le Python du math SDK, une fois le jeu copié dans <math-sdk>/games/ :

    <math-sdk>/env/bin/python verifier_sdk.py <math-sdk> ../wild_side_school/wild_side_school_math.xlsx

Pour chaque combinaison de modes gérée par le SDK, des grilles aléatoires (avec beaucoup de globes)
sont évaluées des deux côtés et comparées.
"""
import os
import sys

import numpy as np

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ICI, "..", "wild_side_school"))


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    sdk, classeur = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
    game_id = sys.argv[3] if len(sys.argv) > 3 else "0_0_globe"
    n_grilles = int(sys.argv[4]) if len(sys.argv) > 4 else 3000
    sys.path.insert(0, sdk)
    sys.path.insert(0, os.path.join(sdk, "games", game_id))
    os.chdir(sdk)

    import simulateur
    from game_config import GameConfig, PARAMS
    from gamestate import GameState
    from src.calculations.lines import Lines
    from src.calculations.ways import Ways

    p = simulateur.load_params(classeur)
    p["poids_base"][p["types"].index("GLOBE")] = p["poids_base"].sum(axis=0) / 25  # ~1 globe par grille
    config = GameConfig()
    top = PARAMS["top_symbol"]
    pays = {(e["kind"], e["symbol"]): e["pay"] for e in PARAMS["paytable"]}
    ok = True

    for gain, mode in [("LINES", "WILD_ADD"), ("LINES", "GLOBAL_SUM"), ("WAYS", "WILD_MULT"), ("WAYS", "GLOBAL_SUM")]:
        # Reconfigure le jeu SDK pour cette combinaison
        config.win_type = gain.lower()
        config.multi_mode = mode
        config.wild_multis = mode != "GLOBAL_SUM"
        config.mult_symbol = "W" if config.wild_multis else "MX"
        config.paytable = dict(pays)
        if gain == "LINES" and config.wild_multis:
            for k in (3, 4, 5):
                if (k, top) in pays:
                    config.paytable[(k, "W")] = pays[(k, top)]
        config.special_symbols = {
            "wild": ["W", config.globe_symbol] if config.wild_multis else [],
            "scatter": [config.scatter_symbol],
            "multiplier": [config.mult_symbol, config.globe_symbol],
            "globe": [config.globe_symbol],
        }
        gs = GameState(config)

        p["mode_gain"], p["mode"] = gain, mode
        m = simulateur.Moteur(p, np.random.default_rng(7))
        grid = m._tirage(n_grilles, "base")
        globe, voisin, mult = m.transformer(grid, "base")
        notre = m.evaluer(grid, globe | voisin, mult).sum(axis=1)

        ecarts = 0
        for i in range(n_grilles):
            board = [[None] * p["rows"] for _ in range(5)]
            for reel in range(5):
                for row in range(p["rows"]):
                    if voisin[i, row, reel]:
                        s = gs.create_symbol(config.mult_symbol)
                        s.assign_attribute({"multiplier": float(mult[i, row, reel])})
                    else:
                        s = gs.create_symbol(p["codes"][grid[i, row, reel]])
                    board[reel][row] = s
            gs.board = board
            if config.wild_multis:
                strat, gm = "symbol", 1
            else:
                strat, gm = "global", gs.board_multiplier()
            if gain == "LINES":
                sdk_win = Lines.get_lines(board, config, multiplier_method=strat, global_multiplier=gm)["totalWin"]
            else:
                sdk_win = Ways.get_ways_data(config, board, global_multiplier=gm,
                                             multiplier_strategy=strat)["totalWin"]
            if abs(sdk_win - notre[i]) > 0.011 * max(1, len(config.paylines)):
                ecarts += 1
                if ecarts <= 3:
                    print(f"  écart grille {i}: SDK {sdk_win} / feuille {notre[i]:.4f}")
        avec_globe = int((globe | voisin).any(axis=(1, 2)).sum())
        etat = "OK" if ecarts == 0 else f"{ecarts} ÉCARTS"
        ok &= ecarts == 0
        print(f"{gain:5} + {mode:10} : {n_grilles} grilles ({avec_globe} avec globe), "
              f"gain total SDK = feuille -> {etat}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
