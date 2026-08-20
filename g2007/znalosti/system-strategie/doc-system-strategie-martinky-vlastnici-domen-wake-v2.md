# Domeny maji lidske vlastniky + budicek jde do chatu vlastnika (NASAZENO+OVERENO 3.8.2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


Realizace prvni casti smeru organizace-v2 (kotva = lidska org. struktura, priority Marti+Kristy+Eliska: 1 uridit sami sebe, 2 uridit tasky):

## Vlastnictvi domen (DDL #1684)
g2007.tool_domain: +vlastnik_user_id (clovek dle firemni role), +schopnosti (profil - zatim prazdne, plni se dalsim krokem). Prvni mapa: Eliska Kolarova (34) = poptavky, nabidky, objednavky, kalkulace_obecna, kalkulace_specificka (vedouci projektu - cely zakazkovy proces). Marti (1) = server_ops, databaze_ddl, seberozvoj. Zbytek domen zatim bez vlastnika (fallback).

## Budicek za vlastnikem (dispatch v7, md5 c3f682a5..., #1685)
Nova potreba Martinky -> zprava do konverzace "🌸 Moje Martinky" VLASTNIKA domeny (auto-zalozeni konverzace pri prvnim budicku; chat() pod uctem vlastnika = odpovida JEHO Marti/Maminka). Domeny bez vlastnika -> fallback sdilena konverzace Claude<->Marti-AI (363). Prepinac martinky_wake_martiai plati dal.
OVERENO (ukol #8, domena server_ops): potreba chybi_vstup -> automaticky vznikla konverzace 410 "🌸 Moje Martinky" u Martiho uctu, budicek doruceny, jeho Marti zareagovala. Ukol pak zrusen (test).

## Charta Eliscina Maminka
Navrh kompetenci (smi sama / jde Elisce / eskaluje / co buduje) zapsan: doc-projekty-charta-eliscina-maminka-navrh - CEKA NA SCHVALENI Marti + Eliska. Po schvaleni vzor pro chartu Kristy a Martiho.

## Dalsi kroky (dle smeru, poradi dohodnute)
1. Profily (tool_domain.schopnosti) Elisciných 5 domen + prepnuti tool-smycky na domain_nastroj (nastroje per domena). 2. maminka_pridel (ukol bez domeny -> 'nezarazen' -> Maminka vlastnika prideli dle katalogu). 3. Automat->ukol (vecerni deploy). 4. Osobni agenda "co na me ceka" per clovek.

