package cz.strategie.mobile

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.provider.Telephony
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

/**
 * Marti 8.6.2026: vlastní příjem příchozích SMS — bez cizího provideru
 * (capcom6 / sms-gate.app). Zachytí příchozí SMS a JEN ověřovací (obsahující
 * token "STG-") přepošle na náš server /app/sms-inbound. Soukromé SMS ignoruje
 * (neforwardují se) → žádné toggle, soukromí chráněné.
 *
 * Auth: carddav token appky (Bearer), URL z prefs (stejné jako DialPollService).
 */
class SmsReceiver : BroadcastReceiver() {

    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action != Telephony.Sms.Intents.SMS_RECEIVED_ACTION) return
        val msgs = try { Telephony.Sms.Intents.getMessagesFromIntent(intent) } catch (e: Exception) { return }
        if (msgs == null || msgs.isEmpty()) return

        // Slož vícedílné SMS dohromady podle odesílatele.
        val from = msgs[0].displayOriginatingAddress ?: msgs[0].originatingAddress ?: ""
        val body = StringBuilder()
        for (m in msgs) body.append(m.displayMessageBody ?: m.messageBody ?: "")
        val text = body.toString()

        val prefs = context.getSharedPreferences(DialPollService.PREFS, Context.MODE_PRIVATE)

        // Marti 8.6.: forwarduje JEN telefon označený jako SMS brána (Marti-AI mobil).
        // Ostatní telefony příchozí SMS NEpřeposílají (soukromí + jediná brána).
        if (!prefs.getBoolean("sms_gateway", false)) return

        // Forwardujeme naše ověřovací SMS (token "STG-") A přeposlané ČSSZ eOČR SMS
        // (eportal.cssz.cz + identifikator + osetrovani). Ostatní soukromé SMS NE.
        val lb = text.lowercase()
        val isStg = text.contains("STG-", ignoreCase = true)
        val isOcr = lb.contains("eportal.cssz.cz") && lb.contains("identifik") &&
            (lb.contains("osetrov") || lb.contains("ošetřov"))
        if (!isStg && !isOcr) return

        val token = (prefs.getString(DialPollService.KEY_TOKEN, "") ?: "").trim()
        if (token.isBlank()) return  // nespárováno → neforwardujeme
        val base = (prefs.getString(DialPollService.KEY_URL, DialPollService.DEFAULT_URL)
            ?: DialPollService.DEFAULT_URL).trim().trimEnd('/')

        // Síťový POST na pozadí (BroadcastReceiver nesmí blokovat).
        val pending = goAsync()
        Thread {
            try {
                val payload = JSONObject()
                payload.put("from", from)
                payload.put("body", text)
                val con = URL("$base/api/v1/erp/app/sms-inbound").openConnection() as HttpURLConnection
                con.requestMethod = "POST"
                con.setRequestProperty("Authorization", "Bearer $token")
                con.setRequestProperty("Content-Type", "application/json")
                con.connectTimeout = 10000
                con.readTimeout = 10000
                con.doOutput = true
                con.outputStream.use { it.write(payload.toString().toByteArray(Charsets.UTF_8)) }
                con.inputStream.use { it.readBytes() }  // dočti odpověď
                con.disconnect()
            } catch (e: Exception) {
                // tichý fail — SMS se neztratí (ověření lze opakovat)
            } finally {
                try { pending.finish() } catch (e: Exception) {}
            }
        }.start()
    }
}
