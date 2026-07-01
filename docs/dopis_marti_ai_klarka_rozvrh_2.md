# Marti-AI — odpověď Kláře (úvazky: 22 vs 33 vyřešeno + abecedně)

> Od: Marti & Claude · 21. 6. 2026 · Pro: Marti-AI → Klára Vlková (`vlkova@nerudovka.cz`)
> Reaguje na: „v aplikaci má Králová 33 h, v součtu z rozvrhu 22 h" + „seřaďte abecedně" + její screenshot.

## Co jsme zjistili (definitivně)

Klárčin screenshot ukázal, že to **33** je z **naší appky STRATEGIE** — z úvazkového přehledu, který jsme postavili nad daty z Bakalářů. **Chyba je u nás, ne u Klárky ani v Bakalářích:**

- Náš přehled sčítal **počet hodin v rozvrhu (placements)**, ale **nezohledňoval lichý/sudý cyklus** —
  střídavé hodiny (1,5 h = lichý 2 / sudý 1) se počítaly jako celé. Proto Královská **33** místo **22**.
- **22 h je správně** a ověřeno **dvěma nezávislými zdroji**: reálný rozvrh (`r_rozvrh`) i úvazkový
  modul Bakalářů (`ruvazky`, POCET_HOD je na 14 dní → /2). Oba dají 22.
- **To je přesně ta 1,5h chyba, kterou Klárka původně hlásila** — a my ji teď máme přesně zaměřenou.

## Co s tím

- **Excel je správný a teď i abecedně** (z reálného rozvrhu, cyklicky správně) — to je pro Klárku platná tabulka.
- **Úvazkový přehled v appce opravíme**, aby ukazoval reálných 22 (započítá lichý/sudý). Vyžaduje to
  doplnit cyklus do zrcadla z Bakalářů (přes Klárčin konektor) — uděláme to čistě, koordinovaně.

## Návrh e‑mailu Kláře (uprav, přidej tón)

> Kláro,
>
> díky moc za screenshot — díky němu jsme to přesně zaměřili. **Měla jsi pravdu, že to nesedí —
> a chyba byla na naší straně**, ne v Bakalářích. Náš úvazkový přehled v appce sčítal hodiny
> z rozvrhu, ale **nezohledňoval střídání lichý/sudý týden** (těch 1,5 h). Proto u Královské
> ukazoval 33 místo reálných **22**.
>
> Správné číslo je **22 h** a ověřili jsme ho dvěma způsoby (reálný rozvrh i úvazkový modul
> Bakalářů) — sedí. V příloze máš opravený přehled **seřazený podle abecedy**, cyklicky správně.
>
> Ten přehled v appce teď opravíme, aby ukazoval rovnou správná čísla. A jakmile mi řekneš, kde máš
> nasmlouvané úvazky, doplním sloupec „rozdíl".
>
> Díky za trpělivost a za to, že sis toho všimla!
> Marti‑AI
>
> *(Příloha: NERUDOVKA_uvazky_2026-06-21.xlsx — abecedně, aktuální)*
