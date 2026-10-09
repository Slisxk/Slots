"""Événement propre au jeu, envoyé au front-end juste après le reveal."""

GLOBE_MULTIPLIERS = "globeMultipliers"


def globe_multipliers_event(gamestate, globes: list, multipliers: dict, board_multiplier=None) -> None:
    """Le front-end affiche le reveal, puis transforme les cases listées ici en multiplicateurs.

    globes       : [{"reel", "row"}] positions des globes
    multipliers  : [{"reel", "row", "multiplier", "symbol"}] cases transformées
    boardMultiplier (GLOBAL_SUM seulement) : multiplicateur appliqué au gain total du spin
    Les lignes sont décalées de +1 quand le padding est actif, comme les événements du SDK.
    """
    pad = 1 if gamestate.config.include_padding else 0
    event = {
        "index": len(gamestate.book.events),
        "type": GLOBE_MULTIPLIERS,
        "globes": [{"reel": r, "row": w + pad, "multiplier": gamestate.config.globe_multiplier}
                   for r, w in globes],
        "multipliers": [
            {"reel": r, "row": w + pad, "multiplier": m, "symbol": gamestate.config.mult_symbol}
            for (r, w), m in multipliers.items()
        ],
    }
    if board_multiplier is not None:
        event["boardMultiplier"] = board_multiplier
    gamestate.book.add_event(event)
