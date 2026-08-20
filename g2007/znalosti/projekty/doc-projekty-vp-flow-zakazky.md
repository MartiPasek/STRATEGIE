# Vp Flow Zakazky

> oblast: `projekty` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

**Flow zakázky poptávka→zaplaceno na klíč cislo_zakazky; zdroje per fáze**

Celý oběh zakázky drží jeden klíč: cislo_zakazky (VR-číslo). Fáze: poptávka → nabídka → objednávka → materiál → výroba (činnosti) → odvoz → faktura → zaplaceno. Faktura AŽ PO odvozu.
Stav flow: tenant.vp_flow_vyroby (booleany ma_poptavka/nabidka/objednavka/material, vyroba_stav, odvoz_datum, ma_faktura, zaplaceno) + kalk_h/real_h/efektivita. Živý pohled připravenosti: /vp-zastup a tenant.vp_zastup_readiness.
Odpovědní za zakázku = korespondenti v e-mailu (e.kolarova, z.cepicky) spárovaní na zakázku přes AB/P kódy v Nazev. Termíny počítej v PRACOVNÍCH dnech (firemni_kalendar), ne kalendářních.

_Souvisi:_ vp-eliska-pilot, vyroba-cinnost-model

