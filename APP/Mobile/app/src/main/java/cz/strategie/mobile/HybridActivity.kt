package cz.strategie.mobile

import android.Manifest
import android.annotation.SuppressLint
import android.content.ContentUris
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.provider.CallLog
import android.provider.ContactsContract
import android.telephony.SmsManager
import android.os.Build
import android.os.Bundle
import android.util.Log
import android.webkit.JavascriptInterface
import android.webkit.WebChromeClient
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.OnBackPressedCallback
import com.google.mlkit.vision.codescanner.GmsBarcodeScanning
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
    private lateinit var web: WebView
    // Marti 7.6. večer: podržený getUserMedia požadavek (mikrofon) — grant až
    // po udělení runtime permission. deny() si WebView pamatuje → mic „nereaguje".
    private var pendingMicReq: android.webkit.PermissionRequest? = null

    override fun onRequestPermissionsResult(
        requestCode: Int, permissions: Array<out String>, grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == 14) {
            val req = pendingMicReq
            pendingMicReq = null
            if (req != null) {
                try {
                    if (grantResults.isNotEmpty() &&
                        grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                        req.grant(arrayOf(android.webkit.PermissionRequest.RESOURCE_AUDIO_CAPTURE))
                    } else req.deny()
                } catch (e: Exception) {}
            }
        }
    }

    private fun base(): String {
        val p = getSharedPreferences(prefsName, MODE_PRIVATE)
        return (p.getString(keyUrl, defUrl) ?: defUrl).trim().trimEnd('/')
    }

    private fun granted(p: String) = checkSelfPermission(p) == PackageManager.PERMISSION_GRANTED
    private fun prefixList(csv: String): List<String> {
        // BEZ uppercase — prefix přesně jak je zadán (STR ≠ str). Marti 6.6.2026.
        val l = csv.split(",").map { it.trim() }.filter { it.isNotEmpty() }
        return if (l.isEmpty()) listOf("STR", "EC") else l
    }
    private fun nameMatches(name: String?, prefixes: List<String>): Boolean {
        // Case-SENSITIVE: "STR" matchne jen "STR…", ne "str…".
        val n = (name ?: "").trim()
        return n.isNotEmpty() && prefixes.any { n.startsWith(it) }
    }
    // Foto z WhatsAppu (když kontakt nemá vlastní avatar). WhatsApp ukládá profilovou
    // fotku jako Data řádek s vlastní mimetype; otevřeme ji jako stream → base64. Marti 6.6.2026.
    private fun whatsAppPhoto(contactId: Long): String? {
        if (contactId <= 0L) return null
        for (mime in arrayOf(
            "vnd.android.cursor.item/vnd.com.whatsapp.profile.picture",
            "vnd.android.cursor.item/vnd.com.whatsapp.w4b.profile.picture"
        )) {
            try {
                val q = contentResolver.query(
                    ContactsContract.Data.CONTENT_URI,
                    arrayOf(ContactsContract.Data._ID),
                    ContactsContract.Data.CONTACT_ID + "=? AND " + ContactsContract.Data.MIMETYPE + "=?",
                    arrayOf(contactId.toString(), mime), null
                )
                q?.use { d ->
                    if (d.moveToFirst()) {
                        val dataId = d.getLong(0)
                        val uri = ContentUris.withAppendedId(ContactsContract.Data.CONTENT_URI, dataId)
                        contentResolver.openInputStream(uri)?.use { ins ->
                            val bytes = ins.readBytes()
                            if (bytes.isNotEmpty())
                                return "data:image/jpeg;base64," + android.util.Base64.encodeToString(bytes, android.util.Base64.NO_WRAP)
                        }
                    }
                }
            } catch (e: Exception) {}
        }
        return null
    }

    private fun notifAccessEnabled(): Boolean {
        return try {
            val flat = android.provider.Settings.Secure.getString(contentResolver, "enabled_notification_listeners") ?: ""
            flat.contains("$packageName/$packageName.NotifListener") || flat.contains("$packageName/.NotifListener")
        } catch (e: Exception) { false }
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

        // Stabilní ID tohoto telefonu (shodné s tím, co hlásí služba do
        // fw.mobile_device) — pro ověření čísla navázané na zařízení.
        @JavascriptInterface
        fun deviceId(): String {
            val p = getSharedPreferences(prefsName, MODE_PRIVATE)
            var id = p.getString(DialPollService.KEY_DEVICE_ID, null)
            if (id.isNullOrBlank()) {
                id = java.util.UUID.randomUUID().toString()
                p.edit().putString(DialPollService.KEY_DEVICE_ID, id).apply()
            }
            return id
        }

        // Poslední příchozí vytočení z ERP (do ~2 min) — pro kartu „Zavolat" na
        // hlavní obrazovce, ať to uživatel vidí i v appce, ne jen v notifikaci.
        @JavascriptInterface
        fun lastDial(): String {
            return try {
                val s = getSharedPreferences(prefsName, MODE_PRIVATE)
                    .getString(DialPollService.KEY_LAST_DIAL, "") ?: ""
                if (s.isBlank()) return ""
                val o = org.json.JSONObject(s)
                val ts = o.optLong("ts", 0L)
                if (System.currentTimeMillis() - ts > 120000L) "" else s
            } catch (e: Exception) { "" }
        }

        @JavascriptInterface
        fun clearLastDial() {
            try {
                val p = getSharedPreferences(prefsName, MODE_PRIVATE)
                // Zruš i systémovou notifikaci vytáčení (akce proběhla v appce).
                val s = p.getString(DialPollService.KEY_LAST_DIAL, "") ?: ""
                if (s.isNotBlank()) {
                    try {
                        val nid = org.json.JSONObject(s).optInt("nid", -1)
                        if (nid > 0) (getSystemService(android.app.NotificationManager::class.java)).cancel(nid)
                    } catch (e: Exception) {}
                }
                p.edit().remove(DialPollService.KEY_LAST_DIAL).apply()
            } catch (e: Exception) {}
        }

        // Číslo telefonu přímo ze SIM (bez SMS brány). Nemusí být dostupné u všech
        // operátorů/SIM → pak vrátí "" a uživatel ho zadá ručně. Vyžádá READ_PHONE_NUMBERS.
        @JavascriptInterface
        fun simNumber(): String {
            return try {
                if (checkSelfPermission(Manifest.permission.READ_PHONE_NUMBERS) != PackageManager.PERMISSION_GRANTED) {
                    runOnUiThread { try { requestPermissions(arrayOf(Manifest.permission.READ_PHONE_NUMBERS), 45) } catch (e: Exception) {} }
                    return ""
                }
                val tm = getSystemService(android.telephony.TelephonyManager::class.java)
                @Suppress("DEPRECATION", "HardwareIds")
                (tm?.line1Number ?: "").trim()
            } catch (e: Exception) { "" }
        }

        // (ponecháno) Ověření čísla přes SMS — fallback, hlavní cesta je simNumber + uložení.
        // STRATEGIE; server z odesílatele přečte reálné číslo. Vyžádá SEND_SMS.
        @JavascriptInterface
        fun sendSms(number: String, body: String): String {
            val n = number.trim(); val b = body.trim()
            if (n.isEmpty() || b.isEmpty()) return "0"
            if (checkSelfPermission(Manifest.permission.SEND_SMS) != PackageManager.PERMISSION_GRANTED) {
                runOnUiThread { try { requestPermissions(arrayOf(Manifest.permission.SEND_SMS), 44) } catch (e: Exception) {} }
                return "need"
            }
            return try {
                val sm = if (Build.VERSION.SDK_INT >= 31)
                    getSystemService(SmsManager::class.java)
                else @Suppress("DEPRECATION") SmsManager.getDefault()
                sm.sendTextMessage(n, null, b, null, null)
                "1"
            } catch (e: Exception) { "0" }
        }

        @JavascriptInterface
        fun toast(msg: String) {
            runOnUiThread { Toast.makeText(this@HybridActivity, msg, Toast.LENGTH_SHORT).show() }
        }

        // Marti 8.6.: SMS brána — JEN tento telefon (Marti-AI mobil) přeposílá
        // příchozí ověřovací SMS. Vyžádá RECEIVE_SMS permission. Vrátí stav.
        @JavascriptInterface
        fun setSmsGateway(enabled: Boolean): String {
            getSharedPreferences(prefsName, MODE_PRIVATE).edit()
                .putBoolean("sms_gateway", enabled).apply()
            if (enabled && !granted(Manifest.permission.RECEIVE_SMS)) {
                runOnUiThread { try { requestPermissions(arrayOf(Manifest.permission.RECEIVE_SMS), 45) } catch (e: Exception) {} }
                return "need"
            }
            return if (enabled) "1" else "0"
        }

        @JavascriptInterface
        fun isSmsGateway(): Boolean =
            getSharedPreferences(prefsName, MODE_PRIVATE).getBoolean("sms_gateway", false)

        // Allowlist alias (Marti-AI) — pojmenovaná akce vytáčení.
        @JavascriptInterface
        fun dialNumber(number: String) = dial(number)

        // Otevři nativní telefonní klávesnici (prázdný dialer) — pro ruční vytočení.
        @JavascriptInterface
        fun openDialpad() {
            runOnUiThread {
                try { startActivity(Intent(Intent.ACTION_DIAL).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)) } catch (e: Exception) {}
            }
        }

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
            val showAll = prefixesCsv.trim() == "*"   // „*" = všechny kontakty (Marti 6.6.)
            val prefixes = prefixList(prefixesCsv)
            val arr = JSONArray()
            try {
                val cur = contentResolver.query(
                    ContactsContract.CommonDataKinds.Phone.CONTENT_URI,
                    arrayOf(ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME, ContactsContract.CommonDataKinds.Phone.NUMBER,
                        ContactsContract.CommonDataKinds.Phone.PHOTO_THUMBNAIL_URI, ContactsContract.CommonDataKinds.Phone.CONTACT_ID),
                    null, null, ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME + " ASC"
                )
                cur?.use { c ->
                    val seen = HashSet<String>()
                    while (c.moveToNext()) {
                        val nm = c.getString(0); val num = c.getString(1); val photoUri = c.getString(2); val contactId = c.getLong(3)
                        if ((showAll || nameMatches(nm, prefixes)) && seen.add((nm ?: "") + "|" + (num ?: ""))) {
                            val o = JSONObject().put("name", nm ?: "").put("number", num ?: "")
                            // Fotky načítáme jen u prefix-filtru (malý seznam). U „Vše"
                            // (stovky kontaktů) by per-kontakt foto + WhatsApp dotaz byly
                            // extrémně pomalé → vynecháme (zobrazí se písmenkové avatary).
                            if (!showAll) {
                                var photo: String? = null
                                if (!photoUri.isNullOrBlank()) {
                                    try {
                                        contentResolver.openInputStream(Uri.parse(photoUri))?.use { ins ->
                                            val bytes = ins.readBytes()
                                            if (bytes.isNotEmpty()) photo = "data:image/jpeg;base64," + android.util.Base64.encodeToString(bytes, android.util.Base64.NO_WRAP)
                                        }
                                    } catch (e: Exception) {}
                                }
                                // Fallback: když kontakt nemá vlastní avatar, zkus WhatsApp profilovku.
                                if (photo == null) photo = whatsAppPhoto(contactId)
                                if (photo != null) o.put("photo", photo)
                            }
                            arr.put(o)
                        }
                    }
                }
            } catch (e: Exception) {}
            return JSONObject().put("contacts", arr).toString()
        }

        // Otevři nativní detail kontaktu (přes celý displej) podle čísla. Marti 6.6.2026.
        @JavascriptInterface
        fun openContact(number: String) {
            val n = number.trim()
            if (n.isEmpty()) return
            runOnUiThread {
                try {
                    var contactUri: Uri? = null
                    if (granted(Manifest.permission.READ_CONTACTS)) {
                        val lookup = Uri.withAppendedPath(
                            ContactsContract.PhoneLookup.CONTENT_FILTER_URI, Uri.encode(n))
                        contentResolver.query(lookup,
                            arrayOf(ContactsContract.PhoneLookup.LOOKUP_KEY, ContactsContract.PhoneLookup._ID),
                            null, null, null)?.use { c ->
                            if (c.moveToFirst()) {
                                contactUri = ContactsContract.Contacts.getLookupUri(c.getLong(1), c.getString(0))
                            }
                        }
                    }
                    val intent = if (contactUri != null)
                        Intent(Intent.ACTION_VIEW, contactUri)
                    else
                        Intent(Intent.ACTION_VIEW, Uri.parse("tel:$n"))  // fallback
                    startActivity(intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
                } catch (e: Exception) {}
            }
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

        // Historie SMS — stejný vzor jako getCallLog (Marti 7.6.2026): jen zprávy
        // od/pro kontakty se jménem dle prefixu (STR,EC). Jméno se dohledává přes
        // PhoneLookup (SMS provider jména nekešuje), per-číslo cache.
        @JavascriptInterface
        fun getSmsLog(prefixesCsv: String): String {
            Log.d("STRATEGIE.bridge", "getSmsLog")
            if (!granted(Manifest.permission.READ_SMS)) {
                runOnUiThread { try { requestPermissions(arrayOf(Manifest.permission.READ_SMS), 13) } catch (e: Exception) {} }
                return "{\"need\":\"sms\"}"
            }
            val prefixes = prefixList(prefixesCsv)
            val arr = JSONArray()
            val nameCache = HashMap<String, String?>()
            fun lookupName(num: String): String? {
                if (num.isEmpty() || !granted(Manifest.permission.READ_CONTACTS)) return null
                if (!nameCache.containsKey(num)) {
                    var nm: String? = null
                    try {
                        val lookup = Uri.withAppendedPath(
                            ContactsContract.PhoneLookup.CONTENT_FILTER_URI, Uri.encode(num))
                        contentResolver.query(lookup,
                            arrayOf(ContactsContract.PhoneLookup.DISPLAY_NAME),
                            null, null, null)?.use { c ->
                            if (c.moveToFirst()) nm = c.getString(0)
                        }
                    } catch (e: Exception) {}
                    nameCache[num] = nm
                }
                return nameCache[num]
            }
            try {
                val cur = contentResolver.query(
                    Uri.parse("content://sms"),
                    arrayOf("address", "body", "type", "date"),
                    null, null, "date DESC"
                )
                cur?.use { c ->
                    var n = 0
                    while (c.moveToNext() && n < 200) {
                        val num = c.getString(0) ?: ""
                        val nm = lookupName(num)
                        if (nameMatches(nm, prefixes)) {
                            var body = c.getString(1) ?: ""
                            if (body.length > 160) body = body.substring(0, 160) + "…"
                            arr.put(JSONObject().put("name", nm ?: "").put("number", num)
                                .put("body", body).put("type", c.getInt(2)).put("date", c.getLong(3)))
                            n++
                        }
                    }
                }
            } catch (e: Exception) {}
            return JSONObject().put("sms", arr).toString()
        }

        // Otevři externí appku/URL (launcher „Aplikace"): chat, ERP, WhatsApp…
        @JavascriptInterface
        fun openExternal(url: String) {
            val u = url.trim()
            if (u.isEmpty()) return
            runOnUiThread {
                try {
                    startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(u)).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
                } catch (e: Exception) {
                }
            }
        }

        // Počty oznámení (badge Aplikace): WhatsApp + SMS z notification listeneru.
        @JavascriptInterface
        fun appBadges(): String {
            val raw = getSharedPreferences(prefsName, MODE_PRIVATE).getString("notif_badges", "{}") ?: "{}"
            var wa = 0; var sms = 0
            try {
                val o = JSONObject(raw)
                val waPkgs = setOf("com.whatsapp", "com.whatsapp.w4b")
                val smsPkgs = setOf("com.google.android.apps.messaging", "com.samsung.android.messaging",
                    "com.android.messaging", "com.android.mms")
                val it = o.keys()
                while (it.hasNext()) {
                    val k = it.next(); val v = o.optInt(k, 0)
                    if (waPkgs.contains(k)) wa += v
                    if (smsPkgs.contains(k)) sms += v
                }
            } catch (e: Exception) {}
            return JSONObject().put("whatsapp", wa).put("sms", sms).put("total", wa + sms)
                .put("access", notifAccessEnabled()).toString()
        }

        @JavascriptInterface
        fun openNotifAccess() {
            runOnUiThread {
                try { startActivity(Intent(android.provider.Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)) } catch (e: Exception) {}
            }
        }

        // Avatar Marti-AI jako data URL (token v headeru) — pozadí hlavní obrazovky.
        @JavascriptInterface
        fun avatarDataUrl(): String {
            return try {
                val con = URL(base() + "/api/v1/erp/app/avatar").openConnection() as HttpsURLConnection
                val tok = getSharedPreferences(prefsName, MODE_PRIVATE).getString(keyToken, "") ?: ""
                if (tok.isNotEmpty()) con.setRequestProperty("Authorization", "Bearer $tok")
                con.connectTimeout = 8000
                con.readTimeout = 8000
                val bytes = con.inputStream.use { it.readBytes() }
                "data:image/jpeg;base64," + android.util.Base64.encodeToString(bytes, android.util.Base64.NO_WRAP)
            } catch (e: Exception) {
                ""
            }
        }

        // ── Verze / aktualizace / párování (O aplikaci) ──
        @JavascriptInterface
        fun buildTime(): String = BuildConfig.BUILD_TIME

        @JavascriptInterface
        fun checkUpdate(): String {
            return try {
                val con = URL(base() + "/api/v1/erp/app/mobile/latest").openConnection() as HttpsURLConnection
                val tok = getSharedPreferences(prefsName, MODE_PRIVATE).getString(keyToken, "") ?: ""
                if (tok.isNotEmpty()) con.setRequestProperty("Authorization", "Bearer $tok")
                con.connectTimeout = 8000; con.readTimeout = 8000
                val o = if (con.responseCode == 200) JSONObject(con.inputStream.bufferedReader().use { it.readText() }) else JSONObject()
                val lc = o.optInt("version_code", 0)
                JSONObject()
                    .put("current_code", BuildConfig.VERSION_CODE).put("current_name", BuildConfig.VERSION_NAME)
                    .put("build_time", BuildConfig.BUILD_TIME)
                    .put("latest_code", lc).put("latest_name", o.optString("version_name", ""))
                    .put("has_update", lc > BuildConfig.VERSION_CODE).toString()
            } catch (e: Exception) {
                JSONObject().put("current_code", BuildConfig.VERSION_CODE).put("current_name", BuildConfig.VERSION_NAME)
                    .put("build_time", BuildConfig.BUILD_TIME).put("has_update", false).put("error", true).toString()
            }
        }

        @JavascriptInterface
        fun installUpdate() {
            val b = base()
            val tok = getSharedPreferences(prefsName, MODE_PRIVATE).getString(keyToken, "") ?: ""
            runOnUiThread { Toast.makeText(this@HybridActivity, "Stahuji novou verzi…", Toast.LENGTH_SHORT).show() }
            Thread {
                try {
                    val dest = java.io.File(cacheDir, "updates/strategie-latest.apk")
                    dest.parentFile?.mkdirs()
                    val con = URL("$b/api/v1/erp/app/mobile/download").openConnection() as HttpsURLConnection
                    if (tok.isNotEmpty()) con.setRequestProperty("Authorization", "Bearer $tok")
                    con.connectTimeout = 10000; con.readTimeout = 60000
                    if (con.responseCode == 200) { con.inputStream.use { inp -> dest.outputStream().use { o -> inp.copyTo(o, 64 * 1024) } } }
                    con.disconnect()
                    if (dest.length() > 0) {
                        val uri = androidx.core.content.FileProvider.getUriForFile(this@HybridActivity, "$packageName.fileprovider", dest)
                        runOnUiThread {
                            try { startActivity(Intent(Intent.ACTION_VIEW).apply { setDataAndType(uri, "application/vnd.android.package-archive"); addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_ACTIVITY_NEW_TASK) }) } catch (e: Exception) {}
                        }
                    } else runOnUiThread { Toast.makeText(this@HybridActivity, "Stažení selhalo", Toast.LENGTH_SHORT).show() }
                } catch (e: Exception) { runOnUiThread { Toast.makeText(this@HybridActivity, "Aktualizace selhala", Toast.LENGTH_SHORT).show() } }
            }.start()
        }

        @JavascriptInterface
        fun openPairing() { openExternal(base() + "/app-pair") }

        // ── Naslouchání (foreground služba + zelená ikona) ──
        @JavascriptInterface
        fun startListening() {
            runOnUiThread {
                try {
                    if (Build.VERSION.SDK_INT >= 33 &&
                        checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
                        requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS), 33)
                    }
                    getSharedPreferences(prefsName, MODE_PRIVATE).edit().putBoolean("service_enabled", true).apply()
                    DialPollService.start(this@HybridActivity)
                    Toast.makeText(this@HybridActivity, "Párování aktivní", Toast.LENGTH_SHORT).show()
                } catch (e: Exception) {}
            }
        }

        @JavascriptInterface
        fun stopListening() {
            runOnUiThread {
                try {
                    getSharedPreferences(prefsName, MODE_PRIVATE).edit().putBoolean("service_enabled", false).apply()
                    DialPollService.stop(this@HybridActivity)
                    Toast.makeText(this@HybridActivity, "Párování pozastaveno", Toast.LENGTH_SHORT).show()
                } catch (e: Exception) {}
            }
        }

        @JavascriptInterface
        fun openBatterySettings() {
            runOnUiThread {
                try { startActivity(Intent(android.provider.Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS).setData(Uri.parse("package:$packageName"))) } catch (e: Exception) {}
            }
        }

        // Spustí nainstalovanou appku podle balíčku (WhatsApp…), jinak fallback URL.
        @JavascriptInterface
        fun openPackage(pkg: String, fallbackUrl: String) {
            runOnUiThread {
                try {
                    val i = packageManager.getLaunchIntentForPackage(pkg)
                    if (i != null) { i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK); startActivity(i) }
                    else if (fallbackUrl.isNotBlank()) startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(fallbackUrl)).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
                } catch (e: Exception) {
                    try { if (fallbackUrl.isNotBlank()) startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(fallbackUrl)).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)) } catch (e2: Exception) {}
                }
            }
        }

        // Spárování přes QR: otevře fotoaparát, naskenuje QR z ERP/PC (/app-pair),
        // uloží u+t do prefs a restartuje obrazovku. Marti 6.6.2026.
        @JavascriptInterface
        fun scanPairQr() {
            runOnUiThread {
                try {
                    GmsBarcodeScanning.getClient(this@HybridActivity).startScan()
                        .addOnSuccessListener { code ->
                            val raw = code.rawValue
                            if (raw.isNullOrBlank()) { Toast.makeText(this@HybridActivity, "Prázdný QR", Toast.LENGTH_SHORT).show(); return@addOnSuccessListener }
                            try {
                                val uri = Uri.parse(raw)
                                val u = uri.getQueryParameter("u")
                                val t = uri.getQueryParameter("t")
                                if (!u.isNullOrBlank() && !t.isNullOrBlank()) {
                                    getSharedPreferences(prefsName, MODE_PRIVATE).edit()
                                        .putString(keyUrl, u.trim()).putString(keyToken, t.trim()).apply()
                                    Toast.makeText(this@HybridActivity, "Spárováno ✓", Toast.LENGTH_SHORT).show()
                                    recreate()
                                } else Toast.makeText(this@HybridActivity, "QR neobsahuje párovací údaje", Toast.LENGTH_SHORT).show()
                            } catch (e: Exception) { Toast.makeText(this@HybridActivity, "QR se nepodařilo přečíst", Toast.LENGTH_SHORT).show() }
                        }
                        .addOnFailureListener { Toast.makeText(this@HybridActivity, "Skener QR není dostupný", Toast.LENGTH_SHORT).show() }
                } catch (e: Exception) { Toast.makeText(this@HybridActivity, "Skener QR není dostupný", Toast.LENGTH_SHORT).show() }
            }
        }
    }

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        // Náběh appky rovnou do /mobile (provizorní „jádro" už nepotřebujeme).
        // Pokud je telefon spárovaný, zapni naslouchání jako dřív MainActivity.
        try {
            val p = getSharedPreferences(prefsName, MODE_PRIVATE)
            val hasToken = !(p.getString(keyToken, "") ?: "").isBlank()
            if (Build.VERSION.SDK_INT >= 33 &&
                checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
                requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS), 33)
            }
            if (hasToken && p.getBoolean("service_enabled", true)) DialPollService.start(this)
        } catch (e: Exception) {}

        web = WebView(this)
        web.settings.javaScriptEnabled = true
        web.settings.domStorageEnabled = true
        web.settings.databaseEnabled = true
        // Vždy čerstvý /mobile (Marti 6.6.2026 — řeší zaseknutí na staré verzi UI).
        web.settings.cacheMode = android.webkit.WebSettings.LOAD_NO_CACHE
        try { web.clearCache(true) } catch (e: Exception) {}
        web.addJavascriptInterface(Bridge(), "STRATEGIE")
        // Marti 7.6.2026: mikrofon pro „Přímá zpráva pro Tvoje Marti" (audio →
        // Whisper). getUserMedia ve WebView vyžaduje grant v onPermissionRequest
        // + runtime RECORD_AUDIO permission.
        web.webChromeClient = object : WebChromeClient() {
            override fun onPermissionRequest(request: android.webkit.PermissionRequest?) {
                val req = request ?: return
                val wantsAudio = req.resources.contains(
                    android.webkit.PermissionRequest.RESOURCE_AUDIO_CAPTURE)
                if (!wantsAudio) { req.deny(); return }
                if (granted(Manifest.permission.RECORD_AUDIO)) {
                    req.grant(arrayOf(android.webkit.PermissionRequest.RESOURCE_AUDIO_CAPTURE))
                } else {
                    // Požadavek podržet a grantnout až po udělení permission —
                    // deny() si WebView pamatuje a mic by „nereagoval".
                    pendingMicReq = req
                    try { requestPermissions(arrayOf(Manifest.permission.RECORD_AUDIO), 14) }
                    catch (e: Exception) { pendingMicReq = null; req.deny() }
                }
            }
        }
        web.webViewClient = object : WebViewClient() {
            @Deprecated("Deprecated in Java")
            override fun shouldOverrideUrlLoading(v: WebView?, url: String?): Boolean {
                val u = url ?: return false
                // Spárování z /app-pair (po přihlášení) — token přijde přes vlastní
                // schéma; zachytíme ho přímo zde, uložíme a vejdeme do menu.
                if (u.startsWith("strategiemobil://")) {
                    try {
                        val uri = Uri.parse(u)
                        val su = uri.getQueryParameter("u"); val st = uri.getQueryParameter("t")
                        if (!su.isNullOrBlank() && !st.isNullOrBlank()) {
                            getSharedPreferences(prefsName, MODE_PRIVATE).edit()
                                .putString(keyUrl, su.trim()).putString(keyToken, st.trim())
                                .putBoolean("service_enabled", true).apply()
                            try { DialPollService.start(this@HybridActivity) } catch (e: Exception) {}
                            v?.post { web.loadUrl(base() + "/mobile") }
                        }
                    } catch (e: Exception) {}
                    return true
                }
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
        // Login-first (Marti 6.6.2026): nepřihlášený telefon (bez tokenu) NESMÍ do
        // menu. Nejdřív /app-pair → přihlášení do STRATEGIE → token → spárování →
        // teprve pak /mobile. Token = identita (čí telefon + jaká práva).
        val hasTok = !(getSharedPreferences(prefsName, MODE_PRIVATE)
            .getString(keyToken, "") ?: "").isBlank()
        web.loadUrl(base() + if (hasTok) "/mobile" else "/app-pair")

        // Zpět: o úroveň výš v /mobile; na hlavní obrazovce přívětivý dialog „ukončit?".
        onBackPressedDispatcher.addCallback(this, object : OnBackPressedCallback(true) {
            override fun handleOnBackPressed() {
                web.evaluateJavascript("(window.__stgBack?window.__stgBack():false)") { r ->
                    if (r != "true") confirmExit()
                }
            }
        })
    }

    // Spuštění přes ikonu v launcheru (ACTION_MAIN) → vždy hlavní obrazovka,
    // i když appka zůstala v paměti na podmenu. Marti 6.6.2026.
    override fun onNewIntent(intent: Intent?) {
        super.onNewIntent(intent)
        setIntent(intent)
        if (intent?.action == Intent.ACTION_MAIN) {
            try { web.evaluateJavascript("(window.__stgHome&&window.__stgHome())", null) } catch (e: Exception) {}
        }
    }

    private fun confirmExit() {
        try {
            android.app.AlertDialog.Builder(this)
                .setTitle("Jste doma 🏠")
                .setMessage("Opravdu chcete STRATEGII ukončit?")
                .setPositiveButton("Ukončit") { _, _ -> finish() }
                .setNegativeButton("Zůstat", null)
                .show()
        } catch (e: Exception) { finish() }
    }
}
