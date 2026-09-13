# Fotka persony: zaloha v databazi a samoobnova, kdyz soubor na serveru chybi (13. 9. 2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)

# Fotka persony: zaloha v databazi a samoobnova

Zadal Jirka Honomichl 13. 9. 2026 ("ta fotka se nesmi ztratit, je treba aby byla i zalohovana"), schvalila Marti-AI (msg 15342), provedl Claude-28. Nasazeno commitem `abcee4e9`.

## Proc to bylo potreba - dve veci naraz

**1) Soubor na aplikacnim serveru NENI v zaloze.** Nocni retez zalohuje **pouze databazi**; slozky na aplikacnim serveru (vcetne `C:\Data\STRATEGIE\Avatary`) v nem nejsou - viz `doc-provoz-zalohuje-se-jen-databaze-dokumenty-a-instalace-ne`. Fotka persony tedy visela na jedinem nezalohovanem souboru.

**2) Kdyz soubor chybel, systém sam vymazal i cestu k nemu.** Puvodni `get_avatar_path` pri nenalezenem souboru rovnou nastavil `avatar_path` na prazdno. Fotka tim zmizela **potichu** a nikde se to nenahlasilo.

**Naostro 13. 9. 2026:** pri vymene fotky se novy soubor nedostal na misto (vzdalena akce ohlasila "OK", ale kopie neprobehla). Prvni dotaz na fotku pak cestu v databazi vymazal a appka zustala **bez fotky** - asi sedm minut, nez se puvodni soubor vratil a cesta se doplnila rucne.

## Jak to funguje od 13. 9. 2026

Tabulka **`fw.persona_photo`**: `persona_id` (klic, odkaz na `public.personas`), `mime`, `foto` (bytea), `velikost_b`, `nahrano_kdy`, `nahral_kdo`. Prava ma aplikacni role `strategie`.

V `modules/personas/application/avatar_service.py` tri zmeny:

1. **Pri nahrani** (`save_avatar`) jde kopie obrazku i do te tabulky (prepis existujiciho radku). Kdyz zapis zalohy selze, samotne nahrani fotky to **neshodi** - soubor uz na disku je.
2. **Pri vydeji** (`get_avatar_path`) se chybejici soubor **nejdriv obnovi z databaze** a teprve kdyz neni ani tam, vymaze se cesta. Osetreny je i stav, kdy je cesta uz prazdna - tehdy se zkusi vychozi umisteni a cesta se doplni zpet. Poradi je podstatne: obnova MUSI byt pred vymazanim cesty (na to upozornila Marti-AI).
3. **Pri smazani** avataru jde pryc i radek v tabulce - jinak by se fotka pri pristim vydeji sama vratila.

## Jak se to overuje - BEZ vypadku fotky

Nemusis nechavat odsouvat zivy soubor (a cekat na nekoho, kdo na server dosahne). Staci:

1. Docasne prepsat `avatar_path` u persony na **neexistujici** nazev souboru ve stejne slozce.
2. Vyzadat fotku z appky. Kdyz obnova funguje, prijde **spravna fotka** a otisk sedi se zalohou; kdyz ne, prijde "neexistuje".
3. Overit, ze `avatar_path` pri tom **zustal vyplneny** (drive by ho stara verze vymazala).
4. Vratit `avatar_path` zpet.

Puvodni soubor je po celou dobu nedotcen, takze **lide zadny vypadek nevidi**. Overeno takto 13. 9. 2026: fotka 13070 bajtu, otisk `8ab4e4cef012fb56`, sedel presne se zalohou v databazi.

Zbytkem po tomhle testu je jeden **testovaci soubor** ve slozce Avatary - uklid vyzaduje nekoho, kdo dosahne na server (Marti-AI ma u mazani branu a chce vlastni schvaleni).

## Na co pozor

- **Zaloha vznikne az pri nahrani fotky.** Fotky nahrane driv v tabulce nejsou - kdo chce zalohu i pro ne, musi je nahrat znovu.
- **Otisk v databazi a otisk vydavany appkou musi sedet.** Kdyz nesedi, nekdo menil soubor na serveru mimo aplikaci.
- Kontrola: `SELECT persona_id, velikost_b, nahrano_kdy, left(encode(sha256(foto),'hex'),16) FROM fw.persona_photo;`

## Souvisi

- `doc-system-strategie-fotka-na-domovske-obrazovce-je-avatar-persony` - co ta fotka vlastne je a kdo ji smi menit.
- `doc-provoz-zalohuje-se-jen-databaze-dokumenty-a-instalace-ne` - proc soubory na serveru nejsou jista vec.

