# Vyhodnoceni zakazek: opravneni na Uzavrit/Zrusit (hotovo 6.8.2026)

> oblast: `vyroba` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Opravneni na akce, ktere sahaji na penize

**Hotovo, nasazeno a overeno 6. 8. 2026** (C28/Jirka), commit `6bf2e2b0`.
Splneni podminky Marti-AI z 24. 7. 2026: *"az pri napojeni realnych dat pridat explicitni
opravneni"*. Data napojena 5. 8. 2026, takze podminka se stala splatnou.

## Proc

"Uzavrit" **vytvari vyplaty** (SuperHruba) v `ec.zakazky_finance_zam`, "Zrusit" je **maze**.
Do 6. 8. to mohl spustit **kterykoli z ~20 lidi** s pristupem do ERP - endpoint
`/api/v1/erp/action/run` gate-oval jen pres `_require_erp_member`, zadny per-action gate.

## Reseni

Tabulka **`ec.akce_opravneni`** (`akce`, `user_id`, `poznamka`, `pridal`, `pridano`)
+ kontrola v `ec_action_run` pro akce v `_EC_AKCE_S_OPRAVNENIM = {uzavrit, zrusit}`.

**Zavreno by default** - kdo v tabulce neni, dostane **HTTP 403** s lidskou hlaskou.
Ostatni akce (priprava, prepocet, koeficienty, slouceni, sefmonter) zustavaji na beznem
pristupu do ERP - jen pocitaji nebo meni hodnoceni, penez se netykaji.

**Je to KONFIGURACE, ne kod:** pridat/odebrat cloveka = jeden radek v tabulce, **zadny deploy**.

## Kdo tam je

`uzavrit` i `zrusit`: **Dusan Havlat (41)** - vedouci vyroby, uzaverku dela (verdikt
Marti-AI 24.7.2026 + potvrdil Jirka 6.8.: *"hlavne at k vyhodnoceni zakazek ma pristup
a prava hlavne Dusan Havlat"*). Dale spravci: Marti (1), Kristyna (11), Jirka (20).

## Overeno naostro obe strany

- clovek NA seznamu -> akce probehne (HTTP 200)
- clovek MIMO seznam -> **HTTP 403** + hlaska "Na tuto akci nemas opravneni. Vytvari
  (nebo maze) vyplaty, proto ji smi spustit jen poverena osoba."
  (overeno docasnym odebranim ze seznamu a vracenim zpet)

Seznam byl naplnen **PRED** nasazenim, aby nevzniklo okno, kdy nemuze nikdo.

## Poznamka: Dusan ma membership_status = 'invited'

Do modulu se dostane pres whitelist scoped uzivatelu (`_ERP_SCOPED_USERS = {41}`), ktery
membership neresi, takze mu to nevadi. **Ale muze mu to chybet jinde** - nekterá mista
filtruji lidi na `user_tenants.membership_status = 'active'` (napr. prijemci v HR).
Stoji za proverku.

