package cz.strategie.mobile

import android.app.Activity
import android.app.KeyguardManager
import android.app.NotificationManager
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Bundle

/**
 * Tichá průchozí aktivita: dostane číslo v extra "phone", otevře systémový
 * dialer předvyplněný tím číslem (ACTION_DIAL — uživatel jen ťukne Volat;
 * NEvolá automaticky, nepotřebuje CALL_PHONE).
 * Cíl full-screen intentu / tapu na notifikaci z DialPollService.
 * Marti 6.6.2026: zobraz se přes zámek a po odemčení otevři vytáčení rovnou
 * (PC klik na číslo → telefon zazvoní → odemknu → naskočí dialer).
 */
class DialActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O_MR1) {
            setShowWhenLocked(true)
            setTurnScreenOn(true)
        }
        val phone = intent?.getStringExtra("phone")?.trim().orEmpty()
        // Zruš notifikaci vytáčení (ať nevisí odznak na ikoně po auto-otevření).
        val notifId = intent?.getIntExtra("notif_id", -1) ?: -1
        if (notifId > 0) {
            try { (getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager).cancel(notifId) } catch (e: Exception) {}
        }
        if (phone.isEmpty()) { finish(); return }

        val km = getSystemService(Context.KEYGUARD_SERVICE) as? KeyguardManager
        if (km != null && km.isKeyguardLocked) {
            // Vyzvi k odemčení; po odemčení otevři dialer (jinak by ho systém
            // na pozadí zablokoval). Marti: „dial se má otevřít hned po odemknutí".
            km.requestDismissKeyguard(this, object : KeyguardManager.KeyguardDismissCallback() {
                override fun onDismissSucceeded() { openDialer(phone); finish() }
                override fun onDismissCancelled() { finish() }
                override fun onDismissError() { openDialer(phone); finish() }
            })
        } else {
            openDialer(phone)
            finish()
        }
    }

    private fun openDialer(phone: String) {
        try {
            startActivity(
                Intent(Intent.ACTION_DIAL, Uri.parse("tel:$phone"))
                    .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            )
        } catch (e: Exception) {
            // žádný dialer — nic neděláme
        }
    }
}
