//
//  PushNotifications.swift
//  mobile
//
//  APNs notifikace pro iOS obal (verze 1.84).
//
//  PROČ APNs a ne polling jako Android: Android má `DialPollService`, foreground
//  službu, která se á 4–20 s ptá `/app/mobile/commands/pending`. iOS trvalý
//  background polling nedovolí — ekvivalent té služby na iPhonu existovat nemůže.
//  Jediná cesta k notifikaci do lišty (i když je appka zavřená) je push ze serveru.
//
//  ROUTING NA OBRAZOVKU: přebírá se vzor z Androidu (HybridActivity.goScreen,
//  commit 4b40fd2e) — volá se `window.__M2W.go('<screen>')`. To NENÍ JS most
//  `window.STRATEGIE` (ten má jen Android), ale funkce, kterou si definuje sám web,
//  takže ji WKWebView umí zavolat přes evaluateJavaScript úplně stejně.
//

import UIKit
import UserNotifications
import WebKit

final class PushDelegate: NSObject, UIApplicationDelegate, UNUserNotificationCenterDelegate {

    static let shared = PushDelegate()

    /// WebView, na kterém se provádí skok z notifikace. Registruje ho ContentView.
    weak var web: WKWebView?

    /// Obrazovka z notifikace, kterou nelze otevřít hned, protože stránka ještě
    /// není načtená (appka právě startuje). Provede se po `didFinish` — stejně
    /// jako Android čeká na `onPageFinished`.
    private var cekajiciObrazovka: String?

    /// Aby se o povolení nežádalo při každém načtení stránky.
    private var jizZadanoOPovoleni = false

    private let adresaRegistrace = "https://strategie-ai.com/api/v1/erp/app/ios/push/register"

    /// Seznam čekajících příkazů — používá se ke srovnání notifikační lišty
    /// se skutečností (viz `synchronizovatNotifikace`).
    private let adresaPending = "https://strategie-ai.com/api/v1/erp/app/mobile/commands/pending"

    // MARK: - Start appky

    func application(_ application: UIApplication,
                     didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]? = nil) -> Bool {
        UNUserNotificationCenter.current().delegate = self
        return true
    }

    /// Návrat do popředí — srovnat notifikační lištu se skutečností.
    /// ⚠️ U SwiftUI appky s `@UIApplicationDelegateAdaptor` se tahle metoda spolehlivě
    /// NEVOLÁ (ověřeno 24. 8. 2026 na fyzickém iPhonu — proto zůstával odznak viset
    /// na starém čísle). Skutečný spouštěč je `scenePhase == .active` v `mobileApp.swift`;
    /// tohle necháváme jen jako neškodnou pojistku, kdyby se to na nějaké verzi iOS chovalo jinak.
    func applicationDidBecomeActive(_ application: UIApplication) {
        synchronizovatNotifikace()
    }

    // MARK: - Povolení a registrace u APNs

    /// Požádá o povolení notifikací a při souhlasu se zaregistruje u APNs.
    /// Volá se až po načtení webu — ne hned po startu, ať se dialog neukáže
    /// dřív, než uživatel vůbec uvidí, k čemu appka je.
    func pozadatOPovoleni() {
        guard !jizZadanoOPovoleni else { return }
        jizZadanoOPovoleni = true

        UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .badge, .sound]) { povoleno, chyba in
            if let chyba = chyba {
                NSLog("[push] žádost o povolení selhala: %@", chyba.localizedDescription)
                return
            }
            guard povoleno else {
                NSLog("[push] uživatel notifikace odmítl")
                return
            }
            DispatchQueue.main.async {
                UIApplication.shared.registerForRemoteNotifications()
            }
        }
    }

    func application(_ application: UIApplication,
                     didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data) {
        let token = deviceToken.map { String(format: "%02x", $0) }.joined()
        NSLog("[push] device token získán (%d znaků)", token.count)
        // Celý token vypisujeme JEN v ladicím buildu — v ostré verzi by neměl
        // co dělat v systémovém logu telefonu. Slouží k ověření notifikací
        // na skutečném zařízení dřív, než je hotová serverová část:
        //   python3 ~/.strategie_apns/nastroje/poslat_notifikaci.py <token>
        #if DEBUG
        NSLog("[push] LADENI — device token: %@", token)
        #endif
        odeslatTokenNaServer(token)
    }

    func application(_ application: UIApplication,
                     didFailToRegisterForRemoteNotificationsWithError error: Error) {
        // V simulátoru bez podpory push, nebo když chybí capability, je to očekávané.
        NSLog("[push] registrace u APNs selhala: %@", error.localizedDescription)
    }

    // MARK: - Odeslání tokenu na server

    /// Pošle token serveru. Identita se bere z přihlašovací cookie, kterou drží
    /// WKWebView — iOS obal nemá JS most a nepotřebuje ho; server uživatele pozná
    /// stejným způsobem jako u běžného requestu z webu.
    private func odeslatTokenNaServer(_ token: String) {
        guard let url = URL(string: adresaRegistrace) else { return }
        let telo: [String: Any] = [
            "device_token": token,
            "app_key": "mobile",
            "platform": "ios",
            "app_version": Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "",
            "device_id": UIDevice.current.identifierForVendor?.uuidString ?? ""
        ]
        pozadavekSCookies(url: url, metoda: "POST",
                          telo: try? JSONSerialization.data(withJSONObject: telo)) { _, odpoved, chyba in
            if let chyba = chyba {
                NSLog("[push] odeslání tokenu selhalo: %@", chyba.localizedDescription)
                return
            }
            guard let kod = (odpoved as? HTTPURLResponse)?.statusCode else { return }
            NSLog("[push] token odeslán, server odpověděl %d", kod)
        }
    }

    // MARK: - Srovnání notifikační lišty se skutečností

    /// Android maže notifikace příkazů, které už nejsou `pending`
    /// (`DialPollService.cancelCommandNotif`) — pozná to z pollu, který mu běží
    /// pořád. iOS na pozadí pollovat nesmí, takže to samé uděláme při každém
    /// návratu do popředí: stáhneme čekající příkazy a doručené notifikace,
    /// které mezi nimi nejsou (někdo je odbavil na počítači), smažeme.
    /// Zároveň se srovná odznak na ikoně.
    func synchronizovatNotifikace() {
        // Logování (přidáno 24. 8. 2026 při hledání chyby s odznakem) — dřív funkce
        // neměla žádnou stopu ani při úspěchu, takže nešlo poznat, jestli se vůbec
        // spustí a jestli setBadgeCount doopravdy projde. Necháváme trvale, ať se to
        // příště nemusí zjišťovat znovu (viz i mobileApp.swift, kde je hlavní příčina).
        guard let url = URL(string: adresaPending) else { return }
        pozadavekSCookies(url: url, metoda: "GET", telo: nil) { data, odpoved, chyba in
            guard let data = data,
                  let json = (try? JSONSerialization.jsonObject(with: data)) as? [String: Any],
                  let prikazy = json["commands"] as? [[String: Any]] else {
                let kod = (odpoved as? HTTPURLResponse)?.statusCode
                NSLog("[push][odznak] /commands/pending se nepodařilo přečíst — data=%@ chyba=%@ http=%@",
                      data == nil ? "nil" : "\(data!.count)B",
                      chyba?.localizedDescription ?? "-",
                      kod.map(String.init) ?? "-")
                return
            }

            var ceka = Set<Int>()
            for p in prikazy {
                if let id = p["id"] as? Int { ceka.insert(id) }
                else if let id = p["id"] as? NSNumber { ceka.insert(id.intValue) }
            }
            NSLog("[push][odznak] server hlásí %d čekajících příkazů", ceka.count)

            let centrum = UNUserNotificationCenter.current()
            centrum.getDeliveredNotifications { doruceno in
                let kSmazani = doruceno.compactMap { n -> String? in
                    let info = n.request.content.userInfo
                    let cid = (info["cmd_id"] as? Int) ?? (info["cmd_id"] as? NSNumber)?.intValue
                    guard let cid = cid else { return nil }   // cizí notifikace nechat být
                    return ceka.contains(cid) ? nil : n.request.identifier
                }
                if !kSmazani.isEmpty {
                    centrum.removeDeliveredNotifications(withIdentifiers: kSmazani)
                    NSLog("[push] smazáno %d notifikací k vyřízeným příkazům", kSmazani.count)
                }
                DispatchQueue.main.async {
                    centrum.setBadgeCount(ceka.count) { chybaOdznaku in
                        if let chybaOdznaku = chybaOdznaku {
                            NSLog("[push][odznak] setBadgeCount(%d) SELHALO: %@", ceka.count, chybaOdznaku.localizedDescription)
                        } else {
                            NSLog("[push][odznak] setBadgeCount(%d) OK, appka teď hlásí applicationIconBadgeNumber=%d",
                                  ceka.count, UIApplication.shared.applicationIconBadgeNumber)
                        }
                    }
                }
            }
        }
    }

    /// Request na server s přihlašovací cookie z WebView. iOS obal nemá JS most
    /// ani vlastní token — server pozná uživatele stejně jako u requestu z webu.
    private func pozadavekSCookies(url: URL, metoda: String, telo: Data?,
                                   hotovo: @escaping (Data?, URLResponse?, Error?) -> Void) {
        WKWebsiteDataStore.default().httpCookieStore.getAllCookies { cookies in
            let naseCookies = cookies.filter { $0.domain.contains("strategie-ai.com") }
            guard !naseCookies.isEmpty else {
                NSLog("[push] %@ přeskočen — uživatel není přihlášen (žádná cookie)", url.path)
                hotovo(nil, nil, nil)
                return
            }
            var request = URLRequest(url: url)
            request.httpMethod = metoda
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            request.setValue("STRATEGIE-iOS", forHTTPHeaderField: "X-STRATEGIE-Client")
            for (hlavicka, hodnota) in HTTPCookie.requestHeaderFields(with: naseCookies) {
                request.setValue(hodnota, forHTTPHeaderField: hlavicka)
            }
            request.httpBody = telo
            URLSession.shared.dataTask(with: request, completionHandler: hotovo).resume()
        }
    }

    // MARK: - Příchozí notifikace

    /// Notifikace dorazila, když je appka na popředí — chceme ji ukázat i tak,
    /// protože iOS by ji jinak potichu zahodil.
    func userNotificationCenter(_ center: UNUserNotificationCenter,
                                willPresent notification: UNNotification,
                                withCompletionHandler completionHandler: @escaping (UNNotificationPresentationOptions) -> Void) {
        completionHandler([.banner, .list, .sound])
    }

    /// Uživatel na notifikaci ťukl.
    func userNotificationCenter(_ center: UNUserNotificationCenter,
                                didReceive response: UNNotificationResponse,
                                withCompletionHandler completionHandler: @escaping () -> Void) {
        let obsah = response.notification.request.content.userInfo
        NSLog("[push] ťuknutí na notifikaci, typ=%@ screen=%@",
              (obsah["type"] as? String) ?? "-", (obsah["screen"] as? String) ?? "-")
        // Pořadí jako na Androidu (CommandActivity): u open_url vede notifikace
        // na konkrétní adresu, jinak se skáče na obrazovku podle payload.screen.
        if (obsah["type"] as? String) == "open_url",
           let adresa = obsah["url"] as? String, let cil = URL(string: adresa) {
            otevritAdresu(cil)
        } else if let obrazovka = obsah["screen"] as? String, !obrazovka.isEmpty {
            otevritObrazovku(obrazovka)
        }
        // Odbavený příkaz zmizí z pending → sesouhlasit lištu i odznak.
        synchronizovatNotifikace()
        completionHandler()
    }

    // MARK: - Skok na obrazovku

    /// Přepne web na obrazovku podle názvu z notifikace. Když stránka ještě není
    /// načtená, skok se schová a provede se po `strankaNactena()`.
    func otevritObrazovku(_ obrazovka: String) {
        let bezpecna = String(obrazovka.filter { $0.isLetter || $0.isNumber || $0 == "_" }.prefix(40))
        guard !bezpecna.isEmpty else { return }

        guard let web = web, !web.isLoading, web.url != nil else {
            NSLog("[push] stránka není načtená, skok na %@ odložen", bezpecna)
            cekajiciObrazovka = bezpecna
            return
        }
        provestSkok(bezpecna, web: web)
    }

    /// Notifikace typu `open_url` — otevřít adresu rovnou ve WebView, ať
    /// uživatel neskončí v Safari mimo appku.
    private func otevritAdresu(_ cil: URL) {
        guard let web = web else {
            NSLog("[push] open_url %@ zahozen — WebView ještě není", cil.absoluteString)
            return
        }
        DispatchQueue.main.async { web.load(URLRequest(url: cil)) }
    }

    /// Hlásí ContentView po dokončení navigace. Odloženou obrazovku pustíme s malou
    /// prodlevou, ať web stihne dojet inicializaci `window.__M2W` (Android čeká 700 ms).
    func strankaNactena() {
        // O povolení se žádá při každém načtení — vlastní pojistka uvnitř zajistí,
        // že se dialog ukáže jen jednou za běh appky.
        pozadatOPovoleni()

        guard let obrazovka = cekajiciObrazovka, let web = web else { return }
        cekajiciObrazovka = nil
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.7) { [weak self] in
            self?.provestSkok(obrazovka, web: web)
        }
    }

    private func provestSkok(_ obrazovka: String, web: WKWebView) {
        let js = "(window.__M2W&&window.__M2W.go?window.__M2W.go('\(obrazovka)'):false)"
        web.evaluateJavaScript(js) { vysledek, chyba in
            if let chyba = chyba {
                NSLog("[push] skok na obrazovku %@ selhal: %@", obrazovka, chyba.localizedDescription)
            } else if (vysledek as? Bool) == false {
                // Web zatím nemá window.__M2W — typicky nepřihlášený telefon.
                NSLog("[push] skok na %@ neproveden — web nenabízí __M2W (nepřihlášen?)", obrazovka)
            } else {
                NSLog("[push] skok na obrazovku %@ proveden", obrazovka)
            }
        }
    }
}
