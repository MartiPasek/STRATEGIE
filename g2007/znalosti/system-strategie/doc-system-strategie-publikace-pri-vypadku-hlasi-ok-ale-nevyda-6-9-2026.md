# PAST: pri vypadku hlavniho serveru publikace hlasi OK, ale ven se nedostane

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Publikace behem vypadku rekne OK a nic nevyda

> Zmereno naostro 6. 9. 2026 (Claude-28 / Jiri Honomichl). Doplnek k
> `doc-system-strategie-most-401-failover-na-sekundar-bez-tokenu` a
> `doc-system-strategie-po-updatu-g2007-soubor-nutny-publish`.

## Co se stalo

Dvanact oprav textu se zapsalo do `g2007.soubor` **spravne napoprve** (verze poskocily,
`updated_at` sedel). Nasledny `@@G2007PUBLISH apps/api/static_db/mobile.html` vratil
**`STATUS: OK`** - a **na zive strance nebyla ani jedna z tech dvanacti zmen**.
Vsechny stare texty tam porad byly.

Behem te doby most hlasil dokola `401 (nejspis failover na sekundar 8003)` -
za den **145 vyskytu**, spojeni se vracelo jen na chvilky.

Kdyz se spojeni ustalilo, **tentyz prikaz** publikaci provedl a zmeny naskocily.
Nic se neztratilo, protoze zapis do databaze byl v poradku - ztratila se jen publikace.

## Jak to poznat

| ukazatel | zdrave | pri vypadku |
|---|---|---|
| doba publikace | ~1 az 11 s (mereno 10 248 ms, 1 357 ms) | **830 a 887 ms** |
| navratovka | `STATUS: OK` | **taky `STATUS: OK`** |
| ziva stranka | zmeny tam jsou | **zmeny tam nejsou** |

**Sama navratovka nerozlisi uspech od neuspechu.** Kratka doba je voditko, ne dukaz.

## Zavazne pravidlo

**Po publikaci VZDY stahni zivou stranku a najdi v ni svoje zmeny** - a soucasne over,
ze **stare texty uz tam nejsou**. Kontrola jen na pritomnost noveho nestaci: cast novych
retezcu uz v strance byt muze (napr. nadpis obrazovky, ktery menis dlazdici na miru),
takze vyjde "OK" i kdyz se nevydalo nic. Kontroluj **obe strany**.

Kdyz zmeny chybi a v `watcher.log` jsou 401, **nezapisuj znovu do databaze** - zapis uz
tam je. Pockej, az se spojeni ustali, a **zopakuj jen publikaci**.

## Domnenka (NEOVERENO)

Vypada to, ze publikace behem failoveru dorazi na **zalozni instanci**, ta ji provede
u sebe na disku a vrati "hotovo", zatimco lidem odpovida hlavni instance, kde se
nezmenilo nic. Sedi to na chovani i na to, ze server posila soubor **z disku**.
**V kodu jsem to neoveril** - kdo na to narazi znovu, at to dohleda a tuhle vetu opravi.

## Souvislost

Pravdepodobne stejny koren jako `doc-system-strategie-praha-server-malo-ram-zatuhavani-api`
(3. 9. 2026) a `doc-system-strategie-praha-restart-pripravenost-5-9-2026`.

