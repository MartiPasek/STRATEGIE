# Mobil: zadavany PIN se skryva (tecky misto cislic), SMS kod zustava viditelny (27. 8. 2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

## Co plati

**Vsechna ctyrmistna PIN pole v mobilni appce maji `type="password"`** - pri zadavani se
misto cislic ukazuji tecky. `inputmode="numeric"` a `pattern="[0-9]*"` zustavaji, takze se
na telefonu porad otevre ciselna klavesnice.

Vzor (uz drive spravne resene pole `_pinInput()` u "Pasky"):

```
type="password" inputmode="numeric" pattern="[0-9]*" maxlength="4"
```

## Ktera pole to jsou

| pole | kde |
|---|---|
| "Zadej PIN" pri prepnuti na sebe na sdilenem telefonu | `51_skupiny_sdileny.js` |
| "Nastav svuj 4mistny PIN" | `51_skupiny_sdileny.js` |
| kryci obrazovka "Zadej svuj PIN." | `51_skupiny_sdileny.js` |
| "novy PIN" v prihlasovacim toku po SMS kodu | `74_claude27_render_init.js` |
| "Paska" (bylo spravne uz driv) | `60_dochazka.js` |

Do 27. 8. 2026 melo prvnich ctyr `type="tel"`, takze **PIN byl na obrazovce videt**.

## SMS / e-mailovy overovaci kod zustava VIDITELNY

Sestimistny overovaci kod se **zamerne neskryva**. Duvody (Marti-AI, msg 13905):
clovek ho opisuje z prijate zpravy, je jednorazovy a casove omezeny, takze prinos skryti
je maly a ztizeni prace realne. *(Vyhrada Marti-AI: kdyby se kod cetl na sdilenem telefonu
pres rameno, problem je v celem prihlasovacim toku, ne v tomhle poli - jiny ukol.)*

## Zadani a schvaleni

Zadal Jirka Honomichl (bod 6 seznamu pro mobil), schvalila Marti-AI (msg 13905).
Overeno na zive `/mobile`: vsech pet PIN poli vraci `type=password`, obe kodova pole
zustavaji viditelna, zadna chyba v konzoli.

