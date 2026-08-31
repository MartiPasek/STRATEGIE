# Most: hláška TIMEOUT u zápisu přes banner NEŘÍKÁ, jestli zápis proběhl — ověřuj čtením

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Most: „TIMEOUT" u zápisu přes schvalovací banner NEŘÍKÁ nic

Ověřeno naostro **28. 8. 2026** (Claude-28 / Jirka Honomichl) — **dvakrát v jedné session,
pokaždé s opačným výsledkem.**

## Co se stalo

Zápis přes most čeká na schválení v oranžovém proužku zhruba 120 vteřin. Když nikdo nestihne
kliknout, most vrátí:

```
# STATUS: TIMEOUT · request #NNNN pořád pending po 120 s.
```

**Tahle hláška NEZNAMENÁ, že se zápis neprovedl.** Znamená jen, že most se přestal ptát.
Člověk může kliknout i potom — a zápis proběhne.

| případ | hláška | co se doopravdy stalo |
|---|---|---|
| zapnutí automatu (`request #2595`) | TIMEOUT | **zápis PROBĚHL** — člověk klikl později |
| roztřídění 89 pravidel (`request #2600`) | TIMEOUT | **zápis NEPROBĚHL** — nikdo neklikl |

Rozdíl mezi nimi **z návratovky nepoznáš.**

## Co s tím

1. **Po TIMEOUTu vždy ověř čtením z databáze**, jestli je změna na místě.
2. **Teprve pak se rozhodni, jestli poslat znovu.** Kdo pošle znovu naslepo, provede zápis
   dvakrát — u `UPDATE` s pevnou hodnotou to nevadí, u přičítání nebo zakládání záznamu ano.
3. **Podmínku formuluj tak, aby druhé odeslání nic nezkazilo** (například
   `… AND aktivni = false` u zapínání) — pak druhý průchod projde s „0 řádků" místo škody.
4. **Když čekáš na člověka, řekni mu to** — proužek se nezobrazí sám od sebe do popředí
   a bez upozornění ho snadno přehlédne.

## Souvisí

- [[doc-system-strategie-most-write-navratovka-jen-posledni-prikaz]] — u dávky více příkazů
  hlásí návratovka počet řádků **jen posledního** z nich, takže ani „7 řádků" neříká,
  že prošlo všech pět příkazů. Zase platí: **ověřuj čtením.**
- [[doc-system-strategie-deploy-hlaska-nenasazeno-muze-byt-falesny-poplach]] — tentýž vzorec
  u nasazení: hláška o neúspěchu, přitom nasazeno bylo.

**Obecné pravidlo, které z toho plyne:** návratovka mostu je zpráva o tom, *jak dopadlo čekání*,
ne o tom, *co je v databázi*. Jediný důkaz je čtení.

