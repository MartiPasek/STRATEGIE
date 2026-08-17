package cz.strategie.mobile

import android.app.Activity
import android.app.AlertDialog
import android.app.NotificationManager
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import java.net.HttpURLConnection
import java.net.URL
import kotlin.concurrent.thread

/**
 * Dialog s doporučením od parentů (Povolit / Zamítnout). Po Povolit appka otevře
 * přesně to nastavení, které uživatel potřebuje — žádné hledání. Marti 5.6.2026.
 */
class CommandActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val id = intent.getLongExtra("cmd_id", -1L)
        val type = intent.getStringExtra("cmd_type") ?: ""
        val title = intent.getStringExtra("cmd_title") ?: "Doporučení"
        val msg = intent.getStringExtra("cmd_msg") ?: ""
        if (id < 0L) { finish(); return }
        when (type) {
            "claude_confirm" -> {
                // Potvrzení akce Clauda přímo z mobilu — Povolit = zápis se provede
                AlertDialog.Builder(this)
                    .setTitle(title)
                    .setMessage(msg)
                    .setCancelable(false)
                    .setPositiveButton("Povolit") { _, _ ->
                        report(id, "accept"); cancelNotif(id); finish()
                    }
                    .setNegativeButton("Odmítnout") { _, _ ->
                        report(id, "reject"); cancelNotif(id); finish()
                    }
                    .show()
            }
            "claude_ok" -> {
                // Marti 14.6.: tiché potvrzení (schváleno/hotovo) — klidné OK, neruší.
                AlertDialog.Builder(this)
                    .setTitle(title)
                    .setMessage(msg)
                    .setCancelable(true)
                    .setPositiveButton("OK") { _, _ -> report(id, "done"); cancelNotif(id); finish() }
                    .setOnCancelListener { report(id, "done"); cancelNotif(id); finish() }
                    .show()
            }
            "claude_msg" -> {
                // Zpráva od Clauda (hotovo/výsledek) — jen informace + otevřít chat.
                // Když zpráva nese payload.screen (typicky žádost o absenci), nabídneme
                // navíc tlačítko, které otevře rovnou tu obrazovku v appce. Jirka
                // 16. 8. 2026, schválila Marti-AI; hlásil Dušan Havlát — ťuknutí na
                // notifikaci o žádosti o dovolenou dosud nabídlo jen „Otevřít chat",
                // takže vedoucí neměl z notifikace cestu ke schválení.
                val screen = safeScreen(intent.getStringExtra("cmd_screen") ?: "")
                val b = AlertDialog.Builder(this)
                    .setTitle(title)
                    .setMessage(msg)
                    .setCancelable(true)
                if (screen.isNotBlank()) {
                    // Popisek posílá SERVER v `payload.label` (Jirka 17. 8. 2026, schválila
                    // Marti-AI) — tím je zdroj pravdy jeden a texty se nemůžou rozejít.
                    // Mapa níže je jen ZÁCHRANA pro zprávy bez `label` (starší zprávy
                    // a případy, kdy ho server nepošle). Nová obrazovka se přidává na
                    // serveru, ne sem; sem jen když má mít popisek i bez serveru.
                    val label = (intent.getStringExtra("cmd_label") ?: "").trim().take(60).ifBlank {
                        when (screen) {
                            "absence" -> "✅ Otevřít schvalování"
                            "dochazka" -> "🖊 Otevřít docházku"
                            else -> "Otevřít"
                        }
                    }
                    b.setPositiveButton(label) { _, _ ->
                        openScreen(screen); report(id, "done"); cancelNotif(id); finish()
                    }
                    b.setNeutralButton("Otevřít chat") { _, _ ->
                        openChat(); report(id, "done"); cancelNotif(id); finish()
                    }
                } else {
                    b.setPositiveButton("Otevřít chat") { _, _ ->
                        openChat(); report(id, "done"); cancelNotif(id); finish()
                    }
                }
                b.setNegativeButton("Zavřít") { _, _ ->
                    report(id, "done"); cancelNotif(id); finish()
                }
                b.setOnCancelListener { report(id, "done"); cancelNotif(id); finish() }
                b.show()
            }
            else -> {
                AlertDialog.Builder(this)
                    .setTitle(title)
                    .setMessage(msg)
                    .setCancelable(false)
                    .setPositiveButton("Povolit") { _, _ ->
                        doAction(type)
                        report(id, "accept")
                        cancelNotif(id)
                        finish()
                    }
                    .setNegativeButton("Teď ne") { _, _ ->
                        report(id, "reject")
                        cancelNotif(id)
                        finish()
                    }
                    .show()
            }
        }
    }

    /** Název obrazovky jde z appky rovnou do JS `go(...)`, proto ho propouštíme
     *  jen jako písmena/číslice/podtržítko — nesmí se z něj dát udělat kód.
     *  Jirka 16. 8. 2026. */
    private fun safeScreen(s: String): String =
        s.trim().filter { it.isLetterOrDigit() || it == '_' }.take(40)

    /** Otevře appku a přepne ji rovnou na danou obrazovku /mobile. HybridActivity
     *  si extra `go_screen` přečte v onNewIntent (když už běží) nebo po načtení
     *  stránky (když se teprve spouští). Když se to nepovede, spadneme na chat —
     *  uživatel nesmí zůstat bez cesty dál. Jirka 16. 8. 2026. */
    private fun openScreen(screen: String) {
        try {
            startActivity(
                Intent(this, HybridActivity::class.java)
                    .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_SINGLE_TOP)
                    .putExtra("go_screen", screen)
            )
        } catch (e: Exception) {
            openChat()
        }
    }

    private fun openChat() {
        try {
            val prefs = getSharedPreferences(DialPollService.PREFS, MODE_PRIVATE)
            val base = (prefs.getString(DialPollService.KEY_URL, DialPollService.DEFAULT_URL)
                ?: DialPollService.DEFAULT_URL).trim().trimEnd('/')
            startActivity(
                Intent(Intent.ACTION_VIEW, Uri.parse(base))
                    .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            )
        } catch (e: Exception) {
        }
    }

    private fun doAction(type: String) {
        try {
            when (type) {
                "fullscreen" -> {
                    if (Build.VERSION.SDK_INT >= 34) {
                        startActivity(
                            Intent(Settings.ACTION_MANAGE_APP_USE_FULL_SCREEN_INTENT)
                                .setData(Uri.parse("package:$packageName"))
                        )
                    } else openAppDetails()
                }
                "battery" -> startActivity(
                    Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS)
                        .setData(Uri.parse("package:$packageName"))
                )
                "notif" -> startActivity(
                    Intent(Settings.ACTION_APP_NOTIFICATION_SETTINGS)
                        .putExtra(Settings.EXTRA_APP_PACKAGE, packageName)
                )
                "calllog" -> openAppDetails()
                "update" -> startActivity(
                    Intent(this, HybridActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                )
                "open_url" -> {
                    val u = intent.getStringExtra("cmd_url")
                    if (!u.isNullOrBlank()) startActivity(
                        Intent(Intent.ACTION_VIEW, Uri.parse(u))
                            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                    )
                }
                else -> { /* message: jen informace */ }
            }
        } catch (e: Exception) {
        }
    }

    private fun openAppDetails() {
        try {
            startActivity(
                Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS)
                    .setData(Uri.parse("package:$packageName"))
            )
        } catch (e: Exception) {
        }
    }

    private fun cancelNotif(id: Long) {
        try {
            (getSystemService(NOTIFICATION_SERVICE) as NotificationManager)
                .cancel((DialPollService.NOTIF_COMMAND_BASE + id).toInt())
        } catch (e: Exception) {
        }
    }

    private fun report(id: Long, decision: String) {
        val prefs = getSharedPreferences(DialPollService.PREFS, MODE_PRIVATE)
        val base = (prefs.getString(DialPollService.KEY_URL, DialPollService.DEFAULT_URL)
            ?: DialPollService.DEFAULT_URL).trim().trimEnd('/')
        val token = (prefs.getString(DialPollService.KEY_TOKEN, "") ?: "").trim()
        if (token.isEmpty()) return
        thread {
            try {
                val c = (URL("$base/api/v1/erp/app/command/$id/result")
                    .openConnection() as HttpURLConnection)
                try {
                    c.requestMethod = "POST"
                    c.setRequestProperty("Authorization", "Bearer $token")
                    c.setRequestProperty("Content-Type", "application/json")
                    c.doOutput = true
                    c.connectTimeout = 8000
                    c.readTimeout = 8000
                    c.outputStream.use { it.write("{\"decision\":\"$decision\"}".toByteArray()) }
                    c.responseCode
                } finally {
                    c.disconnect()
                }
            } catch (e: Exception) {
            }
        }
    }
}
