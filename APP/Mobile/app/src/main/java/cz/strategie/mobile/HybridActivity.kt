package cz.strategie.mobile

import android.Manifest
import android.annotation.SuppressLint
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.provider.CallLog
import android.provider.ContactsContract
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
import org.json.JSONArray
import org.json.JSONObject

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

    private fun granted(p: String) = checkSelfPermission(p) == PackageManager.PERMISSION_GRANTED
    private fun prefixList(csv: String): List<String> {
        val l = csv.split(",").map { it.trim().uppercase() }.filter { it.isNotEmpty() }
        return if (l.isEmpty()) listOf("STR", "EC") else l
    }
    private fun nameMatches(name: String?, prefixes: List<String>): Boolean {
        val n = (name ?: "").trim().uppercase()
        return n.isNotEmpty() && prefixes.any { n.startsWith(it) }
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

        // Kontakty s nastavitelným prefixem (default STR,EC). Nepřiřazené (mimo
        // prefix) se NEvrací (Marti-AI: data-leak dovnitř). Runtime consent dialog.
        @JavascriptInterface
        fun getContacts(prefixesCsv: String): String {
            Log.d("STRATEGIE.bridge", "getContacts")
            if (!granted(Manifest.permission.READ_CONTACTS)) {
                runOnUiThread { try { requestPermissions(arrayOf(Manifest.permission.READ_CONTACTS), 11) } catch (e: Exception) {} }
                return "{\"need\":\"contacts\"}"
            }
            val prefixes = prefixList(prefixesCsv)
            val arr = JSONArray()
            try {
                val cur = contentResolver.query(
                    ContactsContract.CommonDataKinds.Phone.CONTENT_URI,
                    arrayOf(ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME, ContactsContract.CommonDataKinds.Phone.NUMBER),
                    null, null, ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME + " ASC"
                )
                cur?.use { c ->
                    val seen = HashSet<String>()
                    while (c.moveToNext()) {
                        val nm = c.getString(0); val num = c.getString(1)
                        if (nameMatches(nm, prefixes) && seen.add((nm ?: "") + "|" + (num ?: ""))) {
                            arr.put(JSONObject().put("name", nm ?: "").put("number", num ?: ""))
                        }
                    }
                }
            } catch (e: Exception) {}
            return JSONObject().put("contacts", arr).toString()
        }

        // Protokol hovorů — jen záznamy s nakešovaným jménem dle prefixu (STR,EC).
        @JavascriptInterface
        fun getCallLog(prefixesCsv: String): String {
            Log.d("STRATEGIE.bridge", "getCallLog")
            if (!granted(Manifest.permission.READ_CALL_LOG)) {
                runOnUiThread { try { requestPermissions(arrayOf(Manifest.permission.READ_CALL_LOG), 12) } catch (e: Exception) {} }
                return "{\"need\":\"calllog\"}"
            }
            val prefixes = prefixList(prefixesCsv)
            val arr = JSONArray()
            try {
                val cur = contentResolver.query(
                    CallLog.Calls.CONTENT_URI,
                    arrayOf(CallLog.Calls.CACHED_NAME, CallLog.Calls.NUMBER, CallLog.Calls.TYPE, CallLog.Calls.DATE, CallLog.Calls.DURATION),
                    null, null, CallLog.Calls.DATE + " DESC"
                )
                cur?.use { c ->
                    var n = 0
                    while (c.moveToNext() && n < 200) {
                        val nm = c.getString(0)
                        if (nameMatches(nm, prefixes)) {
                            arr.put(JSONObject().put("name", nm ?: "").put("number", c.getString(1) ?: "")
                                .put("type", c.getInt(2)).put("date", c.getLong(3)).put("duration", c.getLong(4)))
                            n++
                        }
                    }
                }
            } catch (e: Exception) {}
            return JSONObject().put("calls", arr).toString()
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
