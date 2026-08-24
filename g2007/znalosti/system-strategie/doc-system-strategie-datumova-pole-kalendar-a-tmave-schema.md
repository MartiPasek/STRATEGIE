# Datumová pole: kalendář se otevře jen na klik a bez color-scheme je ikonka neviditelná (24. 8. 2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


**Našel Jirka Honomichl 24. 8. 2026 („proč tam není možnost výběru data z kalendáře"), opravil Claude-28.** Platí pro každou obrazovku, ne jen pro tu, kde se to našlo.

## Dvě věci, které vypadají jako „chybí kalendář"

### 1) Bez `color-scheme` je ikonka kalendáře neviditelná

Když stránka nemá nastavené `color-scheme: dark`, prohlížeč kreslí systémovou ikonku kalendáře v `input[type=date]` **tmavou** — a na tmavém podkladu ji člověk prostě nevidí. Vyskakovací kalendář by navíc byl světlý uprostřed tmavého systému.

Vypadá to, jako by pole nebylo datumové. **Je.** Ověřeno na produkci: `el.type === 'date'`, ale `getComputedStyle(el).colorScheme === 'normal'`.

```css
input[type="date"]{color-scheme:dark;cursor:pointer}
input[type="date"]::-webkit-calendar-picker-indicator{filter:invert(.8);opacity:.9;cursor:pointer}
```

Většina obrazovek STRATEGIE `color-scheme` v hlavičce má; `karta_zamestnance.html` byla výjimka, proto se to našlo tam.

### 2) Kalendář se sám od sebe otevře JEN po trefení té ikonky

Kliknutí do samotného pole nedělá nic — a to je přesně to, co člověk zkusí. Řeší se to `showPicker()`.

## ⚠️ Gotcha: `showPicker()` smí jen na skutečné gesto uživatele

Ověřeno naostro 24. 8. 2026: pověsit to i na **zaostření pole** (`onfocus`) je **chyba**. Při zaostření tabulátorem prohlížeč vyhodí:

```
NotAllowedError: HTMLInputElement::showPicker() requires a user gesture
```

Při kliknutí myší se pak volání provedla dvě — první kalendář otevřela (`navigator.userActivation.isActive === true`), druhá už jen zbytečně spadla do catch, protože otevření to gesto spotřebovalo. **Používej jen `click`, nikdy `focus`.** Zaostřené pole se má chovat normálně a jít do něj psát.

## Doporučený tvar: JEDEN delegovaný posluchač na stránku

Nevěš to na každé pole zvlášť. Část polí obvykle vzniká **až za běhu** v modálních oknech, takže by se na nová pole časem zapomnělo.

```js
document.addEventListener('click', function(ev){
  const el = ev.target;
  if(!el || el.tagName !== 'INPUT' || el.type !== 'date') return;
  if(el.disabled || el.readOnly) return;
  try{ el.showPicker(); }catch(e){}
});
```

`try/catch` je povinný — kde prohlížeč `showPicker` neumí, zůstane pole obyčejné k psaní a nic se nerozbije.

## Jak to ověřit, aniž bys klikal ručně

Skutečný klik z automatu se nemusí povést a `showPicker()` volané z kódu **vždy** skončí `NotAllowedError` (nemá gesto). Spolehlivá zkouška bez ručního klikání:

1. dočasně obalit `HTMLInputElement.prototype.showPicker` a zapisovat volání,
2. na každé pole poslat `dispatchEvent(new MouseEvent('click'))`,
3. sledovat **jestli se posluchač vůbec spustil** (ne jestli se kalendář otevřel — to bez gesta nejde),
4. k tomu zkontrolovat `getComputedStyle(pole).colorScheme === 'dark'`.

Takhle se dá projít i pole v oknech, která se otevírají až za běhu.

## Kde je to nasazené

`apps/api/static/karta_zamestnance.html` — 16 datumových polí, commity `005cb9d0`, `f1195614` (odstranění chybného `onfocus`) a `46853adf` (rozšíření na celou stránku + sjednocení na jeden posluchač).

