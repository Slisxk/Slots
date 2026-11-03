"""Événement propre au jeu, envoyé juste après le reveal."""

COLUMN_MULTIPLIERS = "columnMultipliers"


def column_multipliers_event(gamestate, new: list, sticky: bool) -> None:
    """new     : [{"reel", "multiplier"}] multis tombés à ce spin (un multi couvre toute la colonne)
    columns : valeur de chaque colonne après ce spin (0 = pas de multi) ; en bonus collant, elle cumule
    sticky  : True si les multis restent jusqu'à la fin du bonus"""
    gamestate.book.add_event({
        "index": len(gamestate.book.events),
        "type": COLUMN_MULTIPLIERS,
        "new": new,
        "columns": list(gamestate.columns),
        "sticky": sticky,
    })
