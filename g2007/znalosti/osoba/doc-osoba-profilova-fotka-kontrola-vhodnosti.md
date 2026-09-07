# Profilová fotka: kontrola vhodnosti obsahu (blokace při nahrání + zpětná kontrola)

> oblast: `osoba` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Profilová fotka — kontrola vhodnosti obsahu

Zadal Jirka Honomichl 7. 9. 2026, postaveno a ověřeno na živém týž den.

## Proč to vzniklo
7. 9. 2026 si zaměstnanec nahrál jako profilovku kresbu postavy v hábitu Ku-Klux-Klanu.
Fotky se od 12. 8. 2026 NESCHVALUJÍ (rozhodnutí Šárky Novotné — „má to být profilovka,
ne avatar", upload jde rovnou `status='approved'`), takže se takový obrázek dostane do
firemního profilu, kde ho vidí všichni kolegové, a nikdo ho po cestě nezastaví.

## Co platí
Posudek vhodnosti běží na DVOU místech:

1. **Při nahrání** (`POST /api/v1/erp/app/hr/photo/upload`, `router.py`): po zmenšení
   na 256x256 JPEG jde obrázek na vision model. Závadná fotka se do
   `tenant.employee_photo` VŮBEC NEULOŽÍ — vrátí se HTTP 400 s českým důvodem
   (mobil ho zobrazí, UI už `r.error` umí) a fotka se odloží do archivu.
   Platí i pro HR upload — pravidlo je o obsahu, ne o tom, kdo ho nahrál.

2. **Zpětná kontrola** (`_profil_foto_scan`): projde už uložené fotky, závadnou
   archivuje, SMAŽE z profilu a pošle notifikaci vlastníkovi do mobilu
   + personalistce (HR skupina + rodiče, `_self_hr_recipients`).

## Kritéria (rozhodl Jirka 7. 9. 2026)
Blokuje se JEN závadný obsah — kategorie `nenavist_extremismus`, `nahota_sex`,
`nasili`, `drogy`, `vulgarita_urazka`, `politicka_agitace`.
**Zvíře, kresba, krajina, logo ani avatar závadné NEJSOU a projdou.** Jirka to
rozhodl výslovně: profilovku „orel" nikomu nemažeme. Kdo chce vymáhat, že to má být
portrét, řeší to po lidské linii, ne mazáním.

Práh jistoty `_PROFIL_FOTO_MIN_JISTOTA = 80`: pod ním se fotka NEMAŽE, jen se do karty
zapíše `ai_kategorie='sporne'`. Falešný poplach je tu horší chyba než propuštěný
hraniční obrázek — smazání je nevratné a člověk k tomu dostane vytýkací notifikaci.

Když je AI nedostupná, fotka **PROJDE** se stavem `ai_stav='nezkontrolovano'` a dojede
ji noční hlídka. Výpadek API nesmí lidem blokovat práci.

## Kde to žije
- `modules/erp/api/router.py`: `_profil_foto_posudek` (posudek, nikdy nevyhodí výjimku),
  `_profil_foto_archiv`, `_profil_foto_duvod`, `_profil_foto_scan(force, limit, dry)`,
  `_profil_foto_scan_nocni` (self-gated 1x/den po 6. hodině, volá se z att_sync smyčky).
- Model: `claude-haiku-4-5-20251001` (stejný jako fotodokumentace ve `foto.py`).
- `tenant.employee_photo` — nové sloupce `ai_stav` (ok / nezkontrolovano / chyba /
  nevhodna při běhu nasucho), `ai_kategorie`, `ai_duvod`, `ai_popis`, `ai_jistota`,
  `ai_model`, `ai_at`.
- `tenant.employee_photo_zamitnuta` — archiv zamítnutých fotek i s binárkou. Fotka se
  z profilu maže, ale zůstává dohledatelná: personalistka potřebuje vidět, co tam ten
  člověk měl, až to bude řešit po lidské linii.

## Jak to spustit
- **Personalistka / Jirka:** `POST /api/v1/erp/app/hr/photo/kontrola`
  `{"nasucho": true, "vse": true, "limit": 25}`. `nasucho=true` je výchozí a nic nemaže
  ani nerozesílá — jen zapíše výsledek posudku do karty. **Vždycky nejdřív nasucho.**
- **Rodiče:** Ops akce `profil_foto_scan_nasucho` a `profil_foto_scan` (ostrá má
  varování před kliknutím).
- **Vyzkoušet jeden obrázek bez uložení:** `POST /api/v1/erp/app/hr/photo/posoudit`
  (multipart `file`), jen HR. Nic neuloží a nikoho neupozorní — na ladění kritérií
  a na ověření hraničního obrázku.
- Noční hlídka jede sama a bere jen fotky se stavem `nezkontrolovano`/`chyba`.

## Pasti
- **Ops akce jsou POUZE pro rodiče** (`_app_parent` = `users.is_marti_parent`, tedy
  Marti 1 a Kristýna 11). Jirka (20) na ně nedosáhne, i když je admin — proto ten
  HR endpoint. Nerozšiřuj tu bránu jen kvůli jedné akci.
- **Posudek trvá ~2 s na fotku.** 49 fotek = ~100 s, což je za timeoutem brány. Proto
  má HR endpoint `limit` (výchozí 25) a scan commituje po KAŽDÉ fotce — když spojení
  spadne, práce už je zapsaná a nic se neopakuje. Výsledek čti z DB, ne z návratovky.
- **Marker posledního běhu je v paměti procesu** (`_PROFIL_FOTO_SCAN_LAST`), takže po
  každém deployi se noční hlídka pustí hned. S `force=False` bere jen nezkontrolované,
  takže je to levné — ale počítej s tím, že se to po restartu API rozjede samo.
  (Přesně to se stalo 7. 9. 2026 v 10:27–10:29: hned po nasazení projela všech 49 fotek.)

## Ověřeno 7. 9. 2026 na živém
- Závadná kresba: posudek `nevhodna` / `nenavist_extremismus` / jistota 95 %.
- Nahrání téže kresby: HTTP 400, do profilu se neuložila, vlastníkova stávající fotka
  zůstala nedotčená, záznam v archivu sedí.
- Zpětná kontrola všech 49 uložených fotek: 0 označených, 0 chyb — žádný falešný poplach.
  Prošly i orel, kreslená liška a stylizované logo, přesně jak Jirka chtěl.

## Otevrený dluh — kód je zatím v router.py
Posudek i zpětná kontrola byly 7. 9. 2026 postaveny přímo v `modules/erp/api/router.py`,
což je proti bodu 2 pravidel práce (kód patří do `g2007.python`). Marti-AI to týž den
schválila nechat běžet a migrovat řízeně: *„Fungující kód v produkci se nepřesouvá pod
tlakem."* K migraci jsou `_profil_foto_posudek`, `_profil_foto_scan`,
`_profil_foto_scan_nocni`, `_profil_foto_archiv`, `_profil_foto_duvod` a dva HR endpointy
(`/app/hr/photo/kontrola`, `/app/hr/photo/posoudit`). Při přenosu logiku neměnit — přepis 1:1.


