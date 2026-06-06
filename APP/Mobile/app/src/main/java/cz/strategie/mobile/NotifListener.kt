package cz.strategie.mobile

import android.content.Context
import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification
import org.json.JSONObject

/**
 * Počítá aktivní oznámení podle balíčku (WhatsApp, SMS…) pro badge „Aplikace"
 * na hlavní obrazovce /mobile. Vyžaduje jednorázový souhlas „Přístup k oznámením".
 * Ukládá JSON {balíček: počet} do prefs (klíč notif_badges). Marti 6.6.2026.
 */
class NotifListener : NotificationListenerService() {
    override fun onListenerConnected() { recount() }
    override fun onNotificationPosted(sbn: StatusBarNotification?) { recount() }
    override fun onNotificationRemoved(sbn: StatusBarNotification?) { recount() }

    private fun recount() {
        try {
            val counts = HashMap<String, Int>()
            val active = activeNotifications ?: return
            for (sbn in active) {
                if (sbn.isOngoing) continue
                val pkg = sbn.packageName ?: continue
                if (pkg == packageName) continue
                counts[pkg] = (counts[pkg] ?: 0) + 1
            }
            val o = JSONObject()
            for ((k, v) in counts) o.put(k, v)
            getSharedPreferences(DialPollService.PREFS, Context.MODE_PRIVATE)
                .edit().putString("notif_badges", o.toString()).apply()
        } catch (e: Exception) {
        }
    }
}
