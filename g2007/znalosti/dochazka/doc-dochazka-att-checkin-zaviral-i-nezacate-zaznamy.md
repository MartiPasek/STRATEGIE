# Prichod do prace prepisoval konec zaznamu, ktery jeste nezacal (zaporne hodiny)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


## Co se delo

`att_checkin` mel hned na zacatku uklid dnesniho dne:

    UPDATE tenant.att_entry SET ended_at=now(), is_active=false,
           hours=round((EXTRACT(EPOCH FROM (date_trunc('minute', now())-started_at))/3600.0)::numeric,2),
           updated_at=now()
     WHERE tenant_id=:t AND employee_id=:e AND entry_date=current_date
       AND ended_at > now() AND status IS DISTINCT FROM 'superseded'

Zamer je spravny (zaznam, ktery "bezi do budoucnosti", se ma pri pichnuti uzavrit),
ale **chybela podminka na zacatek**. Zaznam rucne doplneny na POZDEJSI hodinu tehoz dne
ma konec v budoucnosti taky - a uklid mu ho prepsal na aktualni cas, i kdyz jeste nezacal.
Vysledek: konec DRIV nez zacatek a **zaporne hodiny** (nic je neomezovalo).

## Realny pripad (1. 9. 2026, Pavel Egermaier)

- 07:17 Dusan Havlat doplnil "prevod z 21/8" jako work **16:11-20:11** (att_audit id 1347, poradku).
- 12:58 Pavel se po pauze prihlasil do prace -> uklid prepsal konec na 12:58.
- Zustalo **16:11-12:58 = -3,22 h** (att_entry 10015230) a pravidlo R9 `pretazeni_useku`
  poslalo hlasku "na zakazkach je vic hodin nez trval usek (4.00 h proti -3.22 h)".
- 13:31 Dusan zalozil opravu 16:11-20:13 (10015487).

**Rozsah v datech k 2. 9. 2026:** zaporne rozpeti mel v cele DB **jediny zaznam** (tento).
Dalsich 23 zapornych `hours` jsou cervnove korekce `fond_doplneni` - jina, zamerna vec.
Ohrozeny byl kazdy rucne pridany zaznam na pozdejsi hodinu tehoz dne; takove byly dva
a jeden z nich to zasahlo.

## Oprava (2. 9. 2026, att_checkin v10, schvalila Marti-AI msg 14260)

Do WHERE pribylo `AND started_at <= now()` (co jeste nezacalo, se nezavira) a hours se
pocitaji pres `GREATEST(..., 0)`, aby zaporna hodnota nesla ulozit ani jinudy.
Tvrda kontrola primo v DB (`ended_at >= started_at`) se **zamerne nezavadela** - rozbila by
smeny pres pulnoc; az se budou resit systematicky, prijde constraint s nimi.

**Overeno naostro** 2. 9. 2026 na uctu Jiriho Honomichla: doplnen zaznam 23:00-23:30,
pak pichnut prichod ve 20:43 - zaznam zustal **nedotcen** (0,50 h). Pred opravou by mel
konec 20:43 a -3,28 h. Zkusebni zaznamy nasledne stornovany.

## Na co si dat pozor

- Tuhle podminku ma **jen `att_checkin`** - zadny jiny aktivni skript v `g2007.python`
  konstrukci `ended_at > now()` nepouziva (overeno dotazem 2. 9. 2026).
- `att_fix_add` i `att_fix_entry` maji vlastni kontrolu "Konec musi byt po zacatku",
  takze **rucnim zadanim** takovy zaznam nevznikne - vznikl az pozdejsim prepisem.
- `updated_at` poskozeneho zaznamu ukazoval az cas pozdejsiho storna, takze **podle nej
  se nedalo poznat, kdy se konec zmenil**. Stopu dal az `tenant.att_audit`, kde je
  puvodni zadani (16:11-20:11) videt.

