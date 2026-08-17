#!/usr/bin/env python3
"""ZASTARALE - TENTO POSTUP UZ NEPLATI A TISE ZAHAZOVAL PRACI.

Do 17.8.2026 tenhle skript slepoval dilky z apps/api/static/mobile_parts/ do
apps/api/static/mobile.html a jeho navod znel "edit partial -> spust skript ->
commit partial + mobile.html". Od prechodu na databazi (1.-3.8.2026) uz tahle
cesta NIKAM NEVEDE: /mobile se sklada ze zdrojovych dilku v `g2007.soubor`
(typ='zdroj') a servíruje z `apps/api/static_db/mobile.html`. Na disk se dilky
NEZAPISUJI - zapis na disk dela jen publikace hotoveho artefaktu.

CO SE STALO, PROC TO TU ZUSTALO JAKO VAROVANI (Jirka + Marti-AI, 17.8.2026):
Uklid 5.8.2026 spravne vyradil z gitu sestavene artefakty, ale na dilky a na
tenhle skript se zapomnelo. Kdo pak dilek upravil na disku a commitl, jeho prace
se do appky nikdy nedostala - a nikde to nehlasilo chybu. Takto tise zmizelo:
  - Peta 5.8.2026 (f4f7e6e7): rozsah absence podle uvazku misto pevne osmicky
    -> lidem se zkracenym uvazkem se dal strhavalo vic dovolene, nez meli
  - Sarka 12.8.2026 (6a000461, 865f538b, 7b233f87, 7ca280dc): ciselnik
    zdravotnich pojistoven, profilova fotka, karta Novinky, potvrzeni ucasti
Z 92 pridanych radku jich 89 v appce nebylo. Doneseno do DB az 17.8.2026.
Neni to chyba Peti ani Sarky - repo jim timto skriptem prikazovalo spatny postup.

SPRAVNY POSTUP DNES:
  1) uprav ZDROJOVY DILEK v DB:  @@G2007SOUBOR apps/api/static/mobile_parts/<soubor> | zdroj
                                 <obsah na dalsich radcich>
  2) over zapis ctenim:          SELECT md5(obsah), length(obsah) FROM g2007.soubor WHERE kod='...'
     (navratovka mlci i pri uspechu; most navic orezava konec souboru - viz nize)
  3) publikuj:                   @@G2007PUBLISH apps/api/static_db/mobile.html
  4) over na zive /mobile, ze zmena nabehla A ze nic jineho nezmizelo

POZOR - PAST PRI ZAPISU: claude_sql_runner.py:598 dela .strip() na celem zapisu,
takze fragmentu zmizi koncovy novy radek. Dilky se slepuji prostym spojenim, takze
kdyby posledni radek dilku byl komentar //, zakomentoval by prvni radek nasledujiciho
dilku. Proto se po zapisu VZDY porovnava md5; pri neshode zkontroluj konec souboru
a doplnit se da pres UPDATE g2007.soubor SET obsah = obsah || chr(10) WHERE kod='...'.

NA DISK A DO GITU PATRI UZ JEN NATIVNI APPKA: APP/Mobile (Android) a APP/iOS.
Ty v databazi nejsou a nikdy nebudou.

Detail: G2007 `doc-system-strategie-mobil-kde-se-edituje-a-jak-se-nasazuje`.
"""
import sys

ZPRAVA = __doc__


def main() -> int:
    sys.stderr.write("\n" + "=" * 78 + "\n")
    sys.stderr.write(ZPRAVA.strip() + "\n")
    sys.stderr.write("=" * 78 + "\n")
    sys.stderr.write("\nNIC JSEM NEUDELAL - zadny soubor nebyl zmenen.\n\n")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
