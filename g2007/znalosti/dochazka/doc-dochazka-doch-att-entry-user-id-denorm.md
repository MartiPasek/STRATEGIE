# Dochazka: att_entry.user_id denormalizace vedle employee_id (bod 4 Marti Paska, 27.7.2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Bod z emailu Marti Paska 26.7.: "sjednotit user_id (att_entry ma employee_id, vyroba_work user_id)". HOTOVO 27.7.2026 (i28).

## Reseni (schvalila Marti-AI msg 11292)
Pridat user_id do att_entry jako NULLABLE denormalizaci VEDLE employee_id (ne misto nej). employee_id zustava = mzdova domena. NErozsirovat vyroba_work o employee_id (tam patri user_id + att_entry_id).
Duvod: att_employee se v router.py JOINuje 254x kvuli prekladu employee_id<->user_id; denormalizace to zjednodusi.

## Provedeno
- ALTER TABLE tenant.att_entry ADD COLUMN user_id bigint + backfill z att_employee (banner #1453, schvalen parent). 35372/35429 vyplneno; 57 NULL = zamestnanci bez napojeneho public.users usera.
- Self-completing (commit 09f4519b/20f1e8d8, ve stejnem bloku _maybe_sync_ec_dochazka jako firma_id): UPDATE ... SET user_id=(SELECT em.user_id FROM att_employee em WHERE em.id=ae.employee_id) WHERE user_id IS NULL AND EXISTS(...). Nove radky dostanou user_id samy pri syncu (a 5 min).

## Souvislost
Priprava na Marti Paskuv budouci uklid "opirat se o user_id, ne CisloZam z TabCisZam". Viz [[doc-dochazka-doch-firma-id-backfill]] (stejny pattern denorm pri syncu).

