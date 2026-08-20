# Faze E davka POST5: 8 POST HTTP endpointu dochazky migrovano

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

Migrovano 8 dalsich POST HTTP endpointu dochazky: att_confirm_day, att_dispute_day, att_announce_delete, att_entry_trim, att_entry_project, att_entry_dispute, att_announce, att_clear_announce. att_announce ma vyjimecny vzor - run(uid, body_param) prijima cely raw body dict misto rozlozenych poli, protoze zavisla _att_presence_note(body) pracuje primo s dict.

SQL most mel transientni 401 vypadek pri prvnim insert pokusu, retry po par sekundach uspel bez zmen.

Deploy commit 305ff08c3, 32 insertions/429 deletions (nejvetsi umazani od Faze C). CELKEM AKTIVNICH FUNKCI: 121. router.py: 62928 radku (z puvodnich 67789 = 7.17% zmenseni).

