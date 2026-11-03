"""Gains en ways du SDK, multipliés par les multis de colonne."""

from src.calculations.ways import Ways
from src.executables.executables import Executables


class GameExecutables(Executables):

    def column_multiplier(self, kind: int) -> float:
        """Multi d'une way de longueur kind : somme des multis des colonnes 1..kind, 1 s'il n'y en a aucun."""
        s = sum(self.columns[:kind])
        return s if s > 0 else 1

    def evaluate_ways(self) -> None:
        self.win_data = Ways.get_ways_data(self.config, self.board)
        total = 0.0
        for w in self.win_data["wins"]:
            m = self.column_multiplier(w["kind"])
            w["win"] = round(w["win"] * m, 2)
            w["meta"]["columnMult"] = m
            w["meta"]["globalMult"] = m
            total += w["win"]
        self.win_data["totalWin"] = round(total, 2)
        if self.win_data["totalWin"] > 0:
            Ways.record_ways_wins(self)
            self.win_manager.update_spinwin(self.win_data["totalWin"])
        Ways.emit_wayswin_events(self)
