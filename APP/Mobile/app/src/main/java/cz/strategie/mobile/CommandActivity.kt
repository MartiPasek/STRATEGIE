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
                    Intent(this, MainActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
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
