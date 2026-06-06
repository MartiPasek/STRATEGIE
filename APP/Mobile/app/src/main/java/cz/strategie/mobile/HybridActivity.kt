package cz.strategie.mobile

import android.annotation.SuppressLint
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.util.Log
import android.webkit.JavascriptInterface
import android.webkit.WebChromeClient
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Toast
import androidx.activity.ComponentActivity
import java.net.URL
import javax.net.ssl.HttpsURLConnection

/**
 * Hybridní obrazovka (Temu model): WebView načte /mobile (web-first obsah) a přes
 * JS most `window.STRATEGIE` vystaví nativní funkce telefonu. /mobile zároveň běží
 * jako čistá PWA v prohlížeči (tam most chybí → ladná degradace). Marti 6.6.2026 (POC).
 *
 * Bezpečnost: most je aktivní jen v této appce nad naším originem; rozšiřovat ho
 * opatrně (každá metoda = nový přístup k zařízení).
 */
class HybridActivity : ComponentActivity() {

    private val prefsName = DialPollService.PREFS
    private val keyUrl = DialPollService.KEY_URL
    private val keyToken = DialPollService.KEY_TOKEN
    private val defUrl = DialPollService.DEFAULT_URL

    private fun base(): String {
        val p = getSharedPreferences(prefsName, MODE_PRIVATE)
        return (p.getString(keyUrl, defUrl) ?: defUrl).trim().trimEnd('/')
    }

    inner class Bridge {
        @JavascriptInterface
        fun dial(number: String) {
            val n = number.trim()
            if (n.isEmpty()) return
            try {
                startActivity(
                    Intent(Intent.ACTION_DIAL, Uri.parse("tel:$n"))
                        .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                )
            } catch (e: Exception) {
            }
        }

        @JavascriptInterface
        fun listening(): String {
            val p = getSharedPreferences(prefsName, MODE_PRIVATE)
            return if (p.getBoolean("service_enabled", false)) "1" else "0"
        }

        @JavascriptInterface
        fun version(): String = BuildConfig.VERSION_NAME

        @JavascriptInterface
        fun toast(msg: String) {
            runOnUiThread { Toast.makeText(this@HybridActivity, msg, Toast.LENGTH_SHORT).show() }
        }

        // Allowlist alias (Marti-AI) — pojmenovaná akce vytáčení.
        @JavascriptInterface
        fun dialNumber(number: String) = dial(number)

        // Autentizovaný fetch — token jde JEN v Authorization headeru (NE do DOM/JS;
        // drží doktrínu „login UPN je secret"). Vrací tělo odpovědi jako text.
        // method = GET/POST, path = /api/v1/erp/...  Marti 6.6.2026.
        @JavascriptInterface
        fun authedFetch(method: String, path: String, body: String): String {
            Log.d("STRATEGIE.bridge", "authedFetch $method $path")
            return try {
                val con = URL(base() + path).openConnection() as HttpsURLConnection
                con.requestMethod = method.uppercase()
                val tok = getSharedPreferences(prefsName, MODE_PRIVATE).getString(keyToken, "") ?: ""
                if (tok.isNotEmpty()) con.setRequestProperty("Authorization", "Bearer $tok")
                con.connectTimeout = 8000
                con.readTimeout = 8000
                if (method.equals("POST", true)) {
                    con.doOutput = true
                    con.setRequestProperty("Content-Type", "application/json")
                    con.outputStream.use { it.write(body.toByteArray()) }
                }
                val code = con.responseCode
                val s = if (code in 200..299) con.inputStream else con.errorStream
                s?.bufferedReader()?.use { it.readText() } ?: ""
            } catch (e: Exception) {
                ""
            }
        }
    }

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val web = WebView(this)
        web.settings.javaScriptEnabled = true
        web.settings.domStorageEnabled = true
        web.settings.databaseEnabled = true
        web.addJavascriptInterface(Bridge(), "STRATEGIE")
        web.webChromeClient = WebChromeClient()
        web.webViewClient = object : WebViewClient() {
            @Deprecated("Deprecated in Java")
            override fun shouldOverrideUrlLoading(v: WebView?, url: String?): Boolean {
                val u = url ?: return false
                if (u.startsWith("tel:") || u.startsWith("mailto:") || u.startsWith("sms:")) {
                    try {
                        startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(u)))
                    } catch (e: Exception) {
                    }
                    return true
                }
                return false
            }
        }
        setContentView(web)
        web.loadUrl(base() + "/mobile")
    }
}
