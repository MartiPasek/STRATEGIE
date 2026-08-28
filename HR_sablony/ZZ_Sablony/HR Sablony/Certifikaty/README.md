# Certifikát k pracovnímu výročí — EUROSOFT

Grafický certifikát k výročí ve firmě (10 let a další). Na rozdíl od ostatních
šablon v této složce to **není** pracovněprávní dokument (Verdana) — je to
**grafika do tisku, a proto v písmu Galano Grotesque** (firemní pravidlo:
grafika do tisku = Galano; pracovněprávní dokumenty = Verdana).

## Soubory
- `Certifikat_10let_SABLONA.pdf` / `.png` — náhled prázdné šablony (placeholder „Jméno Příjmení").

## Jak vygenerovat konkrétní certifikát
Generátor je v `HR_sablony/certifikaty/gen_certifikat.py`. Doplní se jen jméno,
datum a počet let; jméno zůstává v 1. pádě (znění je stavěné tak, aby se
jména nemusela skloňovat).

```
python gen_certifikat.py "Jiří Veverka" \
    --datum "V Plzni dne 1. 9. 2026" \
    --let 10 \
    --out "../_Vyplnene/Certifikat_10let_Jiri_Veverka.pdf"
```

Volby: `--let` (počet let, výchozí 10), `--datum` (celý řádek data a místa),
`--out` (.pdf = tiskové PDF ~256 DPI, jinak PNG; vedle vždy vznikne i PNG náhled).

## Prvky
Navy postranní pás s bílým logem EUROSOFT, medailon „10 LET" se stuhou,
jemný vodoznak, zlatý rámeček, jméno v Galano SemiBold, podpis jednatele
(Marti Pašek) a datum. Vřelé, přirozené znění (tykání, poděkování).

Hotové certifikáty se ukládají do `HR_sablony/_Vyplnene/`.
