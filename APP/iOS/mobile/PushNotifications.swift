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

    // MARK: - Start appky

    func application(_ application: UIApplication,
                     didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]? = nil) -> Bool {
        UNUserNotificationCenter.current().delegate = self
        return true
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

        WKWebsiteDataStore.default().httpCookieStore.getAllCookies { cookies in
            let naseCookies = cookies.filter { $0.domain.contains("strategie-ai.com") }
            guard !naseCookies.isEmpty else {
                NSLog("[push] token neodeslán — uživatel není přihlášen (žádná cookie)")
                return
            }

            var request = URLRequest(url: url)
            request.httpMethod = "POST"
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            request.setValue("STRATEGIE-iOS", forHTTPHeaderField: "X-STRATEGIE-Client")
            for (hlavicka, hodnota) in HTTPCookie.requestHeaderFields(with: naseCookies) {
                request.setValue(hodnota, forHTTPHeaderField: hlavicka)
            }

            let telo: [String: Any] = [
                "device_token": token,
                "app_key": "mobile",
                "platform": "ios",
                "app_version": Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "",
                "device_id": UIDevice.current.identifierForVendor?.uuidString ?? ""
            ]
            request.httpBody = try? JSONSerialization.data(withJSONObject: telo)

            URLSession.shared.dataTask(with: request) { _, odpoved, chyba in
                if let chyba = chyba {
                    NSLog("[push] odeslání tokenu selhalo: %@", chyba.localizedDescription)
                    return
                }
                let kod = (odpoved as? HTTPURLResponse)?.statusCode ?? 0
                NSLog("[push] token odeslán, server odpověděl %d", kod)
            }.resume()
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
        if let obrazovka = obsah["screen"] as? String, !obrazovka.isEmpty {
            otevritObrazovku(obrazovka)
        }
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
