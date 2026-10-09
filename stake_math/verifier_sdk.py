#!/usr/bin/env python3
"""
Vérifie que le simulateur de la feuille (simulateur.py) calcule exactement les mêmes gains
que le math SDK de Stake Engine (Lines.get_lines / Ways.get_ways_data + transformation du globe).

À lancer avec le Python du math SDK, une fois le jeu copié dans <math-sdk>/games/ :

    <math-sdk>/env/bin/python verifier_sdk.py <math-sdk> ../modele_maths/modele_maths.xlsx

Pour chaque combinaison de modes gérée par le SDK, des grilles aléatoires (avec beaucoup de globes)
sont évaluées des deux côtés et comparées.
"""
import os
import sys

import numpy as np

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ICI, "..", "modele_maths"))
sys.path.insert(0, ICI)


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
    from src.calculations.cluster import Cluster
    from src.calculations.lines import Lines
    from src.calculations.ways import Ways

    p = simulateur.load_params(classeur)
    p["poids"]["base"][p["types"].index("GLOBE")] = np.round(p["poids"]["base"].sum(axis=0) / 25)  # ~1 globe/grille
    config = GameConfig()
    top = PARAMS["top_symbol"]
    ok = True

    combos = [("CLUSTER", "WILD_ADD"), ("CLUSTER", "GLOBAL_SUM"), ("LINES", "WILD_ADD"),
              ("LINES", "GLOBAL_SUM"), ("WAYS", "WILD_MULT"), ("WAYS", "GLOBAL_SUM")]
    pays_lignes = {(k, c): float(p["pays"][i][k - 3]) for i, c in enumerate(p["codes"])
                   for k in (3, 4, 5) if p["types"][i] == "PAY" and p["pays"][i][k - 3] > 0}
    for gain, mode in combos:
        # Reconfigure le jeu SDK pour cette combinaison
        config.win_type = gain.lower()
        config.paylines = {i + 1: line for i, line in enumerate(p["lignes"].tolist())}
        config.multi_mode = mode
        config.wild_multis = mode != "GLOBAL_SUM"
        config.mult_symbol = "W" if config.wild_multis else "MX"
        if gain == "CLUSTER":
            m0 = simulateur.Moteur(p, np.random.default_rng(0))
            config.paytable = {(k, c): float(m0.pay_taille[i][k]) for i, c in enumerate(p["codes"])
                               for k in range(1, m0.pay_taille.shape[1]) if m0.pay_taille[i][k] > 0}
        else:
            config.paytable = dict(pays_lignes)
        if gain == "LINES" and config.wild_multis:
            for k in (3, 4, 5):
                if (k, top) in pays_lignes:
                    config.paytable[(k, "W")] = pays_lignes[(k, top)]
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
        if gain == "CLUSTER":
            grid = grid.astype(np.int16)
            mult = np.zeros(grid.shape)
            m._activer_globes(grid, mult, np.ones(grid.shape, dtype=bool), "base")
            voisin = grid == simulateur.MULTI
            globe = grid == m.gl
            gains, explose = m._clusters(grid, mult)
            notre = gains.sum(axis=1)
        else:
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
            if gain == "CLUSTER":
                data = Cluster.get_cluster_data(config, board, global_multiplier=gm)
                sdk_win = data["totalWin"]
                sdk_exp = {(q["reel"], q["row"]) for w in data["wins"] for q in w["positions"]}
                nos_exp = {(c, r) for r in range(p["rows"]) for c in range(5) if explose[i, r, c]}
                if sdk_exp != nos_exp:
                    sdk_win = float("nan")   # compté comme écart : cases gagnantes différentes
            elif gain == "LINES":
                sdk_win = Lines.get_lines(board, config, multiplier_method=strat, global_multiplier=gm)["totalWin"]
            else:
                sdk_win = Ways.get_ways_data(config, board, global_multiplier=gm,
                                             multiplier_strategy=strat)["totalWin"]
            if not abs(sdk_win - notre[i]) <= 0.011 * 25:
                ecarts += 1
                if ecarts <= 3:
                    print(f"  écart grille {i}: SDK {sdk_win} / feuille {notre[i]:.4f}")
        avec_globe = int((globe | voisin).any(axis=(1, 2)).sum())
        etat = "OK" if ecarts == 0 else f"{ecarts} ÉCARTS"
        ok &= ecarts == 0
        print(f"{gain:7} + {mode:10} : {n_grilles} grilles ({avec_globe} avec globe), "
              f"gain total SDK = feuille -> {etat}")
    ok &= verifier_cascades(p, config, simulateur, GameState, n_grilles)
    ok &= verifier_globe_garanti(classeur, config, simulateur, GameState, n_grilles)
    sys.exit(0 if ok else 1)


def verifier_cascades(p, config, simulateur, GameState, n_grilles):
    """Cascades : compare statistiquement le SDK (bandes de rouleaux, tumble_board) et la feuille
    (tirage case par case) sur des spins de base complets, globes fréquents, sans free spins."""
    import exporter
    import random
    if not p["cascades"]:
        return True
    p["mode_gain"] = "CLUSTER"
    ok = True
    n_sdk = max(4000, n_grilles * 3)
    # Globe sur ~1 grille sur 4 : assez pour tester les cascades avec multis, sans saturer le max win
    poids_test = p["poids"]["base"].copy()
    poids_test[p["types"].index("GLOBE")] = np.round(poids_test.sum(axis=0) / 100)
    for mode in ("WILD_ADD", "GLOBAL_SUM"):
        p["mode"] = mode
        config.win_type, config.multi_mode = "cluster", mode
        config.wild_multis = mode != "GLOBAL_SUM"
        config.mult_symbol = "W" if config.wild_multis else "MX"
        config.special_symbols = {
            "wild": ["W", config.globe_symbol] if config.wild_multis else [],
            "scatter": [config.scatter_symbol],
            "multiplier": [config.mult_symbol, config.globe_symbol],
            "globe": [config.globe_symbol],
        }
        m0 = simulateur.Moteur(p, np.random.default_rng(0))
        config.paytable = {(k, c): float(m0.pay_taille[i][k]) for i, c in enumerate(p["codes"])
                           for k in range(1, m0.pay_taille.shape[1]) if m0.pay_taille[i][k] > 0}
        # Mêmes poids des deux côtés : bandes construites depuis la feuille (globes fréquents)
        rng = random.Random(1)
        p["poids"]["base"] = poids_test.copy()
        L = int(p["poids"]["base"].sum(axis=0).max())
        sc = p["codes"][p["types"].index("SCATTER")]
        config.reels["TEST"] = [exporter.bande(p["poids"]["base"][:, r], p["codes"], L, p["rows"], sc, rng)
                                for r in range(5)]
        gs = GameState(config)
        gs.betmode, gs.criteria = "base", "basegame"
        conds = gs.get_current_distribution_conditions()
        conds_save = (dict(conds["reel_weights"]), conds.get("mult_values"))
        conds["reel_weights"] = {config.basegame_type: {"TEST": 1}}
        mprob = {float(v): w for v, w in zip(p["multi_val"], p["multi_w"]["base"])}
        conds["mult_values"] = {config.basegame_type: mprob, config.freegame_type: mprob}
        wins = []
        for i in range(n_sdk):
            gs.reset_seed(i)
            gs.reset_book()
            gs.create_board_reelstrips()
            gs.play_board()
            wins.append(gs.win_manager.spin_win)
        conds["reel_weights"], conds["mult_values"] = conds_save
        cap = config.wincap               # le SDK arrête les cascades au max win
        wins = np.minimum(np.array(wins), cap)

        m = simulateur.Moteur(p, np.random.default_rng(11))
        notre = np.minimum(m.spin(200_000, "base")[0], cap)
        diff = wins.mean() - notre.mean()
        err = np.sqrt(wins.var() / len(wins) + notre.var() / len(notre))
        hit_sdk, hit_nous = (wins > 0).mean(), (notre > 0).mean()
        err_hit = np.sqrt(hit_nous * (1 - hit_nous) / len(wins))
        bon = abs(diff) <= 3 * err and abs(hit_sdk - hit_nous) <= 3 * err_hit
        ok &= bon
        print(f"CASCADES {mode:10} : gain moyen SDK {wins.mean():.4f} / feuille {notre.mean():.4f} "
              f"(écart {diff / err:+.1f} σ) ; spins gagnants {hit_sdk:.2%} / {hit_nous:.2%} -> "
              f"{'OK' if bon else 'ÉCART'}")
    return ok


def verifier_globe_garanti(classeur, config, simulateur, GameState, n_grilles):
    """Bonus avec globe garanti : compare statistiquement un free spin du SDK (bandes FRk exportées,
    ensure_globe, cascades) et de la feuille (_tirage avec globe garanti)."""
    p = simulateur.load_params(classeur)          # paramètres réels (pas ceux modifiés pour les tests)
    if p["mode_gain"] != "CLUSTER" or config.win_type != "cluster":
        return True
    ok = True
    for k, b in enumerate(p["bonus"], 1):
        if not b["globe_garanti"]:
            continue
        gs = GameState(config)
        gs.betmode, gs.criteria = "base", "basegame"
        gs.reset_seed(0)
        n_sdk = max(4000, n_grilles * 2)
        wins, globes = [], 0
        for i in range(n_sdk):
            gs.reset_seed(10_000 + i)
            gs.reset_book()
            gs.gametype, gs.bonus = config.freegame_type, k
            gs.draw_board(emit_event=False)
            globes += bool(gs.globe_positions())
            gs.play_board()
            wins.append(gs.win_manager.spin_win)
        cap = config.wincap
        wins = np.minimum(np.array(wins), cap)
        m = simulateur.Moteur(p, np.random.default_rng(13))
        notre = np.minimum(m.spin(100_000, f"fs{k}")[0], cap)
        diff = wins.mean() - notre.mean()
        err = np.sqrt(wins.var() / len(wins) + notre.var() / len(notre))
        bon = abs(diff) <= 3 * err and globes == n_sdk
        ok &= bon
        print(f"GLOBE GARANTI (bonus {k}) : {globes}/{n_sdk} FS SDK avec globe ; gain moyen par FS SDK "
              f"{wins.mean():.2f} / feuille {notre.mean():.2f} (écart {diff / err:+.1f} σ) -> {'OK' if bon else 'ÉCART'}")
    return ok


if __name__ == "__main__":
    main()
