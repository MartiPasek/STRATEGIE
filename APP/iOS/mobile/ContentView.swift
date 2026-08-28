import SwiftUI
import WebKit

// STRATEGIE Mobil — iOS companion (WKWebView kolem https://strategie-ai.com/mobile)
// Companion princip (native_app_vize.md): PWA je nosná, appka přidává nativní kousky,
// které iOS dovolí (mikrofon pro diktování, tel: volání, pull-to-refresh).
// SMS Apple zakazuje (zůstává na Android bráně) — tady se neřeší.

struct WebView: UIViewRepresentable {
    let url: URL

    func makeCoordinator() -> Coordinator { Coordinator() }

    func makeUIView(context: Context) -> WKWebView {
        let config = WKWebViewConfiguration()
        config.allowsInlineMediaPlayback = true                       // audio/video uvnitř stránky
        config.mediaTypesRequiringUserActionForPlayback = []          // přehraj bez extra kliknutí
        config.applicationNameForUserAgent = "STRATEGIE-iOS"          // marker → web pozná nativní iOS obal (zobrazí "Nativní appka"). Kristý/Jirka 12.6., do stavěného souboru doplnil Jirka 18.8.2026
        let web = WKWebView(frame: .zero, configuration: config)
        // Gesto zpět řeší webová vrstva (10_core.js: touchstart/touchend na levém okraji,
        // volá back() nad window.__M2W.stack). Vestavěné gesto WKWebView je ZÁMĚRNĚ vypnuté —
        // jede po historii prohlížeče, ne po __M2W.stack, a protože appka drží navigaci jen
        // v paměti a všechny obrazovky mají tutéž URL, švihnutí vracelo na náhodnou starší
        // stránku. Obě gesta se pouštěla naráz. (Jirka 27. 8. 2026, schválila Marti-AI msg 13911.)
        web.allowsBackForwardNavigationGestures = false
        web.uiDelegate = context.coordinator
        web.navigationDelegate = context.coordinator

        // Pull-to-refresh (potáhni dolů = znovu načíst)
        let rc = UIRefreshControl()
        rc.addTarget(context.coordinator, action: #selector(Coordinator.reload(_:)), for: .valueChanged)
        web.scrollView.refreshControl = rc

        context.coordinator.web = web
        PushDelegate.shared.web = web                                 // skok z notifikace jde na tenhle WebView
        web.load(URLRequest(url: url))
        return web
    }

    func updateUIView(_ uiView: WKWebView, context: Context) {}

    class Coordinator: NSObject, WKUIDelegate, WKNavigationDelegate {
        weak var web: WKWebView?

        @objc func reload(_ sender: UIRefreshControl) {
            web?.reload()
            sender.endRefreshing()
        }

        // KLÍČOVÉ: mikrofon/kamera pro web (getUserMedia → diktování, hlasové zprávy).
        // Appka má povolení v Info.plist; tady ho WebView udělíme automaticky.
        // (iOS 15+) — bez tohohle by mikrofon v WKWebView „nereagoval".
        func webView(_ webView: WKWebView,
                     requestMediaCapturePermissionFor origin: WKSecurityOrigin,
                     initiatedByFrame frame: WKFrameInfo,
                     type: WKMediaCaptureType,
                     decisionHandler: @escaping (WKPermissionDecision) -> Void) {
            decisionHandler(.grant)
        }

        // Stránka dojela — teprve teď má smysl žádat o povolení notifikací a provést
        // odložený skok z notifikace (web musí mít inicializované window.__M2W).
        func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
            PushDelegate.shared.strankaNactena()
        }

        // tel: / mailto: / facetime: → otevřít nativně (dialer, mail). Zbytek nech ve WebView.
        func webView(_ webView: WKWebView,
                     decidePolicyFor navigationAction: WKNavigationAction,
                     decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
            if let u = navigationAction.request.url, let scheme = u.scheme?.lowercased(),
               ["tel", "mailto", "facetime", "facetime-audio"].contains(scheme) {
                UIApplication.shared.open(u)
                decisionHandler(.cancel)
                return
            }
            decisionHandler(.allow)
        }
    }
}

struct ContentView: View {
    var body: some View {
        WebView(url: URL(string: "https://strategie-ai.com/mobile")!)
            .ignoresSafeArea(edges: .bottom)   // web vyplní plochu, horní safe-area zůstane
    }
}

#Preview {
    ContentView()
}
