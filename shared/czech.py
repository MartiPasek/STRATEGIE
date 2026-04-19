"""
Cesky vokativ jmen — pro osloveni v emailech a UI.

Konzervativni implementace: pokryva bezne pripady, neznama nechava v nominativu.
Pro tricky jmena (Petr -> Petre/Petre, Marek -> Marku) je preferovano jasne
pravidlo; nekdy neni 100% spisovne, ale je srozumitelne a uzivatel to nezmati.

Priklady:
  to_vocative("Klara", "female")   -> "Klaro"
  to_vocative("Marie", "female")   -> "Marie"
  to_vocative("Martin", "male")    -> "Martine"
  to_vocative("Marek", "male")     -> "Marku"
  to_vocative("Tomas", "male")     -> "Tomasi"
  to_vocative("Honza", "male")     -> "Honzo"
  to_vocative("Marti", None)       -> "Marti"  (neznamy rod -> nechavame)
"""

# Specialni pripady kde bezna pravidla selhavaji
_SPECIAL_CASES: dict[str, str] = {
    "petr": "Petře",
    "karel": "Karle",
    "pavel": "Pavle",
    "aleš": "Aleši",
    "ales": "Aleši",
    "josef": "Josefe",
    "david": "Davide",
    "marek": "Marku",
    "jakub": "Jakube",
    "lukáš": "Lukáši",
    "tomáš": "Tomáši",
    "matěj": "Matěji",
    "ondřej": "Ondřeji",
}


def to_vocative(name: str | None, gender: str | None) -> str:
    """
    Vrati vokativ jmena podle rodu. Pokud nevime rod, vraci nominativ.
    Prazdny vstup -> prazdny vystup.
    """
    if not name:
        return name or ""
    n = name.strip()
    if not n:
        return ""

    # Specialni pripady (case-insensitive match na cele jmeno)
    key = n.lower()
    if key in _SPECIAL_CASES:
        return _SPECIAL_CASES[key]

    last = n[-1].lower()
    last2 = n[-2:].lower()

    # Zenske jmena
    if gender == "female":
        if last == "a":
            # Klara -> Klaro, Eva -> Evo, Petra -> Petro
            return n[:-1] + "o"
        if last in ("e", "i", "y"):
            # Marie, Alice, Dolly — nechavame
            return n
        # Jinak konzervativne nechavame
        return n

    # Muzske jmena
    if gender == "male":
        if last == "a":
            # Honza -> Honzo, Luka -> Luko
            return n[:-1] + "o"
        # Cizi kratka jmena (Marti, Tony, Andy) koncici na i/y — nechavame
        if last in ("i", "y", "o", "u"):
            return n
        # Tvrde souhlasky k/g/h a 'ch' -> +u
        if last in ("k", "g", "h") or last2 == "ch":
            return n + "u"
        # Mekke souhlasky -> +i
        if last in ("c", "j", "s", "z") or last2 in ("st", "sc"):
            return n + "i"
        if last in ("š", "ž", "č", "ř", "ď", "ť", "ň"):
            return n + "i"
        # Default: +e  (Martin -> Martine, Jan -> Jane)
        return n + "e"

    # Rod neznamy — konzervativne nominativ
    return n
