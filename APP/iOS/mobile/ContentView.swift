import SwiftUI
import WebKit

// Obal kolem webu STRATEGIE (mobile)
// Vylepšená kostra:
//  • mikrofon/kamera (diktování, getUserMedia) přes WKUIDelegate
//  • tel:/mailto:/sms:/facetime: odkazy otevřou nativní aplikaci
//  • pull-to-refresh – tažením dolů se stránka znovu načte
struct WebView: UIViewRepresentable {
    let url: URL

    func makeCoordinator() -> Coordinator {
        Coordinator(url: url)
    }

    func makeUIView(context: Context) -> WKWebView {
        let config = WKWebViewConfiguration()
        config.allowsInlineMediaPlayback = true              // video/audio přímo ve stránce
        config.mediaTypesRequiringUserActionForPlayback = [] // přehrávání bez nutného kliknutí

        let webView = WKWebView(frame: .zero, configuration: config)
        webView.allowsBackForwardNavigationGestures = true   // gesto zpět/vpřed
        webView.uiDelegate = context.coordinator             // povolení mikrofonu/kamery
        webView.navigationDelegate = context.coordinator     // tel:/mailto: odkazy

        // Pull-to-refresh – tažením dolů se stránka znovu načte
        let refresh = UIRefreshControl()
        refresh.addTarget(context.coordinator,
                          action: #selector(Coordinator.handleRefresh(_:)),
                          for: .valueChanged)
        webView.scrollView.refreshControl = refresh
        context.coordinator.webView = webView

        webView.load(URLRequest(url: url))
        return webView
    }

    func updateUIView(_ uiView: WKWebView, context: Context) {}

    // MARK: - Coordinator (delegáti WebKitu)
    final class Coordinator: NSObject, WKUIDelegate, WKNavigationDelegate {
        let url: URL
        weak var webView: WKWebView?

        init(url: URL) {
            self.url = url
        }

        // Pull-to-refresh
        @objc func handleRefresh(_ sender: UIRefreshControl) {
            webView?.reload()
        }

        // Mikrofon / kamera – povolit zachytávání médií (diktování, getUserMedia)
        func webView(_ webView: WKWebView,
                     requestMediaCapturePermissionFor origin: WKSecurityOrigin,
                     initiatedByFrame frame: WKFrameInfo,
                     type: WKMediaCaptureType,
                     decisionHandler: @escaping (WKPermissionDecision) -> Void) {
            decisionHandler(.grant)
        }

        // tel:, mailto:, sms:, facetime: → otevři nativní aplikaci místo načítání ve webu
        func webView(_ webView: WKWebView,
                     decidePolicyFor navigationAction: WKNavigationAction,
                     decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
            if let target = navigationAction.request.url,
               let scheme = target.scheme?.lowercased(),
               ["tel", "mailto", "sms", "facetime"].contains(scheme) {
                UIApplication.shared.open(target)
                decisionHandler(.cancel)
                return
            }
            decisionHandler(.allow)
        }

        // Po dokončení (i při chybě) ukonči animaci pull-to-refresh
        func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
            webView.scrollView.refreshControl?.endRefreshing()
        }

        func webView(_ webView: WKWebView, didFail navigation: WKNavigation!, withError error: Error) {
            webView.scrollView.refreshControl?.endRefreshing()
        }

        func webView(_ webView: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!, withError error: Error) {
            webView.scrollView.refreshControl?.endRefreshing()
        }
    }
}

struct ContentView: View {
    var body: some View {
        WebView(url: URL(string: "https://strategie-ai.com/mobile")!)
            .ignoresSafeArea()   // web vyplní celou plochu
    }
}

#Preview {
    ContentView()
}
