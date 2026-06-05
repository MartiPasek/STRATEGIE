package cz.strategie.mobile

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent

/**
 * Po restartu telefonu (BOOT_COMPLETED) nastartuje DialPollService, pokud si
 * uživatel naslouchání zapnul (prefs "service_enabled"). Tím služba běží
 * dál i po rebootu, bez nutnosti appku otevřít.
 */
class BootReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent?) {
        if (intent?.action != Intent.ACTION_BOOT_COMPLETED) return
        val prefs = context.getSharedPreferences(
            DialPollService.PREFS, Context.MODE_PRIVATE
        )
        if (prefs.getBoolean("service_enabled", false)) {
            DialPollService.start(context)
        }
    }
}
