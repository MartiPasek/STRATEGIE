# Faze E davka POST6: 5 endpointu fix/* + att_sync_vyroba_work migrovano

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Faze E davka POST6 (31.7.-1.8.2026)

Migrovano 5 vetsich POST HTTP endpointu dochazkove fronty oprav (odlozenych z POST4):
att_fix_entry (/app/attendance/fix/entry), att_fix_add (/app/attendance/fix/add),
att_fix_void (/app/attendance/fix/void), att_fix_polozka (/app/attendance/fix/polozka),
att_fix_merge (/app/attendance/fix/merge). Plus jadrova sdilena funkce
_att_sync_vyroba_work (173 radku, "kanonicka kaskada" att_entry/vyroba_work) migrovana
JAKO SAMOSTATNA funkce (cross-script vzor Faze C-2) - byla sdilenou zavislosti vsech
5 fix/* endpointu, ted dostupna i pro budouci fix/resync pres stejny stub.

Overeni: AST-literal-set diff + exec-compile + stray-ref kontrola na vsech 6, byte-presny
round-trip DB vs. lokalni soubor. Deploy commit a30a2ba6d, push OK, cloud OK.
CELKEM AKTIVNICH FUNKCI: 126. router.py 62140 radku (z 67789 = 8.34% zmenseni).

DULEZITA GOTCHA: manualni git commit teto davky spustil automaticke git auto-gc, ktere
se opakovane prerusilo (device_bash nedokaze mazat soubory) a nechalo desitky .lock
souboru napric .git/refs a .git/logs. Commity/push presto uspesne prosly (overeno
byte-presne), ale doporucuje se cloveku spustit `git gc` primo na svem stroji (kde ma
plna prava mazat soubory), aby se .git adresar uklidil. Detaily viz WORK_LOCK.txt zaznam
"FAZE E DAVKA POST6".

