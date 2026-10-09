"""Cibles de l'optimiseur (Rust). Les parts de RTP viennent de params.json["targets"],
c'est-à-dire de la simulation de la feuille de calcul."""

from optimization_program.optimization_config import (
    ConstructScaling,
    ConstructParameters,
    ConstructConditions,
    ConstructFenceBias,
    verify_optimization_input,
)
from game_config import PARAMS


class OptimizationSetup:
    """Paramètres d'optimisation pour les modes base et bonus."""

    def __init__(self, game_config):
        self.game_config = game_config
        t = PARAMS["targets"]
        wincap = game_config.wincap
        rtp = game_config.rtp

        self.game_config.opt_params = {
            "base": {
                "conditions": {
                    "wincap": ConstructConditions(
                        rtp=t["wincap_rtp"], av_win=wincap, search_conditions=wincap
                    ).return_dict(),
                    "0": ConstructConditions(rtp=0, av_win=0, search_conditions=0).return_dict(),
                    "freegame": ConstructConditions(
                        rtp=t["freegame_rtp"], hr=t["freegame_hr"], search_conditions={"symbol": "scatter"}
                    ).return_dict(),
                    "basegame": ConstructConditions(hr=t["basegame_hr"], rtp=t["basegame_rtp"]).return_dict(),
                },
                "scaling": ConstructScaling([]).return_dict(),
                "parameters": ConstructParameters(
                    num_show=5000,
                    num_per_fence=10000,
                    min_m2m=4,
                    max_m2m=8,
                    pmb_rtp=1.0,
                    sim_trials=5000,
                    test_spins=[50, 100, 200],
                    test_weights=[0.3, 0.4, 0.3],
                    score_type="rtp",
                ).return_dict(),
                "distribution_bias": ConstructFenceBias(
                    applied_criteria=["basegame"],
                    bias_ranges=[(2.0, 3.0)],
                    bias_weights=[0.5],
                ).return_dict(),
            },
            "bonus": {
                "conditions": {
                    "wincap": ConstructConditions(
                        rtp=t["wincap_rtp"], av_win=wincap, search_conditions=wincap
                    ).return_dict(),
                    "freegame": ConstructConditions(rtp=round(rtp - t["wincap_rtp"], 5), hr="x").return_dict(),
                },
                "scaling": ConstructScaling([]).return_dict(),
                "parameters": ConstructParameters(
                    num_show=5000,
                    num_per_fence=10000,
                    min_m2m=4,
                    max_m2m=8,
                    pmb_rtp=1.0,
                    sim_trials=5000,
                    test_spins=[10, 20, 50],
                    test_weights=[0.6, 0.2, 0.2],
                    score_type="rtp",
                ).return_dict(),
                "distribution_bias": ConstructFenceBias(
                    applied_criteria=["freegame"],
                    bias_ranges=[(game_config.buy_cost * 2, game_config.buy_cost * 4)],
                    bias_weights=[0.3],
                ).return_dict(),
            },
        }

        verify_optimization_input(self.game_config, self.game_config.opt_params)
