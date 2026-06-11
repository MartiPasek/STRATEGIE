
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
