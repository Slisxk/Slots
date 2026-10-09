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
    en multiplicateurs, 3 bonus (3 / 4 / 5 symboles bonus, le 3e caché), spins boostés, bonus buy."""

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

        # Les bonus : 1 = free spins, 2 = super free spins, 3 = bonus caché (voir params.json["bonuses"])
        self.bonuses = {b["id"]: b for b in p["bonuses"]}
        seuils = sorted((b["scatters"], b["id"]) for b in p["bonuses"])
        n_cases = self.num_reels * p["num_rows"]
        fs_k = p["fs_per_scatter_in_fs"]
        base_table = {}
        for n in range(seuils[0][0], n_cases + 1):   # le dernier seuil vaut « et plus » (cascades)
            base_table[n] = self.bonuses[[i for s, i in seuils if s <= n][-1]]["spins"]
        self.freespin_triggers = {
            self.basegame_type: base_table,
            # Pendant les FS : chaque symbole bonus ajoute fs_k free spins
            self.freegame_type: {n: n * fs_k for n in range(1, n_cases + 1)},
        }
        self.anticipation_triggers = {
            self.basegame_type: seuils[0][0] - 1,
            self.freegame_type: self.num_reels + 1,  # pas d'anticipation pendant les FS
        }

        # Bandes de rouleaux : BR0 (base), BRB (spins boostés), FR1/FR2/FR3 (FS de chaque bonus),
        # WCAP (FS enrichis en globes, seulement pour fabriquer des résultats « max win »)
        self.reels = {}
        for r in ["BR0", "BRB", "WCAP"] + [b["reels"] for b in p["bonuses"]]:
            self.reels[r] = self.read_reels_csv(os.path.join(self.reels_path, f"{'FRWCAP' if r == 'WCAP' else r}.csv"))
        # Bandes courtes pour l'animation des rouleaux côté front-end (config_fe uniquement)
        pad = {g: os.path.join(self.reels_path, f) for g, f in
               ((self.basegame_type, "PAD_BR.csv"), (self.freegame_type, "PAD_FR.csv"))}
        self.padding_reels[self.basegame_type] = (
            self.read_reels_csv(pad[self.basegame_type]) if os.path.exists(pad[self.basegame_type]) else self.reels["BR0"])
        self.padding_reels[self.freegame_type] = (
            self.read_reels_csv(pad[self.freegame_type]) if os.path.exists(pad[self.freegame_type])
            else self.reels[self.bonuses[1]["reels"]])
        self.padding_symbol_values = {self.globe_symbol: {"multiplier": {self.globe_multiplier: 1}}}

        def multis(d):
            return {_num(k): w for k, w in d.items()}

        mult_base = multis(p["mult_values"]["basegame"])
        bonus_mults = {i: multis(b["mult_values"]) for i, b in self.bonuses.items()}
        bonus_reels = {i: {b["reels"]: 1} for i, b in self.bonuses.items()}
        # Max win : bandes enrichies en globes et multis plus forts, pour fabriquer ces résultats rares
        wcap_mults = {i: {v: w * v for v, w in m.items()} for i, m in bonus_mults.items()}
        wcap_reels = {i: {b["reels"]: 1, "WCAP": 5} for i, b in self.bonuses.items()}

        def conditions(base_reels, scatters=None, wincap=False):
            """scatters : {nb de symboles bonus forcés sur la grille de départ: poids} (None = pas de bonus).
            Les bandes et les multis des FS dépendent du bonus obtenu (bonus_reels / bonus_mults, lus par
            game_override.get_current_distribution_conditions)."""
            c = {
                "reel_weights": {self.basegame_type: {base_reels: 1},
                                 self.freegame_type: (wcap_reels if wincap else bonus_reels)[1]},
                "mult_values": {self.basegame_type: mult_base,
                                self.freegame_type: (wcap_mults if wincap else bonus_mults)[1]},
                "bonus_reels": wcap_reels if wincap else bonus_reels,
                "bonus_mults": wcap_mults if wincap else bonus_mults,
                "force_wincap": wincap,
                "force_freegame": scatters is not None,
            }
            if scatters is not None:
                c["scatter_triggers"] = scatters
            return c

        def jeu(nom, cout, base_reels, quotas):
            """Mode de jeu « spin » (base ou boost). Critères : wincap, un critère par bonus (grille de
            départ forcée avec le seuil du bonus ; le bonus obtenu dépend du nombre final de symboles
            bonus, cascades comprises), 0 (perdu) et basegame (gagnant sans bonus)."""
            dist = [Distribution(criteria="wincap", quota=0.001, win_criteria=self.wincap,
                                 conditions=conditions(base_reels, {s: 1 for s, _ in seuils[1:]} or {seuils[0][0]: 1},
                                                       wincap=True))]
            for s, i in seuils:
                dist.append(Distribution(criteria=f"bonus{i}", quota=quotas[i],
                                         conditions=conditions(base_reels, {s: 1})))
            dist += [
                # « 0 » : tours perdants, tous identiques en gain, peu de books suffisent ; « basegame » en
                # demande beaucoup (les rares spins avec globe pèsent lourd dans le RTP)
                Distribution(criteria="0", quota=0.1, win_criteria=0.0, conditions=conditions(base_reels)),
                Distribution(criteria="basegame", quota=round(0.899 - sum(quotas.values()), 4),
                             conditions=conditions(base_reels)),
            ]
            return BetMode(name=nom, cost=cout, rtp=self.rtp, max_win=self.wincap, auto_close_disabled=False,
                           is_feature=True, is_buybonus=False, distributions=dist)

        def achat(nom, i):
            """Bonus buy : le spin de déclenchement a exactement le seuil de symboles bonus du bonus i."""
            s = self.bonuses[i]["scatters"]
            return BetMode(name=nom, cost=float(self.bonuses[i]["buy_cost"]), rtp=self.rtp, max_win=self.wincap,
                           auto_close_disabled=False, is_feature=False, is_buybonus=True,
                           distributions=[
                               Distribution(criteria="wincap", quota=0.001, win_criteria=self.wincap,
                                            conditions=conditions("BR0", {s: 1}, wincap=True)),
                               Distribution(criteria="freegame", quota=0.999, conditions=conditions("BR0", {s: 1})),
                           ])

        quotas = {1: 0.08, 2: 0.06, 3: 0.04}
        self.bet_modes = [jeu("base", 1.0, "BR0", quotas),
                          jeu("boost", float(p["boost"]["cost"]), "BRB", quotas)]
        # Modes d'achat : nom du mode -> bonus acheté
        self.buy_modes = {}
        for i, b in sorted(self.bonuses.items()):
            if b.get("buy_cost"):
                self.buy_modes[b["mode"]] = i
                self.bet_modes.append(achat(b["mode"], i))
