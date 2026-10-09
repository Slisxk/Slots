"""Génère les books, optimise le RTP, produit les statistiques et vérifie le format.

    python games/<game_id>/run.py            (depuis la racine du math-sdk)
    python games/<game_id>/run.py --test     (petit essai rapide, sans optimisation)
    python games/<game_id>/run.py --books 200000   (nombre de résultats par mode, 100 000 par défaut)
    python games/<game_id>/run.py --optimiseur     (optimiseur Rust du SDK au lieu de la pondération
                                                    naturelle ; il peut déformer la distribution des gains)
"""

import os
import sys

from gamestate import GameState
from game_config import GameConfig
from game_config import PARAMS
from game_optimization import OptimizationSetup
from ponderation import ponderer
from optimization_program.run_script import OptimizationExecution
from utils.game_analytics.run_analysis import create_stat_sheet
from utils.rgs_verification import execute_all_tests
from src.state.run_sims import create_books
from src.write_data.write_configs import generate_configs

if __name__ == "__main__":
    test = "--test" in sys.argv
    optimiseur_sdk = "--optimiseur" in sys.argv
    books = int(sys.argv[sys.argv.index("--books") + 1]) if "--books" in sys.argv else int(1e5)

    num_threads = max(1, min(10, os.cpu_count() or 1))
    rust_threads = max(1, (os.cpu_count() or 1) * 2)
    batching_size = 5000
    compression = True
    profiling = False

    # Nombre de résultats (books) par mode. Pour la publication, monte à 1e5 ou plus.
    num_sim_args = {
        "base": int(2e3) if test else books,
        "bonus": int(2e3) if test else books,
    }

    run_conditions = {
        "run_sims": True,
        "run_optimization": not test,
        "run_analysis": not test,
        "run_format_checks": not test,
    }
    target_modes = list(num_sim_args.keys())

    config = GameConfig()
    gamestate = GameState(config)
    if run_conditions["run_optimization"] or run_conditions["run_analysis"]:
        optimization_setup_class = OptimizationSetup(config)

    if run_conditions["run_sims"]:
        create_books(gamestate, config, num_sim_args, batching_size, num_threads, compression, profiling)

    generate_configs(gamestate)

    if run_conditions["run_optimization"]:
        if optimiseur_sdk:
            OptimizationExecution().run_all_modes(config, target_modes, rust_threads)
        else:
            ponderer(config, PARAMS)   # garde la distribution naturelle des gains (voir ponderation.py)
        generate_configs(gamestate)

    if run_conditions["run_analysis"]:
        create_stat_sheet(gamestate, custom_keys=[{"symbol": "scatter"}])

    if run_conditions["run_format_checks"]:
        execute_all_tests(config)
