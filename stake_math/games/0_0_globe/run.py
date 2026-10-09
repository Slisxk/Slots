"""Génère les books, optimise le RTP, produit les statistiques et vérifie le format.

    python games/<game_id>/run.py            (depuis la racine du math-sdk)
    python games/<game_id>/run.py --test     (petit essai rapide, sans optimisation)
"""

import os
import sys

from gamestate import GameState
from game_config import GameConfig
from game_optimization import OptimizationSetup
from optimization_program.run_script import OptimizationExecution
from utils.game_analytics.run_analysis import create_stat_sheet
from utils.rgs_verification import execute_all_tests
from src.state.run_sims import create_books
from src.write_data.write_configs import generate_configs

if __name__ == "__main__":
    test = "--test" in sys.argv

    num_threads = max(1, min(10, os.cpu_count() or 1))
    rust_threads = max(1, (os.cpu_count() or 1) * 2)
    batching_size = 5000
    compression = True
    profiling = False

    # Nombre de résultats (books) par mode. Pour la publication, monte à 1e5 ou plus.
    num_sim_args = {
        "base": int(2e3) if test else int(1e5),
        "bonus": int(2e3) if test else int(1e5),
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
        OptimizationExecution().run_all_modes(config, target_modes, rust_threads)
        generate_configs(gamestate)

    if run_conditions["run_analysis"]:
        create_stat_sheet(gamestate, custom_keys=[{"symbol": "scatter"}])

    if run_conditions["run_format_checks"]:
        execute_all_tests(config)
