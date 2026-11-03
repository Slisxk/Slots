"""Gains en ways du SDK : chaque wild compte pour son multi (stratégie « symbol » : les multis se multiplient)."""

from src.calculations.ways import Ways
from src.executables.executables import Executables


class GameExecutables(Executables):

    def evaluate_ways(self) -> None:
        self.win_data = Ways.get_ways_data(self.config, self.board, multiplier_strategy="symbol")
        if self.win_data["totalWin"] > 0:
            Ways.record_ways_wins(self)
            self.win_manager.update_spinwin(self.win_data["totalWin"])
        Ways.emit_wayswin_events(self)
