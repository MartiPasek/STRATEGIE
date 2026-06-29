package cz.strategie.mobile

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.os.Build

/**
 * Po restartu telefonu (BOOT_COMPLETED) nastartuje DialPollService, pokud si
 * uživatel naslouchání zapnul (prefs "service_enabled"). Tím služba běží
 * dál i po rebootu, bez nutnosti appku otevřít.
 *
 * Android 15 (API 35)+ ale ZAKAZUJE startovat z přijímače BOOT_COMPLETED
 * foreground službu typu `dataSync` (jinak ForegroundServiceStartNotAllowedException).
 * Google Play to hlásí jako „Omezené typy služeb v popředí". Proto na Androidu 15+
 * službu po rebootu NEstartujeme — rozjede se sama při příštím otevření appky
 * (HybridActivity volá DialPollService.start). Na Androidu 14 a níž = beze změny.
 */
class BootReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent?) {
        if (intent?.action != Intent.ACTION_BOOT_COMPLETED) return
        // Android 15+: dataSync FGS nelze spustit z BOOT_COMPLETED → nestartuj.
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.VANILLA_ICE_CREAM) return
        val prefs = context.getSharedPreferences(
            DialPollService.PREFS, Context.MODE_PRIVATE
        )
        if (prefs.getBoolean("service_enabled", false)) {
            DialPollService.start(context)
        }
    }
}
