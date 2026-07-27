# R8 / ProGuard pravidla pro release build (Jirka, 27.7.2026).
#
# Kontext: Google Play u vydani 1.74 doporucil "Optimalizaci R8 muzete zlepsit
# pamet a vykon aplikace". R8 se zapina v app/build.gradle.kts
# (release { optimization { enable = true } }).
#
# ⚠️ KRITICKE: appka je WebView hybrid. Cely /mobile web komunikuje s nativni
# vrstvou pres JS most `window.STRATEGIE.<metoda>()` = HybridActivity.Bridge
# s 33 metodami oznacenymi @JavascriptInterface. Ty se volaji JMENEM z
# JavaScriptu, takze je zadny staticky analyzator nevidi jako pouzite.
# Bez keep pravidel nize je R8 prejmenuje nebo vyhodi a appka se rozbije
# (web zavola STRATEGIE.neco() -> undefined). Nemazat.

# --- JS most: nechat nazvy VSECH @JavascriptInterface metod ---------------
-keepclassmembers class * {
    @android.webkit.JavascriptInterface <methods>;
}

# --- JS most: nechat samotnou tridu Bridge (vcetne jejich clenu) ----------
# addJavascriptInterface(Bridge(), "STRATEGIE") v HybridActivity
-keep class cz.strategie.mobile.HybridActivity$Bridge { *; }

# --- Komponenty deklarovane v manifestu ------------------------------------
# (AGP je drzi pres aapt_rules, tohle je pojistka pri zmene manifestu)
-keep class cz.strategie.mobile.HybridActivity { *; }
-keep class cz.strategie.mobile.DialActivity { *; }
-keep class cz.strategie.mobile.PairActivity { *; }
-keep class cz.strategie.mobile.CommandActivity { *; }
-keep class cz.strategie.mobile.DialPollService { *; }
-keep class cz.strategie.mobile.NotifListener { *; }
-keep class cz.strategie.mobile.BootReceiver { *; }

# --- ML Kit / QR skener: registrary se vytvareji REFLEXI ------------------
# MlKitComponentDiscoveryService cte z manifestu meta-data
#   com.google.firebase.components:com.google.mlkit.common.internal.CommonComponentRegistrar
#   com.google.firebase.components:com.google.mlkit.vision.common.internal.VisionCommonRegistrar
# a instancuje je pres bezparametrovy konstruktor. R8 ten konstruktor odstranil
# -> v logcatu "NoSuchMethodException: ...Registrar.<init>" a QR parovani
# (Bridge.scanPairQr) prestalo fungovat. ZMERENO NA EMULATORU 27.7.2026 —
# neni to teoreticke riziko, opravdu se to stalo. Nemazat.
-keep class * implements com.google.firebase.components.ComponentRegistrar {
    <init>();
}
-keep class com.google.mlkit.** { *; }

# --- Zachovat radky v stacktrace (analyza padu v Play Console) -------------
-keepattributes SourceFile,LineNumberTable
-renamesourcefileattribute SourceFile

# Pozn.: Compose, Coil, play-services-code-scanner a androidx si vlastni
# consumer-proguard pravidla prinaseji samy (v AAR), nemusime je opisovat.
