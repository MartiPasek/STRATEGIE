package cz.strategie.mobile

import android.app.Activity
import android.content.Intent
import android.os.Bundle
import android.widget.Toast

/**
 * Párování přes odkaz (deep link) strategiemobil://pair?u=<server>&t=<token>&k=mobile.
 * Pro samoobslužné spárování na stejném telefonu (kolega si appku stáhne z webu,
 * nainstaluje a klepne „Otevřít v appce" — bez skenování QR). Uloží adresu+token,
 * zapne naslouchání a otevře hlavní obrazovku.
 */
class PairActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val data = intent?.data
        var ok = false
        if (data != null) {
            val u = data.getQueryParameter("u")
            val t = data.getQueryParameter("t")
            if (!u.isNullOrBlank() && !t.isNullOrBlank()) {
                getSharedPreferences(DialPollService.PREFS, MODE_PRIVATE).edit()
                    .putString(DialPollService.KEY_URL, u.trim())
                    .putString(DialPollService.KEY_TOKEN, t.trim())
                    .putBoolean("service_enabled", true)
                    .apply()
                try {
                    DialPollService.start(this)
                } catch (e: Exception) {
                }
                ok = true
            }
        }
        Toast.makeText(
            this,
            if (ok) "Spárováno ✓ — naslouchání zapnuto" else "Neplatný párovací odkaz",
            Toast.LENGTH_LONG
        ).show()
        startActivity(Intent(this, HybridActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
        finish()
    }
}
