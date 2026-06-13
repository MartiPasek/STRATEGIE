# 🍎 Návod pro Jirku — rozjezd iOS appky STRATEGIE (krok po kroku)

> Ahoj Jirko! Tohle je úplně podrobný návod. **Dělej to odshora dolů, nepřeskakuj.**
> Po každé části je **✅ KONTROLA** — když to sedí, jdi dál. Když ne, napiš Martimu.
>
> **Dnes večer cíl:** nainstalovat prostředí + uvidět naši appku běžet v iPhone
> simulátoru. **Apple účet k tomu NEPOTŘEBUJEŠ** (čeká na schválení) — dnes jedeš
> celé v simulátoru.

---

## ČÁST A — Instalace prostředí (většina času je jen čekání na stažení)

**A1. Zkontroluj verzi macOS**
- Vlevo nahoře **🍎 menu → About This Mac**.
- Potřebuješ **macOS Sonoma 14.5 nebo novější** (ideálně Sequoia 15).
- Když máš starší → **System Settings → General → Software Update** → nainstaluj.

**A2. Nainstaluj Xcode (velké, spusť jako PRVNÍ)**
- Otevři **App Store** (přímo na Macu, ikona modré „A").
- Do vyhledávání napiš **Xcode** → u Xcode klikni **Get / Install**.
- ⚠️ Je to **~12–15 GB**, stahuje klidně hodinu. **Nech to běžet na pozadí**
  a mezitím můžeš dělat A4.

**A3. Spusť Xcode poprvé**
- Až se stáhne, **otevři Xcode**.
- Vyskočí **„Agree" k licenci** → odsouhlas.
- Nech ho **doinstalovat doplňkové komponenty** (chvíli to trvá, je to normální).

**A4. Nainstaluj nástroje příkazové řádky**
- Otevři **Terminal**: stiskni **Cmd + mezerník**, napiš `Terminal`, Enter.
- Zkopíruj a vlož tento řádek, pak Enter:
  ```
  xcode-select --install
  ```
- Vyskočí okno → **Install**. (Když napíše „already installed", je to taky OK.)

**A5. Přihlas Apple ID do Xcode**
- V Xcode nahoře: **Xcode menu → Settings… → Accounts**.
- Vlevo dole **„+" → Apple ID** → přihlas se (zatím stačí běžné Apple ID;
  firemní vývojářský tým přidáme, až Apple schválí účet).

> ### ✅ KONTROLA A
> Xcode jde otevřít, v Accounts vidíš svoje Apple ID, Terminal nehlásí chybu.
> Když ano → pokračuj. Když ne → napiš Martimu, co se zaseklo.

---

## ČÁST B — Vytvoř appku (kostra, co načte naši STRATEGII)

**B1. Nový projekt**
- Xcode → **File → New → Project…** (nebo na úvodní obrazovce „Create New Project").
- Nahoře vyber záložku **iOS** → dlaždice **App** → **Next**.

**B2. Vyplň přesně tohle:**
| Pole | Co napsat |
|---|---|
| Product Name | `mobile` |
| Team | None (zatím nech prázdné) |
| Organization Identifier | `cz.strategie` |
| Bundle Identifier (samo se vyplní) | `cz.strategie.mobile` ✅ |
| Interface | **SwiftUI** |
| Language | **Swift** |
| Storage / Testing | nech vypnuté/None |

- **Next** → vyber, kam uložit (klidně **Desktop**) → **Create**.

**B3. Vlož náš kód**
- V levém panelu klikni na soubor **`ContentView.swift`**.
- **Smaž úplně všechno**, co v něm je, a vlož místo toho tohle:

```swift
import SwiftUI
import WebKit

// Obal kolem webu STRATEGIE (mobile.html)
struct WebView: UIViewRepresentable {
    let url: URL

    func makeUIView(context: Context) -> WKWebView {
        let config = WKWebViewConfiguration()
        config.allowsInlineMediaPlayback = true            // video/audio v stránce
        let webView = WKWebView(frame: .zero, configuration: config)
        webView.allowsBackForwardNavigationGestures = true // gesto zpět/vpřed
        webView.load(URLRequest(url: url))
        return webView
    }

    func updateUIView(_ uiView: WKWebView, context: Context) {}
}

struct ContentView: View {
    var body: some View {
        WebView(url: URL(string: "https://strategie-ai.com/mobile")!)
            .ignoresSafeArea()   // ať web vyplní celou plochu
    }
}

#Preview {
    ContentView()
}
```

**B4. Spusť to v simulátoru**
- Nahoře uprostřed Xcode je výběr zařízení — vyber třeba **iPhone 16**.
- Klikni **▶ (Run)** vlevo nahoře (nebo **Cmd + R**).
- Poprvé to chvíli buildí a spouští simulátor — **buď trpělivý**.

> ### ✅ KONTROLA B
> Naběhne **iPhone simulátor** a v něm **naše appka STRATEGIE** — uvidíš
> přihlášení / docházku, přesně jako na telefonu. 🎉
> **A to celé bez Apple účtu!** Když tohle vidíš, večerní cíl je splněný.

---

## ČÁST C — Uložit projekt do našeho repa (až bude kostra běžet)

> Tohle není nutné dnes — klidně až zítra. Slouží k tomu, ať je iOS projekt
> u nás v gitu vedle Android appky.

- Marti ti pošle **URL repa + přístupový token (PAT)**.
- iOS projekt patří do složky **`APP/iOS`** v repu.
- S tímhle ti pomůže Claude — neřeš to sám, ať si nerozhodíš strukturu.

---

## ❌ Co dnes NEJDE (a je to úplně v pořádku)

- **Spustit na opravdovém iPhonu** — to vyžaduje schválený Apple Developer účet
  (čeká na ověření Apple). Dnes proto jen **simulátor**.
- **Push notifikace, kontakty, mikrofon** — doplníme až po účtu, společně s Claudem.

---

## 🆘 Když se zasekneš

| Problém | Co s tím |
|---|---|
| Xcode chce heslo | To je heslo k tvému Macu (přihlašovací). |
| Simulátor nenaběhne | Xcode → **Window → Devices and Simulators**, zkontroluj, že je nějaký iPhone. Nebo Xcode restartuj. |
| V appce **bílá obrazovka** | Zkontroluj internet a že v kódu je přesně `https://strategie-ai.com/mobile`. |
| Build hlásí červenou chybu | Vyfoť obrazovku a pošli Martimu — Claude ti řekne, co s tím. |
| „Untrusted / signing" hláška | To je jen pro běh na telefonu. V **simulátoru** to neřeš. |

---

## ➡️ Až budeš hotový

Napiš Martimu „**kostra běží v simulátoru**" → Claude si s tebou sedne na další
krok: **most mezi webem a Swiftem** (aby šly z webu volat nativní věci, co iOS
dovolí — push, kontakty, mikrofon, telefon).

Držíme palce, Jirko! 🤝 Není to závod — dělej to v klidu krok po kroku.

---

*Připravil Claude (id=23) pro Marti & Jirku, 8. 6. 2026.
Doprovodný dokument: `apple_app_priprava.md` (celkový plán + stav účtu).*
