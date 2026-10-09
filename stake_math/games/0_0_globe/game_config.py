"""Configuration du jeu. Toutes les valeurs viennent de params.json (généré par exporter.py)."""

import json
import os

from src.config.config import Config
from src.config.distributions import Distribution
from src.config.betmode import BetMode

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "params.json"), encoding="utf-8") as f:
    PARAMS = json.load(f)


def _num(k):
    """Clés JSON -> nombres (les multis peuvent être décimaux)."""
    v = float(k)
    return int(v) if v.is_integer() else v


class GameConfig(Config):
    """Grille 5 x 5 (clusters + cascades, ou lignes / ways), globe qui transforme ses 8 voisins
    en multiplicateurs, free spins avec +N FS par symbole bonus."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        super().__init__()
        p = PARAMS
        self.game_id = p["game_id"]
        self.provider_number = p["provider_number"]
        self.working_name = p["working_name"]
        self.game_name = p["working_name"]
        self.provider_name = p.get("provider_name", "mon_studio")
        self.wincap = float(p["wincap"])
        self.win_type = p["win_type"]  # "cluster", "lines" ou "ways"
        self.cascades = bool(p.get("cascades", False))
        self.rtp = p["rtp"]
        self.construct_paths()

        # Grille
        self.num_reels = p["num_reels"]
        self.num_rows = [p["num_rows"]] * self.num_reels

        # Modes des multiplicateurs (voir readme.txt)
        self.multi_mode = p["multi_mode"]
        self.wild_multis = self.multi_mode in ("WILD_ADD", "WILD_MULT")
        self.scatter_symbol = p["scatter"]
        self.globe_symbol = p["globe"]
        self.globe_multiplier = _num(p["globe_multiplier"])
        # Symbole posé autour du globe : wild multiplicateur (W) ou multiplicateur simple (MX)
        self.mult_symbol = "W" if self.wild_multis else "MX"

        self.paytable = {(e["kind"], e["symbol"]): e["pay"] for e in p["paytable"]}
        if self.win_type == "lines" and self.wild_multis:
            # Une ligne 100 % wild paie comme le symbole le plus fort
            for k in (3, 4, 5):
                if (k, p["top_symbol"]) in self.paytable:
                    self.paytable[(k, "W")] = self.paytable[(k, p["top_symbol"])]

        if self.win_type == "lines":
            self.paylines = {i + 1: line for i, line in enumerate(p["paylines"])}
        self.include_padding = True

        wilds = ["W", self.globe_symbol] if self.wild_multis else []
        self.special_symbols = {
            "wild": wilds,
            "scatter": [self.scatter_symbol],
            "multiplier": [self.mult_symbol, self.globe_symbol],
            "globe": [self.globe_symbol],
        }

        fs_k = p["fs_per_scatter_in_fs"]
        n_cases = self.num_reels * p["num_rows"]
        seuils = sorted((int(k), int(v)) for k, v in p["fs_triggers_base"].items())
        base_table = {}
        for n in range(seuils[0][0], n_cases + 1):   # le dernier seuil vaut « et plus » (cascades)
            base_table[n] = [v for k, v in seuils if k <= n][-1]
        self.freespin_triggers = {
            self.basegame_type: base_table,
            # Pendant les FS : chaque symbole bonus ajoute fs_k free spins
            self.freegame_type: {n: n * fs_k for n in range(1, n_cases + 1)},
        }
        self.anticipation_triggers = {
            self.basegame_type: min(self.freespin_triggers[self.basegame_type].keys()) - 1,
            self.freegame_type: self.num_reels + 1,  # pas d'anticipation pendant les FS
        }
        self.buy_cost = float(p["buy"]["cost"])
        self.buy_spins = int(p["buy"]["spins"])

        # Bandes de rouleaux
        reels = {"BR0": "BR0.csv", "FR0": "FR0.csv", "WCAP": "FRWCAP.csv"}
        self.reels = {}
        for r, f in reels.items():
            self.reels[r] = self.read_reels_csv(os.path.join(self.reels_path, f))
        # Bandes courtes pour l'animation des rouleaux côté front-end (config_fe uniquement)
        pad = {g: os.path.join(self.reels_path, f) for g, f in
               ((self.basegame_type, "PAD_BR.csv"), (self.freegame_type, "PAD_FR.csv"))}
        self.padding_reels[self.basegame_type] = (
            self.read_reels_csv(pad[self.basegame_type]) if os.path.exists(pad[self.basegame_type]) else self.reels["BR0"])
        self.padding_reels[self.freegame_type] = (
            self.read_reels_csv(pad[self.freegame_type]) if os.path.exists(pad[self.freegame_type]) else self.reels["FR0"])
        self.padding_symbol_values = {self.globe_symbol: {"multiplier": {self.globe_multiplier: 1}}}

        mult = {g: {_num(k): w for k, w in d.items()} for g, d in p["mult_values"].items()}
        mult_normal = {self.basegame_type: mult["basegame"], self.freegame_type: mult["freegame"]}
        mult_wincap = {self.basegame_type: mult["basegame"], self.freegame_type: mult["wincap"]}
        scatter_natural = {int(k): w for k, w in p["scatter_trigger_weights"].items() if w > 0}
        min_scatter = min(self.freespin_triggers[self.basegame_type].keys())

        freegame_condition = {
            "reel_weights": {self.basegame_type: {"BR0": 1}, self.freegame_type: {"FR0": 1}},
            "scatter_triggers": scatter_natural,
            "mult_values": mult_normal,
            "force_wincap": False,
            "force_freegame": True,
        }
        basegame_condition = {
            "reel_weights": {self.basegame_type: {"BR0": 1}},
            "mult_values": mult_normal,
            "force_wincap": False,
            "force_freegame": False,
        }
        zerowin_condition = dict(basegame_condition)
        wincap_condition = {
            "reel_weights": {self.basegame_type: {"BR0": 1}, self.freegame_type: {"FR0": 1, "WCAP": 5}},
            "scatter_triggers": {k: w for k, w in scatter_natural.items() if k > min_scatter} or scatter_natural,
            "mult_values": mult_wincap,
            "force_wincap": True,
            "force_freegame": True,
        }
        # Bonus buy : on force le nombre minimum de symboles bonus, le nombre de FS vient de buy.spins
        buy_condition = dict(freegame_condition, scatter_triggers={min_scatter: 1})
        buy_wincap_condition = dict(wincap_condition, scatter_triggers={min_scatter: 1})

        self.bet_modes = [
            BetMode(
                name="base",
                cost=1.0,
                rtp=self.rtp,
                max_win=self.wincap,
                auto_close_disabled=False,
                is_feature=True,
                is_buybonus=False,
                distributions=[
                    Distribution(criteria="wincap", quota=0.001, win_criteria=self.wincap,
                                 conditions=wincap_condition),
                    Distribution(criteria="freegame", quota=0.1, conditions=freegame_condition),
                    Distribution(criteria="0", quota=0.4, win_criteria=0.0, conditions=zerowin_condition),
                    Distribution(criteria="basegame", quota=0.5, conditions=basegame_condition),
                ],
            ),
            BetMode(
                name="bonus",
                cost=self.buy_cost,
                rtp=self.rtp,
                max_win=self.wincap,
                auto_close_disabled=False,
                is_feature=False,
                is_buybonus=True,
                distributions=[
                    Distribution(criteria="wincap", quota=0.001, win_criteria=self.wincap,
                                 conditions=buy_wincap_condition),
                    Distribution(criteria="freegame", quota=0.1, conditions=buy_condition),
                ],
            ),
        ]
