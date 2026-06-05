package cz.strategie.mobile

import android.app.Activity
import android.content.Intent
import android.net.Uri
import android.os.Bundle

/**
 * Tichá průchozí aktivita: dostane číslo v extra "phone", otevře systémový
 * dialer předvyplněný tím číslem (ACTION_DIAL — uživatel jen ťukne Volat;
 * NEvolá automaticky, nepotřebuje CALL_PHONE) a hned se zavře.
 * Cíl full-screen intentu / tapu na notifikaci z DialPollService.
 */
class DialActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val phone = intent?.getStringExtra("phone")?.trim().orEmpty()
        if (phone.isNotEmpty()) {
            try {
                startActivity(
                    Intent(Intent.ACTION_DIAL, Uri.parse("tel:$phone"))
                        .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                )
            } catch (e: Exception) {
                // žádný dialer — nic neděláme
            }
        }
        finish()
    }
}
