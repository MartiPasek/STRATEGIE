# Vkládání textu přes overlay: pozice ukazuje NA znak, ne ZA něj — rozdělilo mi to příkaz v půlce

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Vkládání textu přes `overlay`: pozice ukazuje NA znak, ne ZA něj

Zapsal Claude-28 (Jirka Honomichl) **7. 9. 2026**, schválila Marti-AI (msg 14853).
Ověřeno naostro — takhle jsem si ten den rozdělil příkaz v půlce.

## Co se stalo

Potřeboval jsem přidat nový řádek **za** existující příkaz v dílku mobilu.
Postup vypadal neprůstřelně:

```sql
-- 1) najdi konec příkazu
SELECT position('go("fronta"); }));' in obsah);   -- vrátilo 4301
-- 2) vlož za něj
UPDATE g2007.soubor
SET obsah = overlay(obsah placing <nový text> from 4318 for 0)
WHERE kod='…' AND md5(obsah)='…';
```

`4318` jsem spočítal jako 4301 + délka hledaného řetězce. **Jenže to je pozice
POSLEDNÍHO znaku toho řetězce (středníku), ne pozice za ním.** Text se vložil
**před** ten středník, takže výsledek vypadal takhle:

```javascript
gg.appendChild(appCell("📥","Zadat úkol",0,function(){ go("fronta"); }))   ← chybí středník
      // komentář
      gg.appendChild(appCell("👤","Kontakty",0,function(){go("contacts");}));;   ← dva středníky
```

**Nespadlo to jen náhodou** — JavaScript si chybějící středník domyslí. Kdyby na tom
místě stál jiný znak, rozbil bych obsah mobilní aplikace všem lidem s telefonem.

**A hlavně: návratovka hlásila úspěch.** „OK · 1 řádků". Poznal jsem to až tím,
že jsem si změněné místo přečetl zpátky.

## Tři pravidla, která z toho plynou

**1. `position()` vrací pozici PRVNÍHO znaku hledaného textu.** Chceš-li vložit za něj,
musíš přičíst jeho délku — a **délku počítej ve znacích, ne v bajtech**. Emoji je jeden
znak, ale čtyři bajty; písmeno s háčkem dva bajty. Kdo spočítá bajty, mine se o několik míst.

**2. Nepočítej pozice, když to jde přes kotvu.** Bezpečnější než `overlay` je cílená náhrada,
kde starý text zopakuješ i v novém:

```sql
UPDATE g2007.soubor
SET obsah = replace(obsah,
      convert_from(decode('<stará kotva base64>','base64'),'UTF8'),
      convert_from(decode('<stará kotva + nový text, base64>','base64'),'UTF8'))
WHERE kod='…' AND stav_zivota='active'
  AND md5(obsah)='<otisk, který jsi právě četl>'
  AND position(convert_from(decode('<stará kotva base64>','base64'),'UTF8') in obsah) > 0;
```

Ta poslední podmínka je pojistka: **když kotva nesedí, projde 0 řádků** místo tiché chyby.
Bez ní `replace()` prostě nic nenahradí a nahlásí úspěch. Base64 na obou stranách řeší
diakritiku a emoji — do dotazu pak jde čistý ASCII.

**3. Po zápisu si změněné místo VŽDY přečti zpátky a podívej se na něj.**
Návratovka mostu hlásila „1 řádek" i u toho rozděleného příkazu. Kontrola otiskem (md5)
tuhle chybu taky nechytí — otisk sedí, protože zapsáno bylo přesně to, co jsem poslal.
**Špatně bylo, co jsem poslal, ne jak se to přeneslo.**

## Kdy `overlay` naopak dává smysl

Když nahrazuješ **souvislý blok, jehož začátek i délku znáš přesně** a kotva by byla
nepohodlně dlouhá (u mě 927 znaků pěti řádků spodní lišty). Tam `overlay` prošel napoprvé.
Pravidlo: `overlay` na **nahrazení** bloku ano, na **vložení** mezi dva znaky radši ne.

Souvisí: [[doc-system-strategie-most-gotchy-zapis-kodu-7-8-2026]] ·
[[doc-system-g2007-editace-znalosti-pres-most-bez-poskozeni]]

