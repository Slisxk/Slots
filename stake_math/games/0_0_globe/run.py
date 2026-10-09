"""Génère les books, les pondère (pondération naturelle), produit les statistiques et vérifie le format.

    python games/<game_id>/run.py            (depuis la racine du math-sdk)
    python games/<game_id>/run.py --test     (petit essai rapide, sans pondération ni statistiques)
    python games/<game_id>/run.py --books 200000   (nombre de résultats par mode, 100 000 par défaut)
    python games/<game_id>/run.py --modes base,boost   (seulement ces modes)
"""

import os
import sys

from gamestate import GameState
from game_config import GameConfig
from game_config import PARAMS
from ponderation import ponderer
from utils.game_analytics.retrieve_game_information import GameInformation
from utils.game_analytics.print_all_results import PrintJSON
from utils.rgs_verification import execute_all_tests
from src.state.run_sims import create_books
from src.write_data.write_configs import generate_configs

if __name__ == "__main__":
    test = "--test" in sys.argv
    books = int(sys.argv[sys.argv.index("--books") + 1]) if "--books" in sys.argv else int(1e5)

    num_threads = max(1, min(10, os.cpu_count() or 1))
    batching_size = 5000
    compression = True
    profiling = False

    config = GameConfig()
    gamestate = GameState(config)
    modes = [m.get_name() for m in config.bet_modes]
    if "--modes" in sys.argv:
        modes = sys.argv[sys.argv.index("--modes") + 1].split(",")

    # Nombre de résultats (books) par mode. Pour la publication, 1e5 ou plus.
    num_sim_args = {m: int(2e3) if test else books for m in modes}

    create_books(gamestate, config, num_sim_args, batching_size, num_threads, compression, profiling)
    generate_configs(gamestate)

    if not test:
        # Poids des résultats : distribution naturelle du jeu, RTP exact, limites « 3 étoiles »
        ponderer(config, PARAMS, modes)
        generate_configs(gamestate)
        # Statistiques (library/statistics_summary.json). Le classeur xlsx du SDK n'est pas produit :
        # il dépend des « fences » de l'optimiseur Rust, qui n'est pas utilisé ici.
        PrintJSON(GameInformation(gamestate, custom_keys=[{"symbol": "scatter"}, {"symbol": "bonus"}]))
        execute_all_tests(config)
