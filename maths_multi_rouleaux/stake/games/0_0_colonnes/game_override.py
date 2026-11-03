"""Surcharges du SDK : choix du bonus, bandes du bonus, multis de colonne (collants ou non)."""

import random

from game_executables import GameExecutables
from game_events import column_multipliers_event
from src.calculations.statistics import get_random_outcome
from src.events.events import fs_trigger_event


class GameStateOverride(GameExecutables):

    def reset_book(self):
        super().reset_book()
        self.bonus = 0
        self.columns = [0] * self.config.num_reels     # multi de chaque colonne (0 = aucun)

    def assign_special_sym_function(self):
        self.special_symbol_functions = {}

    def get_current_distribution_conditions(self) -> dict:
        """Pendant les FS, les bandes sont celles du bonus en cours."""
        conds = super().get_current_distribution_conditions()
        if self.gametype == self.config.freegame_type and getattr(self, "bonus", 0):
            fg = self.config.freegame_type
            conds = dict(conds)
            conds["reel_weights"] = dict(conds["reel_weights"], **{fg: conds["bonus_reels"][self.bonus]})
        return conds

    def bonus_from_scatters(self, count: int) -> int:
        out = 0
        for i, b in sorted(self.config.bonuses.items()):
            if count >= b["scatters"]:
                out = i
        return out

    def update_freespin_amount(self, scatter_key: str = "scatter") -> None:
        """Bonus acheté (mode d'achat) ou selon le nombre de scatters. freeSpinTrigger porte "bonus"."""
        if self.betmode in self.config.buy_modes:
            self.bonus = self.config.buy_modes[self.betmode]
        else:
            self.bonus = self.bonus_from_scatters(self.count_special_symbols(scatter_key))
        self.tot_fs = self.config.bonuses[self.bonus]["spins"]
        self.columns = [0] * self.config.num_reels      # les multis collants repartent de zéro
        fs_trigger_event(self, basegame_trigger=True, freegame_trigger=False)
        self.book.events[-1]["bonus"] = self.bonus
        self.book.events[-1]["sticky"] = bool(self.config.bonuses[self.bonus]["sticky"])
        self.record({"kind": self.bonus, "symbol": "bonus", "gametype": self.gametype})

    def draw_column_multipliers(self) -> None:
        """Chaque colonne peut recevoir un multi. Non collant : les multis du spin précédent disparaissent.
        Collant : un multi reste sur sa colonne et chaque nouveau multi s'ajoute à sa valeur."""
        if self.gametype == self.config.basegame_type:
            cfg, sticky = self.config.col_mult["base"], False
        else:
            cfg, sticky = self.config.col_mult[self.bonus], bool(self.config.bonuses[self.bonus]["sticky"])
        boost = self.config.wincap_activation_boost if self.get_current_distribution_conditions()["force_wincap"] else 1.0
        if not sticky:
            self.columns = [0] * self.config.num_reels
        new = []
        for reel in range(self.config.num_reels):
            if random.random() < min(1.0, cfg["act"][reel] * boost):
                value = get_random_outcome(cfg["values"])
                self.columns[reel] += value
                new.append({"reel": reel, "multiplier": value})
        if new or any(self.columns):
            column_multipliers_event(self, new, sticky)

    def check_repeat(self) -> None:
        super().check_repeat()
        if self.repeat is False:
            win_criteria = self.get_current_betmode_distributions().get_win_criteria()
            if win_criteria is not None and self.final_win != win_criteria:
                self.repeat = True
                return
            if self.criteria == "basegame" and self.final_win == 0:
                self.repeat = True
