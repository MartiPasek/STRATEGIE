package cz.strategie.mobile

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.Manifest
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.media.AudioAttributes
import android.net.Uri
import android.content.pm.ServiceInfo
import android.os.Build
import android.os.IBinder
import android.provider.CallLog
import androidx.core.app.NotificationCompat
import androidx.core.content.ContextCompat
import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import kotlin.concurrent.thread

/**
 * Služba na pozadí (Marti 4.6.2026): pollne `/phone-dial-request/pending` na
 * serveru (Bearer = CardDAV token) každé ~4 s. Když přijde požadavek (PC dvojklik
 * na telefon v ERP) → high-priority notifikace „Vytočit …" s full-screen intentem
 * → DialActivity spustí dialer s číslem. Pak označí požadavek consumed.
 *
 * Android pravidlo: služba na pozadí nesmí sama spustit aktivitu (dialer) od
 * Androidu 10 — proto notifikace (jako příchozí hovor). Full-screen intent +
 * CATEGORY_CALL = nejblíž „rovnou vyskočí", co OS dovolí.
 */
class DialPollService : Service() {

    @Volatile private var running = false
    private var worker: Thread? = null
    private var cycle = 0

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onCreate() {
        super.onCreate()
        createChannels()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        startForegroundCompat()
        if (!running) {
            running = true
            worker = thread(name = "dial-poll") { pollLoop() }
        }
        return START_STICKY
    }

    override fun onDestroy() {
        running = false
        worker?.interrupt()
        worker = null
        super.onDestroy()
    }

    private fun pollLoop() {
        while (running) {
            try {
                val prefs = getSharedPreferences(PREFS, Context.MODE_PRIVATE)
                val base = (prefs.getString(KEY_URL, DEFAULT_URL) ?: DEFAULT_URL)
                    .trim().trimEnd('/')
                val token = (prefs.getString(KEY_TOKEN, "") ?: "").trim()
                if (token.isNotEmpty()) {
                    val reqs = fetchPending(base, token)
                    for (i in 0 until reqs.length()) {
                        val r = reqs.getJSONObject(i)
                        val id = r.optInt("id", -1)
                        val phone = r.optString("phone", "")
                        val label = r.optString("label", "")
                        if (id > 0 && phone.isNotEmpty()) {
                            notifyDial(id, phone, label)
                            consume(base, token, id)
                            recordPendingCall(id, phone)
                        }
                    }
                    processPendingCalls(base, token)
                    checkCommands(base, token)
                    // Každých ~5 min: nahlas stav (verze + nastavení) + zkontroluj verzi.
                    if (cycle % UPDATE_CHECK_EVERY == 0) {
                        reportHeartbeat(base, token)
                        checkAppUpdate(base, token)
                    }
                }
                cycle++
            } catch (e: Exception) {
                // síťová / parse chyba — neshazuj službu, zkus příští kolo
            }
            try {
                Thread.sleep(POLL_MS)
            } catch (e: InterruptedException) {
                break
            }
        }
    }

    private fun fetchPending(base: String, token: String): JSONArray {
        val c = (URL("$base/api/v1/erp/phone-dial-request/pending")
            .openConnection() as HttpURLConnection)
        try {
            c.requestMethod = "GET"
            c.setRequestProperty("Authorization", "Bearer $token")
            c.connectTimeout = 8000
            c.readTimeout = 8000
            if (c.responseCode == 200) {
                val body = c.inputStream.bufferedReader().use { it.readText() }
                val obj = JSONObject(body)
                if (obj.optBoolean("ok", false)) {
                    return obj.optJSONArray("requests") ?: JSONArray()
                }
            }
        } finally {
            c.disconnect()
        }
        return JSONArray()
    }

    private fun consume(base: String, token: String, id: Int) {
        try {
            val c = (URL("$base/api/v1/erp/phone-dial-request/$id/consume")
                .openConnection() as HttpURLConnection)
            try {
                c.requestMethod = "POST"
                c.setRequestProperty("Authorization", "Bearer $token")
                c.setRequestProperty("Content-Type", "application/json")
                c.doOutput = true
                c.connectTimeout = 8000
                c.readTimeout = 8000
                c.outputStream.use { it.write("{\"status\":\"done\"}".toByteArray()) }
                c.responseCode
            } finally {
                c.disconnect()
            }
        } catch (e: Exception) {
            // consume selhal — příští poll případně znovu (idempotentní na serveru)
        }
    }

    private fun notifyDial(id: Int, phone: String, label: String) {
        val dialIntent = Intent(this, DialActivity::class.java).apply {
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP)
            putExtra("phone", phone)
        }
        val pi = PendingIntent.getActivity(
            this, id, dialIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        val title = if (label.isNotBlank()) label else phone
        val n = NotificationCompat.Builder(this, CH_ALERT)
            .setSmallIcon(android.R.drawable.sym_action_call)
            .setContentTitle("Vytočit: $title")
            .setContentText(phone)
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setCategory(NotificationCompat.CATEGORY_CALL)
            .setAutoCancel(true)
            .setContentIntent(pi)
            .setFullScreenIntent(pi, true)
            .build()
        nm().notify(NOTIF_DIAL_BASE + id, n)
    }

    private fun startForegroundCompat() {
        val n = buildOngoing()
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            startForeground(NOTIF_ONGOING, n, ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC)
        } else {
            startForeground(NOTIF_ONGOING, n)
        }
    }

    private fun buildOngoing(): Notification {
        val openApp = PendingIntent.getActivity(
            this, 0, Intent(this, HybridActivity::class.java),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        return NotificationCompat.Builder(this, CH_ONGOING)
            .setSmallIcon(R.drawable.ic_stat_energy)
            .setColor(0xFF00C853.toInt())
            .setColorized(true)
            .setContentTitle("STRATEGIE")
            .setContentText("Párování s ERP — aktivní")
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .setOngoing(true)
            .setContentIntent(openApp)
            .build()
    }

    private fun nm() =
        getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager

    private fun strategieSound(): Uri =
        Uri.parse("android.resource://" + packageName + "/" + R.raw.strategie_chime)

    private fun createChannels() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val attrs = AudioAttributes.Builder()
                .setUsage(AudioAttributes.USAGE_NOTIFICATION)
                .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
                .build()
            val sound = strategieSound()
            nm().createNotificationChannel(
                NotificationChannel(
                    CH_ONGOING, "Služba vytáčení", NotificationManager.IMPORTANCE_LOW
                ).apply {
                    // Trvalá notifikace „Párování s ERP" nesmí dělat odznak (číslo 1)
                    // na ikoně appky v launcheru. Marti 6.6.2026.
                    setShowBadge(false)
                }
            )
            // Příchozí vytáčení — vlastní STRATEGIE zvuk (nový kanál id v2,
            // aby se nový zvuk projevil i při update bez reinstalace)
            nm().createNotificationChannel(
                NotificationChannel(
                    CH_ALERT, "Příchozí vytáčení", NotificationManager.IMPORTANCE_HIGH
                ).apply {
                    setSound(sound, attrs)
                    enableVibration(true)
                }
            )
            nm().createNotificationChannel(
                NotificationChannel(
                    CH_UPDATE, "Aktualizace appky", NotificationManager.IMPORTANCE_DEFAULT
                )
            )
            nm().createNotificationChannel(
                NotificationChannel(
                    CH_COMMAND, "Doporučení", NotificationManager.IMPORTANCE_HIGH
                )
            )
            // Claude — potvrzení a zprávy (vlastní STRATEGIE zvuk)
            nm().createNotificationChannel(
                NotificationChannel(
                    CH_CLAUDE, "Claude", NotificationManager.IMPORTANCE_HIGH
                ).apply {
                    description = "Potvrzení a zprávy od Clauda"
                    setSound(sound, attrs)
                    enableVibration(true)
                }
            )
        }
    }

    // ── Heartbeat: nahlas serveru verzi + nastavení (fw.mobile_device) ──────
    private fun deviceId(): String {
        val prefs = getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        var id = prefs.getString(KEY_DEVICE_ID, null)
        if (id.isNullOrBlank()) {
            id = java.util.UUID.randomUUID().toString()
            prefs.edit().putString(KEY_DEVICE_ID, id).apply()
        }
        return id
    }

    private fun reportHeartbeat(base: String, token: String) {
        try {
            val callLog = ContextCompat.checkSelfPermission(
                this, Manifest.permission.READ_CALL_LOG
            ) == PackageManager.PERMISSION_GRANTED
            val notif = androidx.core.app.NotificationManagerCompat
                .from(this).areNotificationsEnabled()
            val fullscreen = if (Build.VERSION.SDK_INT >= 34) {
                try { nm().canUseFullScreenIntent() } catch (e: Exception) { false }
            } else true
            val payload = JSONObject().apply {
                put("device_id", deviceId())
                put("device_label", "${Build.MANUFACTURER} ${Build.MODEL}")
                put("version_code", BuildConfig.VERSION_CODE)
                put("version_name", BuildConfig.VERSION_NAME)
                put("android_release", Build.VERSION.RELEASE)
                put("service_enabled", true)
                put("call_log_enabled", callLog)
                put("notif_enabled", notif)
                put("fullscreen_enabled", fullscreen)
                put("server_url", base)
            }
            val c = (URL("$base/api/v1/erp/app/$APP_KEY/heartbeat")
                .openConnection() as HttpURLConnection)
            try {
                c.requestMethod = "POST"
                c.setRequestProperty("Authorization", "Bearer $token")
                c.setRequestProperty("Content-Type", "application/json")
                c.doOutput = true
                c.connectTimeout = 8000
                c.readTimeout = 8000
                c.outputStream.use { it.write(payload.toString().toByteArray()) }
                c.responseCode
            } finally {
                c.disconnect()
            }
        } catch (e: Exception) {
        }
    }

    // ── Samo-aktualizace: server řekne, že je nová verze → stáhni → nabídni ──
    private fun checkAppUpdate(base: String, token: String) {
        try {
            val c = (URL("$base/api/v1/erp/app/$APP_KEY/latest")
                .openConnection() as HttpURLConnection)
            val body: String
            try {
                c.requestMethod = "GET"
                c.setRequestProperty("Authorization", "Bearer $token")
                c.connectTimeout = 8000
                c.readTimeout = 8000
                if (c.responseCode != 200) return
                body = c.inputStream.bufferedReader().use { it.readText() }
            } finally {
                c.disconnect()
            }
            val o = JSONObject(body)
            if (!o.optBoolean("available", false)) return
            val remote = o.optInt("version_code", 0)
            if (remote <= BuildConfig.VERSION_CODE) return  // máme aktuální/novější
            val vname = o.optString("version_name", "")
            val prefs = getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            val apkPath = "${cacheDir.absolutePath}/updates/strategie-$remote.apk"
            val already = prefs.getInt(KEY_DL_CODE, 0) == remote && java.io.File(apkPath).exists()
            if (!already) {
                if (!downloadApk(base, token, apkPath)) return
                prefs.edit().putInt(KEY_DL_CODE, remote).apply()
            }
            notifyUpdate(remote, vname, apkPath)
        } catch (e: Exception) {
        }
    }

    private fun downloadApk(base: String, token: String, destPath: String): Boolean {
        return try {
            val dest = java.io.File(destPath)
            dest.parentFile?.mkdirs()
            val c = (URL("$base/api/v1/erp/app/$APP_KEY/download")
                .openConnection() as HttpURLConnection)
            try {
                c.requestMethod = "GET"
                c.setRequestProperty("Authorization", "Bearer $token")
                c.connectTimeout = 10000
                c.readTimeout = 60000
                if (c.responseCode != 200) return false
                c.inputStream.use { inp ->
                    dest.outputStream().use { out -> inp.copyTo(out, 64 * 1024) }
                }
            } finally {
                c.disconnect()
            }
            dest.length() > 0
        } catch (e: Exception) {
            false
        }
    }

    private fun notifyUpdate(versionCode: Int, versionName: String, apkPath: String) {
        val i = Intent(this, InstallActivity::class.java).apply {
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            putExtra(InstallActivity.EXTRA_APK, apkPath)
        }
        val pi = PendingIntent.getActivity(
            this, 9000 + versionCode, i,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        val label = if (versionName.isNotBlank()) "verze $versionName" else "nová verze"
        val n = NotificationCompat.Builder(this, CH_UPDATE)
            .setSmallIcon(android.R.drawable.stat_sys_download_done)
            .setContentTitle("STRATEGIE — $label k dispozici")
            .setContentText("Klepni pro instalaci aktualizace")
            .setPriority(NotificationCompat.PRIORITY_DEFAULT)
            .setAutoCancel(true)
            .setContentIntent(pi)
            .build()
        nm().notify(NOTIF_UPDATE, n)
    }

    // ── Vzdálená doporučení parentů → notifikace → CommandActivity dialog ───
    // Příkazy, které už mají zobrazenou notifikaci — aby se nenotifikovaly
    // znovu každé kolo (jinak se na ikoně hromadí počet). Marti 5.6.
    private val shownCommandIds =
        java.util.Collections.synchronizedSet(HashSet<Long>())

    private fun checkCommands(base: String, token: String) {
        try {
            val c = (URL("$base/api/v1/erp/app/$APP_KEY/commands/pending")
                .openConnection() as HttpURLConnection)
            val body: String
            try {
                c.requestMethod = "GET"
                c.setRequestProperty("Authorization", "Bearer $token")
                c.connectTimeout = 8000
                c.readTimeout = 8000
                if (c.responseCode != 200) return
                body = c.inputStream.bufferedReader().use { it.readText() }
            } finally {
                c.disconnect()
            }
            val arr = JSONObject(body).optJSONArray("commands") ?: return
            val current = HashSet<Long>()
            for (i in 0 until arr.length()) {
                val cmd = arr.getJSONObject(i)
                val id = cmd.optLong("id", -1L)
                if (id < 0L) continue
                current.add(id)
                // notifikuj jen NOVÉ příkazy (ne každé kolo znovu)
                if (shownCommandIds.add(id)) {
                    notifyCommand(
                        id,
                        cmd.optString("command_type", ""),
                        cmd.optString("title", "Doporučení"),
                        cmd.optString("message", ""),
                        cmd.optString("payload", "")
                    )
                }
            }
            // de-pile: příkazy, co už nejsou pending (vyřízené jinde) → zruš jejich
            // notifikaci, ať počet na ikoně klesá sám.
            val gone = synchronized(shownCommandIds) { shownCommandIds.toList() }
                .filter { it !in current }
            for (gid in gone) {
                cancelCommandNotif(gid)
                shownCommandIds.remove(gid)
            }
        } catch (e: Exception) {
        }
    }

    private fun cancelCommandNotif(id: Long) {
        try {
            nm().cancel((NOTIF_COMMAND_BASE + id).toInt())
        } catch (e: Exception) {
        }
    }

    private fun notifyCommand(
        id: Long, type: String, title: String, msg: String, payload: String
    ) {
        if (id < 0L) return
        val i = Intent(this, CommandActivity::class.java).apply {
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            putExtra("cmd_id", id)
            putExtra("cmd_type", type)
            putExtra("cmd_title", title)
            putExtra("cmd_msg", msg)
            try {
                if (type == "open_url" && payload.isNotBlank()) {
                    putExtra("cmd_url", JSONObject(payload).optString("url", ""))
                }
            } catch (e: Exception) {
            }
        }
        val pi = PendingIntent.getActivity(
            this, (NOTIF_COMMAND_BASE + id).toInt(), i,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        val ch = if (type == "claude_confirm" || type == "claude_msg") CH_CLAUDE else CH_COMMAND
        val n = NotificationCompat.Builder(this, ch)
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentTitle(title)
            .setContentText(if (msg.isNotBlank()) msg else "Klepni pro zobrazení")
            .setStyle(NotificationCompat.BigTextStyle().bigText(msg))
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setAutoCancel(true)
            .setOnlyAlertOnce(true)
            .setContentIntent(pi)
            .build()
        nm().notify((NOTIF_COMMAND_BASE + id).toInt(), n)
    }

    // ── Call-log: dohledání startu + doby hovoru pro vytočená čísla ──────
    // Po vytočení (notify+consume) zaznamenáme {id, phone, ts}. Každé kolo
    // pak v call-logu hledáme dokončený odchozí hovor na to číslo a propíšeme
    // start + dobu hovoru do tabulky vyzvánění. Ring (doba vyzvánění) v
    // call-logu není → doplní až real-time krok.
    private fun recordPendingCall(id: Int, phone: String) {
        try {
            val prefs = getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            val arr = JSONArray(prefs.getString(KEY_PENDING_CALLS, "[]") ?: "[]")
            for (i in 0 until arr.length()) {
                if (arr.getJSONObject(i).optInt("id") == id) return  // idempotent
            }
            arr.put(JSONObject().apply {
                put("id", id)
                put("phone", phone)
                put("ts", System.currentTimeMillis())
            })
            prefs.edit().putString(KEY_PENDING_CALLS, arr.toString()).apply()
        } catch (e: Exception) {
        }
    }

    private fun processPendingCalls(base: String, token: String) {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.READ_CALL_LOG)
            != PackageManager.PERMISSION_GRANTED
        ) return
        val prefs = getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        val arr = try {
            JSONArray(prefs.getString(KEY_PENDING_CALLS, "[]") ?: "[]")
        } catch (e: Exception) {
            JSONArray()
        }
        if (arr.length() == 0) return
        val keep = JSONArray()
        val now = System.currentTimeMillis()
        for (i in 0 until arr.length()) {
            val o = arr.getJSONObject(i)
            val id = o.optInt("id", -1)
            val phone = o.optString("phone", "")
            val ts = o.optLong("ts", 0L)
            if (id <= 0 || phone.isEmpty()) continue
            if (now - ts > 2 * 60 * 60 * 1000L) continue  // timeout 2h → vzdej
            val call = findOutgoingCall(phone, ts - 60_000L)
            if (call != null) {
                reportCallResult(base, token, id, call.first, call.second)
            } else {
                keep.put(o)  // hovor ještě neskončil / není v logu → zkus příště
            }
        }
        prefs.edit().putString(KEY_PENDING_CALLS, keep.toString()).apply()
    }

    /** Poslední odchozí hovor na číslo od sinceMs. Vrací (startMs, durationS) nebo null. */
    private fun findOutgoingCall(phone: String, sinceMs: Long): Pair<Long, Int>? {
        val want = digits(phone)
        if (want.length < 6) return null
        try {
            val proj = arrayOf(
                CallLog.Calls.NUMBER, CallLog.Calls.DATE,
                CallLog.Calls.DURATION, CallLog.Calls.TYPE
            )
            val sel = "${CallLog.Calls.TYPE} = ? AND ${CallLog.Calls.DATE} >= ?"
            val args = arrayOf(
                CallLog.Calls.OUTGOING_TYPE.toString(), sinceMs.toString()
            )
            contentResolver.query(
                CallLog.Calls.CONTENT_URI, proj, sel, args,
                "${CallLog.Calls.DATE} DESC"
            )?.use { c ->
                val iNum = c.getColumnIndex(CallLog.Calls.NUMBER)
                val iDate = c.getColumnIndex(CallLog.Calls.DATE)
                val iDur = c.getColumnIndex(CallLog.Calls.DURATION)
                while (c.moveToNext()) {
                    val num = digits(c.getString(iNum) ?: "")
                    if (num.length >= 6 && num.takeLast(9) == want.takeLast(9)) {
                        return Pair(c.getLong(iDate), c.getInt(iDur))
                    }
                }
            }
        } catch (e: Exception) {
        }
        return null
    }

    private fun reportCallResult(
        base: String, token: String, id: Int, startMs: Long, durationS: Int
    ) {
        try {
            val c = (URL("$base/api/v1/erp/phone-dial-request/$id/call-result")
                .openConnection() as HttpURLConnection)
            try {
                c.requestMethod = "POST"
                c.setRequestProperty("Authorization", "Bearer $token")
                c.setRequestProperty("Content-Type", "application/json")
                c.doOutput = true
                c.connectTimeout = 8000
                c.readTimeout = 8000
                val payload = JSONObject().apply {
                    put("started_at_ms", startMs)
                    put("talk_duration_s", durationS)
                }
                c.outputStream.use { it.write(payload.toString().toByteArray()) }
                c.responseCode
            } finally {
                c.disconnect()
            }
        } catch (e: Exception) {
        }
    }

    private fun digits(s: String): String = s.filter { it.isDigit() }

    companion object {
        const val PREFS = "strategie_prefs"
        const val KEY_URL = "server_url"
        const val KEY_TOKEN = "token"
        const val KEY_PENDING_CALLS = "pending_calls"
        const val KEY_DL_CODE = "downloaded_update_code"
        const val KEY_DEVICE_ID = "device_id"
        const val APP_KEY = "mobile"
        const val DEFAULT_URL = "https://strategie-ai.com"
        const val CH_ONGOING = "dial_ongoing"
        const val CH_ALERT = "dial_alert_v2"      // v2 = vlastní STRATEGIE zvuk
        const val CH_UPDATE = "app_update"
        const val CH_COMMAND = "app_command"
        const val CH_CLAUDE = "claude_v1"         // potvrzení + zprávy od Clauda
        const val NOTIF_ONGOING = 1001
        const val NOTIF_UPDATE = 1002
        const val NOTIF_DIAL_BASE = 2000
        const val NOTIF_COMMAND_BASE = 7000L
        const val POLL_MS = 4000L
        const val UPDATE_CHECK_EVERY = 75  // ~5 min (75 × 4 s)

        fun start(ctx: Context) {
            val i = Intent(ctx, DialPollService::class.java)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                ctx.startForegroundService(i)
            } else {
                ctx.startService(i)
            }
        }

        fun stop(ctx: Context) {
            ctx.stopService(Intent(ctx, DialPollService::class.java))
        }
    }
}
