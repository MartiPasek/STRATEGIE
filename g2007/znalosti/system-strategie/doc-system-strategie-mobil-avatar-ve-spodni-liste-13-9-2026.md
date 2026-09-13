# Mobil: druhá ikona spodní lišty je profilová fotka přihlášeného (13. 9. 2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)

Zadal Jiří Honomichl 13. 9. 2026, schválila Marti-AI (msg 15307). Provedl Claude-28.
Vydání mobilní aplikace **v189**.

## Co se změnilo

Druhá ikona zleva ve spodní liště (ta s křestním jménem pod sebou) ukazuje **vlastní profilovou
fotku přihlášeného člověka** místo pevné siluety 👤. Je to tatáž fotka jako kolečko v záhlaví
obrazovky „Moje docházka" — jeden zdroj, `/api/v1/erp/app/hr/photo-me`.

**Kdo vlastní schválenou fotku nemá, vidí dál siluetu.** Není to větev v kódu podle dat:
jádro u člověka bez schválené fotky vrací **404** (`router.py`, obsluha `app/hr/photo-me`,
čte `tenant.employee_photo` se `status='approved'`), takže se uplatní obsluha chyby obrázku.
Stejný vzor už používalo kolečko v záhlaví.

**Dopad k 13. 9. 2026:** schválenou fotku má **50 lidí** — těm se ikona změnila, ostatním ne.

## Tři místa v obsahu appky

1. `74_claude27_render_init.js`, funkce `renderNav()` — místo emoji se do tlačítka vkládá
   `<img class="navava" src="/api/v1/erp/app/hr/photo-me?t=…">`. Obsluha chyby se **věší v kódu**
   (`_avaImg.onerror = …`), ne přes atribut v HTML — inline `onerror` je křehký a nesnáší se
   s bezpečnostní politikou stránky.
2. `02_styles.html` — pravidlo `.tabbtn .i img.navava { display:block; width:21px; height:21px;
   border-radius:50%; object-fit:cover; }`. Bez něj by obrázek seděl na řádku jako písmeno
   a popisek by byl níž než u ostatních ikon (tatáž past jako u SVG ikony Aplikací, 2. 9. 2026).
3. `48_hr_podminky_me.js` — po úspěšném nahrání nové fotky se **překreslí lišta**
   (`window.__M2W._avaTs=Date.now(); window.__M2W.renderNav();`). Bez toho by v liště zůstala
   stará fotka až do restartu appky.

## Proč je čas v adrese stabilní po dobu spuštění

`renderNav()` běží při každém překreslení lišty, tedy velmi často. Kdyby se čas v adrese
generoval pokaždé znovu, tahala by se fotka ze serveru při každém překreslení. Proto se jednou
uloží do `window.__M2W._avaTs` a mění se jen při nahrání nové fotky. Jádro navíc posílá
hlavičku s minutovou platností v mezipaměti.

## Jak se to ověřovalo (bez zásahu do dat)

Chování „člověk bez fotky" jde vyzkoušet na živé liště, aniž by se komukoli mazala fotka:
na obrázku v liště se vyvolá událost chyby načtení a musí se objevit silueta. Pak se lišta
překreslí a obrázek se vrátí. Ověřeno takto 13. 9. 2026 na živém `/mobile`.

