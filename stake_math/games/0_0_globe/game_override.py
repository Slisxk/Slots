"""Surcharges des fonctions génériques du SDK."""

from game_executables import GameExecutables
from src.events.events import fs_trigger_event


class GameStateOverride(GameExecutables):
    """Multi du globe, nombre de FS du bonus buy, conditions de répétition."""

    def reset_book(self):
        super().reset_book()

    def assign_special_sym_function(self):
        self.special_symbol_functions = {self.config.globe_symbol: [self.assign_globe_multiplier]}

    def assign_globe_multiplier(self, symbol) -> None:
        symbol.assign_attribute({"multiplier": self.config.globe_multiplier})

    def update_freespin_amount(self, scatter_key: str = "scatter") -> None:
        """Bonus acheté : nombre de FS fixe (buy.spins). Sinon : table de déclenchement."""
        if self.betmode == "bonus":
            self.tot_fs = self.config.buy_spins
            fs_trigger_event(self, basegame_trigger=True, freegame_trigger=False)
        else:
            super().update_freespin_amount(scatter_key)

    def check_repeat(self) -> None:
        super().check_repeat()
        if self.repeat is False:
            win_criteria = self.get_current_betmode_distributions().get_win_criteria()
            if win_criteria is not None and self.final_win != win_criteria:
                self.repeat = True
                return
            # « basegame » et « freegame » doivent produire un gain non nul
            if win_criteria is None and self.final_win == 0:
                self.repeat = True
