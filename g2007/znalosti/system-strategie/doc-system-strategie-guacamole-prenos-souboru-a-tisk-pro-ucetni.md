# Guacamole: přenos souborů a tisk pro účetní — jak zapnout a tři pasti

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)

Účetní přistupují k cloud Heliosu (188.12) přes bránu Guacamole na 188.11 (prohlížeč → RDP, bez VPN). Do 9. 9. 2026 neuměly dostat soubor z plochy k sobě do počítače. Ověřeno a zprovozněno 10. 9. 2026 (Kristý + C24).

## Kde se to zapíná
`https://ucto.strategie-ai.com` → přihlásit jako `guacadmin` → Nastavení → Připojení → kliknout **přímo na název** připojení (`Helios – Martia` / `Helios – Peta`) → sekce **Přesměrování zařízení**.

Pozor: na té stránce je i odkaz na *sdílený profil* — to je něco jiného (sdílení běžícího sezení s další osobou) a parametry RDP tam nejsou.

| Pole (české popisky, ověřeno na obrazovce) | Hodnota |
|---|---|
| Povolit tisk | ✓ |
| Název přesměrované tiskárny | `Guacamole PDF` |
| Povolit jednotku (= enable-drive) | ✓ |
| Název jednotky | `Guacamole` |
| Cesta na disku (= drive-path) | `/tmp/${GUAC_USERNAME}` |
| Automaticky vytvořit disk | ✓ |
| Zakázat stahování / nahrávání souborů | nechat prázdné (jsou to ZÁKAZY) |

Změna se projeví až v **novém** sezení — nestačí zavřít záložku, uživatel se musí **odhlásit z Windows** (Start → ikona účtu → Odhlásit se) a přihlásit znovu. Zavřením prohlížeče sezení na serveru běží dál.

## Jak se s tím pracuje
- **Ven z plochy:** ve vzdálené ploše přesunout soubor do složky **`Download`** uvnitř disku Guacamole. Co tam přistane, prohlížeč automaticky stáhne uživateli. Složku vytváří brána sama. Není to odkládací složka — cokoli tam dáš, okamžitě odchází.
- **Dovnitř:** `Ctrl`+`Alt`+`Shift` → v postranní nabídce tlačítko **Nahrát soubory**.
- **Sestavy:** tisk v Heliosu na tiskárnu `Guacamole PDF` → PDF se stáhne rovnou do prohlížeče. Ověřeno 10. 9. 2026 (Poznámkový blok i sestava z Heliosu, diakritika v pořádku).

## PAST 1 — `create-drive-path` nezakládá nadřazené adresáře
`drive-path = /drive/${GUAC_USERNAME}` **nefunguje**, protože složka `/drive` uvnitř kontejneru `guacd` neexistuje. `/tmp` existuje, proto `/tmp/${GUAC_USERNAME}` funguje.

**Zrádné je, že disk se ve Windows stejně ZOBRAZÍ.** Brána zařízení ohlásí, i když za ním není použitelná složka. Projeví se to takhle:
- „Složka je prázdná"
- každá operace (kopírování i *Nový → Textový dokument*) hlásí „Položka již není umístěna v Tento počítač … Jednotka nebo složka přesměrovaná pomocí Vzdálené plochy"
- čisté odhlášení a přihlášení nepomůže

**Ikona disku NENÍ důkaz funkčnosti. Důkaz je až vytvoření souboru v něm.**

## PAST 2 — testování zevnitř vzdálené plochy
Když si administrátor otevře bránu v prohlížeči, který sám běží na vzdálené ploše (typicky RDP na 188.11), stahují se soubory **do složky Stažené soubory toho mezistroje**, ne k němu na notebook. Vypadá to jako nefunkční přenos, přitom funguje správně.

Poznávací znamení: **plovoucí lišta s IP adresou nad adresním řádkem prohlížeče** = jsi ve vzdálené ploše. Testovat je potřeba z vlastního stroje. Účetní se hlásí ze svého počítače, takže jich se to netýká.

## PAST 3 — neuložená změna
Cesta k disku zůstala několik kol na původní hodnotě, aniž by to bylo znát. **Po každém Uložit načíst stránku znovu (`F5`) a zkontrolovat, že hodnota zůstala.**

## Co je provizorní (k 10. 9. 2026)
- `/tmp` je **dočasné** — restart kontejneru složku vysype. Je to průchoďák, ne úložiště; na disku nikdo nic nenechává.
- Trvalé řešení: do `deploy/guacamole/docker-compose.yml` ke službě `guacd` doplnit `volumes: - ./guac-drive:/drive` a vrátit cestu na `/drive/${GUAC_USERNAME}`. Martiho ruka (188.11, WSL).
- Nastaveno zatím jen na jednom připojení — druhé nastavit stejně.

## Bezpečnostní kontext
Bránou tečou mzdy a účetnictví. K 8. 9. 2026 **není nasazen IP allowlist v Caddy** a **není potvrzeno, že se po testech vrátilo TOTP 2FA**. Zapnutý přenos souborů znamená, že se přes bránu dají data vynést ven — projít s Martim.

## Související
Heslo `guacadmin` není v trezoru hesel STRATEGIE (`tenant.user_secret`) ani v repu — doplnit. Provozní popis brány: `docs/helios_ucetni_michal_infrastruktura_a_jazyk.md` (otevřený bod č. 3 je tímto vyřešen), runbook `deploy/guacamole/RUNBOOK.md`.

