# Příznak „čeká na zařazení" visí, když je číselník výchozích podmínek prázdný (25. 8. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Příznak `ceka_na_zarazeni` visí, když číselník výchozích podmínek nic nevrátí

Zjistil Claude-28 na dotaz **Jirky Honomichla** 25. 8. 2026, schválila **Marti-AI** (msg 13652).
Navazuje na [[doc-dochazka-podminky-slouceny-se-smlouvou]] a
[[doc-system-strategie-podminky-vychozi-na-sirku-a-historie-zmen]].

## Jak to má fungovat (záměr, Jirka 20. 8. 2026)

Výchozí hodnoty se člověku do smlouvy propíšou **jen při PRVNÍM zařazení do skupiny**.
Pozdější změna skupiny už nic nepřepočítává — kvůli lidem s individuální dohodou.

Mechanismus stojí na příznaku v `tenant.engagement.pod_meta`:

1. `tenant.engagement_pod_defaults` (BEFORE INSERT na `engagement`) označí každou nevyplněnou
   položku příznakem `ceka_na_zarazeni: true` — **ale jen když člověk v tu chvíli ještě není
   v žádné skupině s výchozími hodnotami**. Když už ve skupině je, hodnoty se naplní rovnou
   a příznak se **nenastaví vůbec** (`RETURN NEW` ve větvi `v_grp IS NOT NULL`).
2. `tenant.engagement_doplneni_pri_zarazeni` (AFTER INSERT na `staff_group_member`) projde
   jen položky s příznakem, doplní je z číselníku a **příznak smaže**.
3. Druhé zařazení spouštěč sice spustí, ale žádný příznak už nenajde → nepřepíše nic. ✅

Ruční zápis podmínek (`hr_conditions_save`, živý kód v `g2007.python`) příznak u dotčené
položky **rovněž odstraní** — buď klíč z `pod_meta` smaže, nebo ho nahradí novým razítkem.
Ručně zadaná hodnota je tedy před automatikou chráněná.

## ⚠️ Mezera

Mazání příznaku je **uvnitř podmínky, že číselník vrátil neprázdnou hodnotu**:

```
IF v_val IS NOT NULL AND btrim(v_val) <> '' THEN
    ... UPDATE ...
    v_meta := v_meta - v_kod;   -- smazání příznaku je AŽ TADY
END IF;
```

Když číselník `tenant.podminky_skupin` pro tu položku **nic nevrátí**, hodnota se nezapíše
a **příznak zůstane viset**. Další zařazení do skupiny pak položku přepíše znovu — přestože
záměr byl přepsat jen poprvé.

## Proč to není teorie — číselník je dnes prázdný

Stav ověřený v databázi 25. 8. 2026:

- **systémový řádek** (ze kterého se dědí) má **samé nuly** — dovolená 0, sick days 0,
  stravenka 0, home office 0; vyplněný je jen úvazek 40 h,
- **všech 17 skupinových řádků je prázdných**, včetně nových skupin
  13 EXTERNÍ / 14 KANCELÁŘE / 15 VÝROBA (ty mají navíc 0 členů).

Číselník **čeká na naplnění**. Dokud se nenaplní, každý nově zakládaný člověk si příznak ponese.

## Dopad — jmenovitě

**Dnes se to netýká nikoho.** Ze **76 aktivních lidí se současnou smlouvou nemá visící příznak
ani jeden** (dotaz přes `jsonb_each(pod_meta)` na `ceka_na_zarazeni = true`).

Riziko je **do budoucna**: nový zaměstnanec založený za prázdného číselníku si příznak ponese,
a kdyby ho personální zařadila do druhé skupiny **až potom, co se číselník naplní**, hodnoty
by se mu přepsaly podruhé.

Související zjištění téhož dne: ze 76 lidí má **29 nulovou dovolenou i sick days i stravenku** —
z toho **26 OSVČ** (u nich je nula správně), **2 dohodáři** a **1 zaměstnankyně na HPP**
s polovičním úvazkem. U všech tří neOSVČ je v `pod_meta` poznámka z 16. 8. 2026, že se hodnota
ze staré tabulky **záměrně nepřenášela** a má ji doplnit personální oddělení. Není to závada,
je to nedoplněný stav čekající na naplnění číselníku.

## Co s tím

Mezera zmizí sama, jakmile se číselník naplní — bude se mít co zapsat a příznak se smaže.
Kdyby se číselník naplňovat neměl, musela by se úprava udělat ve spouštěči (smazat příznak
i tehdy, když číselník nic nevrátí). **Zatím se nic neměnilo** — tohle je jen zápis nálezu.

