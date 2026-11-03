#!/usr/bin/env python3
"""
Génère classeur_maths.xlsx : modèle de maths « symboles géants + wilds multiplicateurs collants » (style Dog House).

    python generer_classeur.py                     # écrit classeur_maths.xlsx
    python generer_classeur.py autre.xlsx "W_FS=(20,15,15)"   # surcharge rapide d'une valeur

Le classeur contient les réglages (cellules bleues) et le tableau de bord. Les maths se calculent avec
simulateur.py : RTP exact des spins du jeu de base (toutes les positions des bandes), fréquence exacte des
bonus, bonus à wilds collants simulés, contrôles de Stake Engine. Les résultats s'écrivent dans l'onglet
Simulation et le Résumé se met à jour.
"""
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter as L
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.worksheet.datavalidation import DataValidation

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
import simulateur as SIMU  # noqa: E402

OUT = sys.argv[1] if len(sys.argv) > 1 and "=" not in sys.argv[1] else str(ICI / "classeur_maths.xlsx")

# ============================================================================ valeurs par défaut
NB_ROULEAUX, NB_LIGNES = 5, 4
RMAX = 6
SYMBOLES = [  # code, nom, type, 3, 4, 5, 6 identiques (x mise totale, par way ; multiples de 0,1)
    ("H1", "Premium 1", "PAY", 0.8, 2.0, 8.0, 16.0),
    ("H2", "Premium 2", "PAY", 0.6, 1.7, 4.8, 9.6),
    ("H3", "Premium 3", "PAY", 0.4, 1.2, 3.2, 6.4),
    ("H4", "Premium 4", "PAY", 0.3, 0.8, 2.0, 4.0),
    ("L1", "Bas 1 (A)", "PAY", 0.2, 0.6, 1.2, 2.4),
    ("L2", "Bas 2 (K)", "PAY", 0.2, 0.4, 0.8, 1.6),
    ("L3", "Bas 3 (Q)", "PAY", 0.2, 0.3, 0.6, 1.2),
    ("L4", "Bas 4 (J)", "PAY", 0.1, 0.2, 0.6, 1.2),
    ("L5", "Bas 5 (10)", "PAY", 0.1, 0.2, 0.6, 1.2),
    ("W", "Wild multiplicateur", "WILD", 0, 0, 0, 0),
    ("S", "Scatter", "SCATTER", 0, 0, 0, 0),
]
PAYANTS = [40, 50, 60, 70, 110, 120, 130, 140, 150]
TAILLES = {"H": (0.5, 0.3, 0.2), "L": (0.6, 0.25, 0.15)}   # probabilité d'un bloc de 1, 2, 3 cases
W_BASE, S_BASE = 3, 15
W_FS = (20.9, 17, 15)                       # wilds en free spins : bonus 1, 2, 3
S_FS = 22
BONUS = [  # nom, scatters, FS, wilds (NON / FIXE / MARCHE), prix (vide = non achetable)
    ("Free spins", 3, 10, "MARCHE", 97),
    ("Super free spins", 4, 10, "FIXE", 465),
    (None, None, None, None, None),
]
WILD_VALEURS = [2, 3, 5]
WILD_POIDS = {"base": [70, 30, 0], "fs1": [60.5, 35, 4.5], "fs2": [70, 30, 0], "fs3": [60, 35, 5]}
RETRIG_SCATTERS, RETRIG_FS = 3, 5
RTP_CIBLE, RTP_MIN, RTP_MAX = 0.962, 0.96, 0.965
MAX_WIN = 10_000

for k, v in [a.split("=", 1) for a in sys.argv[1:] if "=" in a]:
    exec(f"{k} = {v}")

N = len(SYMBOLES)
I_W = [s[2] for s in SYMBOLES].index("WILD")
I_S = [s[2] for s in SYMBOLES].index("SCATTER")
PHASES = ["base", "fs1", "fs2", "fs3"]

# ============================================================================ styles
F = "Arial"
f_norm, f_bold = Font(name=F, size=10), Font(name=F, size=10, bold=True)
f_title = Font(name=F, size=14, bold=True, color="1F3B57")
f_sub = Font(name=F, size=11, bold=True, color="1F3B57")
f_in = Font(name=F, size=10, color="0000FF")
f_link = Font(name=F, size=10, color="008000")
f_note = Font(name=F, size=9, italic=True, color="666666")
f_head = Font(name=F, size=10, bold=True, color="FFFFFF")
fill_in = PatternFill("solid", fgColor="FFF2CC")
fill_head = PatternFill("solid", fgColor="1F3B57")
fill_tot = PatternFill("solid", fgColor="E7EEF5")
fill_key = PatternFill("solid", fgColor="FFFF00")
thin = Side(style="thin", color="BFBFBF")
box = Border(left=thin, right=thin, top=thin, bottom=thin)
center = Alignment(horizontal="center", vertical="center")
PCT, NUM, X2 = "0.00%", "#,##0", '0.00"x"'

wb = Workbook()


def put(ws, ref, v, font=f_norm, fmt=None, fill=None, align=None, border=True):
    c = ws[ref]
    c.value = v
    c.font = font
    if fmt:
        c.number_format = fmt
    if fill:
        c.fill = fill
    if align:
        c.alignment = align
    if border:
        c.border = box
    return c


def inp(ws, ref, v, fmt=None):
    return put(ws, ref, v, f_in, fmt, fill_in)


def header(ws, row, col0, labels):
    for i, lbl in enumerate(labels):
        put(ws, f"{L(col0 + i)}{row}", lbl, f_head, fill=fill_head, align=center)


def title(ws, text, sub=None):
    ws["A1"].value, ws["A1"].font = text, f_title
    if sub:
        ws["A2"].value, ws["A2"].font = sub, f_note


def name(n, ref):
    wb.defined_names[n] = DefinedName(n, attr_text=ref)


def widths(ws, d):
    for k, v in d.items():
        ws.column_dimensions[k].width = v


def note(ws, ref, txt):
    put(ws, ref, txt, f_note, border=False)


# ============================================================================ LISEZ-MOI
ws = wb.active
ws.title = "LISEZ-MOI"
title(ws, "Modèle de maths : symboles géants + wilds multiplicateurs collants (style Dog House)")
TXT = [
    ("Le principe", f_sub),
    ("• Grille NB_ROULEAUX x NB_LIGNES (5 x 4 = 1 024 ways par défaut). Gains en ways de gauche à droite : un symbole sur des rouleaux consécutifs à partir du rouleau 1.", None),
    ("• SYMBOLES GÉANTS : sur les bandes, chaque symbole payant forme un bloc de 1, 2 ou 3 cases de haut (onglet Tailles). Un symbole géant compte pour chaque case visible qu'il occupe.", None),
    ("• WILDS MULTIPLICATEURS (pas sur le rouleau 1) : chaque wild porte un multi (x2, x3…). Dans une way, un wild compte pour sa valeur au lieu de 1 : les multis de rouleaux différents se multiplient (comme Dog House).", None),
    ("• BONUS : 3 scatters = bonus 1, 4 scatters = bonus 2… (table dans Config). Mode des wilds de chaque bonus : NON (normaux), FIXE (collants : ils restent à leur place jusqu'à la fin, comme Dog House) ou MARCHE (collants et ils avancent d'un rouleau vers la gauche à chaque free spin, puis sortent).", None),
    ("• Retrigger : RETRIG_SCATTERS scatters ou plus pendant les FS = +RETRIG_FS free spins.", None),
    ("", None),
    ("Comment l'utiliser", f_sub),
    ("1. Modifie uniquement les cellules BLEUES sur fond jaune : Config, Paytable, Tailles, Poids, Wilds.", None),
    ("2. Lance le calcul : python simulateur.py classeur_maths.xlsx --exact (≈ 1 min) pour caler, puis python simulateur.py classeur_maths.xlsx (≈ 10 min) pour valider.", None),
    ("   Le RTP des spins du jeu de base et la fréquence des bonus sont EXACTS (toutes les positions des bandes) ; les bonus à wilds collants sont simulés. Les résultats s'écrivent dans Simulation et le Résumé se met à jour.", None),
    ("3. Quand tout est OK, exporte vers le math SDK de Stake Engine : dossier stake/ (voir README.md et INSTALLATION_MAC.md).", None),
    ("Pour une autre slot : change la grille, les symboles, la paytable, les tailles, les poids, les multis des wilds et jusqu'à 3 bonus. Garde le même ordre de symboles partout.", None),
    ("", None),
    ("Code couleur", f_sub),
    ("Bleu sur fond jaune = saisie · Noir = formule · Vert = lien vers un autre onglet · Fond jaune vif = résultat clé", None),
]
for i, (t, fnt) in enumerate(TXT):
    c = ws.cell(row=3 + i, column=1, value=t)
    c.font = fnt or f_norm
    c.alignment = Alignment(wrap_text=True, vertical="top")
ws.column_dimensions["A"].width = 150

# ============================================================================ Config
ws = wb.create_sheet("Config")
title(ws, "Paramètres généraux", "Cellules bleues sur fond jaune = à modifier.")
header(ws, 4, 1, ["Paramètre", "Valeur", "Notes"])
cfg = [
    ("NB_ROULEAUX", "Nombre de rouleaux", NB_ROULEAUX, NUM, "3 à 6."),
    ("NB_LIGNES", "Nombre de lignes (hauteur)", NB_LIGNES, NUM, "2 à 6."),
    ("NB_WAYS", "Nombre de ways", "=NB_LIGNES^NB_ROULEAUX", NUM, "Calculé."),
    ("RTP_CIBLE", "RTP visé", RTP_CIBLE, PCT, "Le SDK règle le RTP final exactement sur cette valeur (pondération)."),
    ("RTP_MIN", "RTP minimum accepté", RTP_MIN, PCT, "Ta règle : 96 % minimum (le math SDK refuse en dessous de 96,0 %)."),
    ("RTP_MAX", "RTP maximum accepté", RTP_MAX, PCT, "Ta règle : 96,5 % maximum (le math SDK refuse au-dessus de 96,7 %)."),
    ("MAX_WIN", "Max win (x mise)", MAX_WIN, NUM, "Plafond d'un tour. Plus fréquent que 1 sur 10 000 000 (doc Stake)."),
    ("RETRIG_SCATTERS", "Scatters pour un retrigger en FS", RETRIG_SCATTERS, NUM, ""),
    ("RETRIG_FS", "FS ajoutés par un retrigger", RETRIG_FS, NUM, ""),
    ("PART_SPINS_MIN", "Équilibre : part minimum des spins", 0.55, PCT, "Les spins doivent rapporter."),
    ("PART_SPINS_MAX", "Équilibre : part maximum des spins", 0.70, PCT, "Au-delà, les bonus deviennent trop faibles."),
    ("PART_BONUS_MAX", "Équilibre : part maximum d'un bonus", 0.35, PCT, "Aucun bonus ne doit « tout donner »."),
    ("HIT_MIN", "Fréquence de gain minimum", 1 / 8, PCT, "Checklist Stake : 1 tour gagnant sur 3 à 8 (jamais moins de 1 sur 20)."),
    ("HIT_MAX", "Fréquence de gain maximum", 1 / 3, PCT, ""),
    ("LONGUEUR_BANDES", "Longueur des bandes (cases)", 20_000, NUM, "Les bandes sont construites depuis Poids et Tailles."),
    ("SEED_BANDES", "Graine des bandes", 2026, NUM, "Même graine = mêmes bandes."),
    ("SIM_SPINS", "Spins de base simulés", 2_000_000, NUM, "≥ 1 000 000 pour caler, ≥ 20 000 000 pour valider (repo de skills)."),
    ("SIM_BUY", "Tours simulés par bonus", 100_000, NUM, ""),
    ("SIM_SEED", "Graine de la simulation", 2026, NUM, ""),
]
for i, (nm, lbl, v, fmt, nt) in enumerate(cfg):
    r = 5 + i
    put(ws, f"A{r}", lbl)
    if isinstance(v, str) and v.startswith("="):
        put(ws, f"B{r}", v, f_norm, fmt)
    else:
        inp(ws, f"B{r}", v, fmt)
    note(ws, f"C{r}", nt)
    name(nm, f"Config!$B${r}")
r0 = 5 + len(cfg) + 2
put(ws, f"A{r0}", "Les bonus", f_sub, border=False)
header(ws, r0 + 1, 1, ["Nom du bonus (libre)", "Scatters", "FS donnés", "Wilds", "Prix d'achat (x mise)", "Notes"])
BONUS_R0 = r0 + 2
notes_b = ["MARCHE : les wilds restent et avancent d'un rouleau vers la gauche à chaque FS, puis sortent.",
           "FIXE : les wilds restent à leur place jusqu'à la fin du bonus (Dog House). Prix ≤ 500 pour garder la mise max de 1 000 $.",
           "Optionnel : laisse la ligne vide pour 2 bonus seulement."]
for i, row in enumerate(BONUS):
    r = BONUS_R0 + i
    for col, v, fmt in zip("ABCDE", row, (None, NUM, NUM, None, NUM)):
        inp(ws, f"{col}{r}", v, fmt)
    note(ws, f"F{r}", notes_b[i])
name("BONUS", f"Config!$A${BONUS_R0}:$E${BONUS_R0 + 2}")
dv = DataValidation(type="list", formula1='"NON,FIXE,MARCHE"', allow_blank=True)
ws.add_data_validation(dv)
dv.add(f"D{BONUS_R0}:D{BONUS_R0 + 2}")
widths(ws, {"A": 42, "B": 16, "C": 14, "D": 14, "E": 18, "F": 90})

# ============================================================================ Paytable
ws = wb.create_sheet("Paytable")
title(ws, "Paytable (x mise totale, par way)", "Valeurs en multiples de 0,1 (règle du math SDK : gains par pas de 0,1x la mise).")
header(ws, 3, 1, ["Code", "Symbole", "Type", "3 identiques", "4 identiques", "5 identiques", "6 identiques"])
PT0 = 4
for i, s in enumerate(SYMBOLES):
    r = PT0 + i
    for col, v in zip("ABC", s[:3]):
        inp(ws, f"{col}{r}", v)
    for col, v in zip("DEFG", s[3:]):
        if s[2] == "PAY":
            inp(ws, f"{col}{r}", v, X2)
        else:
            put(ws, f"{col}{r}", v, f_norm, X2)
name("SYMBOLES", f"Paytable!$A${PT0}:$G${PT0 + N - 1}")
dvt = DataValidation(type="list", formula1='"PAY,WILD,SCATTER"')
ws.add_data_validation(dvt)
dvt.add(f"C{PT0}:C{PT0 + N - 1}")
note(ws, f"A{PT0 + N + 1}", "Gain = valeur x nombre de ways, où chaque wild compte pour son multi. Exemple : H1 sur 3 rouleaux avec un wild x2 au rouleau 2 et un wild x3 au rouleau 3 = 0,8 x 2 x 3 = 4,8x.")
widths(ws, {"A": 8, "B": 20, "C": 10, "D": 13, "E": 13, "F": 13, "G": 13})

# ============================================================================ Tailles
ws = wb.create_sheet("Tailles")
title(ws, "Symboles géants : hauteur des blocs sur les bandes", "Probabilité qu'un bloc d'un symbole payant fasse 1, 2 ou 3 cases de haut. Wild et scatter : toujours 1 case.")
header(ws, 3, 1, ["Code", "Symbole", "1 case", "2 cases", "3 cases", "Hauteur moyenne"])
for i, s in enumerate(SYMBOLES):
    r = 4 + i
    put(ws, f"A{r}", f"=Paytable!A{PT0 + i}", f_link)
    put(ws, f"B{r}", f"=Paytable!B{PT0 + i}", f_link)
    if s[2] == "PAY":
        for col, v in zip("CDE", TAILLES[s[0][0]]):
            inp(ws, f"{col}{r}", v, PCT)
    else:
        for col, v in zip("CDE", (1, 0, 0)):
            put(ws, f"{col}{r}", v, f_norm, PCT)
    put(ws, f"F{r}", f"=IF(SUM(C{r}:E{r})=0,0,(C{r}+2*D{r}+3*E{r})/SUM(C{r}:E{r}))", f_norm, "0.00")
name("TAILLES", f"Tailles!$A$4:$E${3 + N}")
note(ws, f"A{N + 6}", "Plus de blocs hauts = des symboles géants plus fréquents, des gains plus gros mais un peu plus rares (moins de symboles différents par rouleau).")
widths(ws, {"A": 8, "B": 20, "C": 12, "D": 12, "E": 12, "F": 16})

# ============================================================================ Poids
ws = wb.create_sheet("Poids")
title(ws, "Part des cases de chaque symbole, par rouleau", "Poids = nombre de cases sur 1 000 environ. Les colonnes au-delà de NB_ROULEAUX sont ignorées.")
LBL = {"base": "JEU DE BASE", "fs1": "FREE SPINS DU BONUS 1", "fs2": "FREE SPINS DU BONUS 2", "fs3": "FREE SPINS DU BONUS 3"}
for b_i, ph in enumerate(PHASES):
    t0 = 3 + b_i * (N + 5)
    put(ws, f"A{t0}", LBL[ph], f_sub, border=False)
    header(ws, t0 + 1, 1, ["Code", "Symbole"] + [f"R{k}" for k in range(1, RMAX + 1)] + [""] + [f"P(R{k})" for k in range(1, RMAX + 1)])
    first = t0 + 2
    wv = W_BASE if ph == "base" else W_FS[b_i - 1]
    sv = S_BASE if ph == "base" else S_FS
    for i in range(N):
        r = first + i
        put(ws, f"A{r}", f"=Paytable!A{PT0 + i}", f_link)
        put(ws, f"B{r}", f"=Paytable!B{PT0 + i}", f_link)
        for k in range(RMAX):
            v = PAYANTS[i] if i < len(PAYANTS) else (wv if i == I_W else sv)
            if i == I_W and k == 0:
                v = 0
            inp(ws, f"{L(3 + k)}{r}", v, NUM)
            tc = f"{L(3 + k)}${first + N}"
            put(ws, f"{L(10 + k)}{r}", f"=IF({tc}=0,0,{L(3 + k)}{r}/{tc})", f_norm, PCT)
    t = first + N
    put(ws, f"B{t}", "Total", f_bold, fill=fill_tot)
    for k in range(RMAX):
        put(ws, f"{L(3 + k)}{t}", f"=SUM({L(3 + k)}{first}:{L(3 + k)}{t - 1})", f_bold, NUM, fill_tot)
    name(f"POIDS_{ph.upper()}", f"Poids!$A${first}:$H${t - 1}")
widths(ws, {"A": 8, "B": 20, **{L(c): 8 for c in range(3, 9)}, "I": 2, **{L(c): 9 for c in range(10, 16)}})

# ============================================================================ Wilds
ws = wb.create_sheet("Wilds")
title(ws, "Multis des wilds", "Chaque wild reçoit une valeur tirée selon ces poids. Dans une way, les multis des wilds de rouleaux différents se multiplient.")
noms_ph = ["Jeu de base", "Bonus 1", "Bonus 2", "Bonus 3"]
header(ws, 4, 1, ["Valeur"] + [f"Poids {n}" for n in noms_ph] + [f"P {n}" for n in noms_ph])
M0 = 5
M1 = M0 + len(WILD_VALEURS) - 1
for i, v in enumerate(WILD_VALEURS):
    r = M0 + i
    inp(ws, f"A{r}", v, X2)
    for j, ph in enumerate(PHASES):
        cw, cp = L(2 + j), L(6 + j)
        inp(ws, f"{cw}{r}", WILD_POIDS[ph][i], "0.0")
        put(ws, f"{cp}{r}", f"=IF(${cw}${M1 + 1}=0,0,{cw}{r}/${cw}${M1 + 1})", f_norm, PCT)
put(ws, f"A{M1 + 1}", "Total", f_bold, fill=fill_tot)
put(ws, f"A{M1 + 2}", "Multi moyen", f_bold, fill=fill_tot)
for j in range(4):
    cw, cp = L(2 + j), L(6 + j)
    put(ws, f"{cw}{M1 + 1}", f"=SUM({cw}{M0}:{cw}{M1})", f_bold, "0.0", fill_tot)
    put(ws, f"{cp}{M1 + 2}", f"=SUMPRODUCT($A${M0}:$A${M1},{cp}{M0}:{cp}{M1})", f_bold, X2, fill_key)
name("WILD_MULTIS", f"Wilds!$A${M0}:$E${M1}")
note(ws, f"A{M1 + 4}", "Ajoute des lignes de valeurs en dessous si besoin (et étends la plage nommée WILD_MULTIS). Avec des wilds collants, garde des petites valeurs : les multis s'accumulent sur plusieurs rouleaux.")
widths(ws, {"A": 12, **{L(c): 14 for c in range(2, 10)}})

# ============================================================================ Simulation
ws = wb.create_sheet("Simulation")
title(ws, "Résultats du calcul (écrits par simulateur.py — ne pas saisir ici)", "python simulateur.py classeur_maths.xlsx")
header(ws, 4, 1, ["Jeu de base", "Valeur"])
for key in SIMU.LIGNES_SIM:
    r = SIMU.SIM_LIGNE[key]
    put(ws, f"A{r}", SIMU.LIBELLES_SIM[key])
    fmt = {"spins": NUM, "estimation": "0.000%", "spins_exact": "0.000%", "rtp": "0.000%", "marge": "0.000%",
           "rtp_spins": PCT, "hit": PCT, "ecart_type": "0.00", "mediane": X2, "max": X2, "p_max": "0.0000000%",
           "etl40b": "0.000", "etl10k": "0.000", "cvar": "0.0"}.get(key) or (
        "0.000000%" if key.startswith("freq") else PCT if key.startswith("rtp_bonus") else X2 if key.startswith("gain") else "0.00")
    put(ws, f"B{r}", None, f_norm, fmt)
header(ws, SIMU.SIM_A0, 1, ["Chaque bonus joué comme un achat", "Bonus 1", "Bonus 2", "Bonus 3"])
for key in SIMU.LIGNES_ACHAT:
    r = SIMU.SIM_LIGNE["a_" + key]
    put(ws, f"A{r}", SIMU.LIBELLES_ACHAT[key])
    fmt = {"sessions": NUM, "prix": NUM, "rtp": PCT, "marge": PCT, "prix_conseille": "0", "fs_moyens": "0.0",
           "p_max": "0.0000%", "etl40b": "0.000", "etl10k": "0.000", "cvar": "0.0"}.get(key, X2)
    for col in "BCD":
        put(ws, f"{col}{r}", None, f_norm, fmt)
header(ws, SIMU.SIM_C0, 1, ["Contrôle", "Valeur", "Règle", "Statut"])
put(ws, "F4", "Distribution des gains (jeu de base)", f_head, fill=fill_head)
put(ws, "G4", "% des tours", f_head, fill=fill_head)
for i in range(10):
    put(ws, f"F{5 + i}", None)
    put(ws, f"G{5 + i}", None, f_norm, "0.0000%")
widths(ws, {"A": 50, "B": 24, "C": 52, "D": 22, "E": 2, "F": 22, "G": 14})
SIM = lambda key: f"Simulation!{SIMU.cellule(key)}"
SIMA = lambda key, k: f"Simulation!{'BCD'[k - 1]}{SIMU.SIM_LIGNE['a_' + key]}"

# ============================================================================ Résumé
ws = wb.create_sheet("Résumé", 1)
title(ws, "Résumé : RTP et équilibre", "Mis à jour par simulateur.py (onglet Simulation).")
header(ws, 4, 1, ["Composante", "Fréquence", "Gain moyen", "FS joués", "RTP apporté", "Part du RTP", "Achat : prix", "RTP de l'achat", "Prix conseillé"])
put(ws, "A5", "Spins du jeu de base (calcul exact)", f_bold)
put(ws, "B5", "chaque spin")
put(ws, "C5", f"={SIM('spins_exact')}", f_link, "0.0000")
put(ws, "E5", f"={SIM('spins_exact')}", f_bold, PCT)
for k in range(3):
    r = 6 + k
    bk = BONUS_R0 + k
    act = f"ISNUMBER(Config!$B${bk})"
    put(ws, f"A{r}", f'=IF({act},"Bonus {k + 1} : "&Config!A{bk}&" (wilds "&LOWER(Config!D{bk})&")","Bonus {k + 1} : non utilisé")')
    put(ws, f"B{r}", f"=IF({act},{SIM(f'freq{k + 1}')},0)", f_link, "0.000000%")
    put(ws, f"C{r}", f"=IF({act},{SIM(f'gain{k + 1}')},0)", f_link, X2)
    put(ws, f"D{r}", f"=IF({act},{SIM(f'fsm{k + 1}')},0)", f_link, "0.0")
    put(ws, f"E{r}", f"=IF({act},{SIM(f'rtp_bonus{k + 1}')},0)", f_bold, PCT)
    put(ws, f"G{r}", f'=IF(ISNUMBER(Config!E{bk}),Config!E{bk},"non achetable")', f_link, NUM)
    put(ws, f"H{r}", f'=IF(ISNUMBER({SIMA("rtp", k + 1)}),{SIMA("rtp", k + 1)},"-")', f_link, PCT)
    put(ws, f"I{r}", f'=IF({act},{SIMA("prix_conseille", k + 1)},"-")', f_link, "0")
put(ws, "A9", "RTP ESTIMÉ (spins exacts + bonus simulés)", f_bold, fill=fill_key)
put(ws, "E9", "=SUM(E5:E8)", f_bold, "0.000%", fill_key)
for r in range(5, 9):
    put(ws, f"F{r}", f"=IF($E$9=0,0,E{r}/$E$9)", f_norm, PCT)
put(ws, "A10", "Statut du RTP", f_bold)
put(ws, "E10", '=IF(E9=0,"Lance le simulateur",IF(AND(E9>=RTP_MIN,E9<=RTP_MAX),"OK",IF(E9<RTP_MIN,"Trop bas","Trop haut")))', f_bold, fill=fill_key)
put(ws, "A11", "RTP simulé (2M de spins, plafond compris)", f_norm)
put(ws, "E11", f"={SIM('rtp')}", f_link, "0.000%")
put(ws, "F11", f'=IF(ISNUMBER({SIM("marge")}),"± "&TEXT({SIM("marge")},"0.00%"),"")', f_note)
note(ws, "A12", "Le SDK règle ensuite le RTP final exactement sur RTP_CIBLE (pondération naturelle). Les contrôles complets (règles Stake, risques, équilibre) sont listés dans l'onglet Simulation.")
c0 = 15
put(ws, f"A{c0 - 1}", "CONTRÔLES (copie de l'onglet Simulation)", f_sub, border=False)
header(ws, c0, 1, ["Contrôle", "Valeur", "Règle", "Statut"])
for i in range(22):
    r = c0 + 1 + i
    src = SIMU.SIM_C0 + 1 + i
    for col in "ABCD":
        put(ws, f"{col}{r}", f'=IF(Simulation!{col}{src}="","",Simulation!{col}{src})', f_bold if col == "D" else f_norm)
widths(ws, {"A": 52, "B": 24, "C": 60, "D": 24, "E": 14, "F": 12, "G": 14, "H": 14, "I": 14})

for s in wb.worksheets:
    s.sheet_view.showGridLines = False
wb.calculation.fullCalcOnLoad = True
wb.save(OUT)
print("ok", OUT)
