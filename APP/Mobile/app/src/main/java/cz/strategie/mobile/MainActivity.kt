package cz.strategie.mobile

import android.Manifest
import android.app.NotificationManager
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.provider.Settings
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.core.content.pm.ShortcutInfoCompat
import androidx.core.content.pm.ShortcutManagerCompat
import androidx.core.graphics.drawable.IconCompat
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardCapitalization
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.ContextCompat
import androidx.core.content.FileProvider
import coil.compose.AsyncImage
import coil.request.ImageRequest
import com.google.mlkit.vision.codescanner.GmsBarcodeScanning
import cz.strategie.mobile.ui.theme.STRATEGIEMobileTheme
import org.json.JSONObject
import java.io.File
import java.net.HttpURLConnection
import java.net.URL
import kotlin.concurrent.thread
import kotlinx.coroutines.delay

private const val PREFS = "strategie_prefs"
private const val KEY_URL = "server_url"
private const val KEY_TOKEN = "token"
private const val KEY_SERVICE = "service_enabled"
private const val KEY_LAST_VER = "last_installed_vc"
private const val DEFAULT_URL = "https://strategie-ai.com"
private val BRAND_BLUE = Color(0xFF4A7BA8)

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            STRATEGIEMobileTheme {
                Scaffold(modifier = Modifier.fillMaxSize()) { innerPadding ->
                    AppRoot(modifier = Modifier.padding(innerPadding))
                }
            }
        }
    }
}

data class CmdItem(
    val id: Long,
    val type: String,
    val title: String,
    val msg: String,
    val payload: String,
)

@Composable
fun AppRoot(modifier: Modifier = Modifier) {
    val context = LocalContext.current
    val prefs = remember { context.getSharedPreferences(PREFS, Context.MODE_PRIVATE) }

    var serverUrl by remember { mutableStateOf(prefs.getString(KEY_URL, DEFAULT_URL) ?: DEFAULT_URL) }
    var token by remember { mutableStateOf(prefs.getString(KEY_TOKEN, "") ?: "") }
    var serviceOn by remember { mutableStateOf(prefs.getBoolean(KEY_SERVICE, false)) }
    var showSettings by remember { mutableStateOf(false) }
    var serverVersionCode by remember { mutableStateOf(0) }
    var serverVersionName by remember { mutableStateOf("") }
    var updating by remember { mutableStateOf(false) }
    var canInstall by remember { mutableStateOf(true) }
    var notifs by remember { mutableStateOf<List<CmdItem>>(emptyList()) }
    var notifSel by remember { mutableStateOf(-1L) }
    var replyText by remember { mutableStateOf("") }

    fun base(): String = serverUrl.trim().trimEnd('/')

    fun toastMain(msg: String) {
        Handler(Looper.getMainLooper()).post {
            Toast.makeText(context, msg, Toast.LENGTH_LONG).show()
        }
    }

    // Zjisti nejnovější verzi na serveru. announce=true → po dokončení ukáže
    // toast s výsledkem (ruční „Zkontrolovat verzi" v nastavení). Marti 5.6.
    fun checkVersion(announce: Boolean) {
        val t = token.trim()
        if (t.isEmpty()) {
            if (announce) Toast.makeText(context, "Nejdřív spáruj telefon", Toast.LENGTH_SHORT).show()
            return
        }
        thread {
            var ok = false
            try {
                val c = (URL(base() + "/api/v1/erp/app/mobile/latest")
                    .openConnection() as HttpURLConnection)
                c.setRequestProperty("Authorization", "Bearer $t")
                c.connectTimeout = 8000; c.readTimeout = 8000
                if (c.responseCode == 200) {
                    val o = JSONObject(c.inputStream.bufferedReader().use { it.readText() })
                    if (o.optBoolean("available")) {
                        serverVersionCode = o.optInt("version_code")
                        serverVersionName = o.optString("version_name")
                        ok = true
                    }
                }
                c.disconnect()
            } catch (e: Exception) {
            }
            if (announce) {
                val msg = when {
                    !ok || serverVersionCode <= 0 -> "Verzi se nepodařilo zjistit (zkontroluj připojení)"
                    serverVersionCode > BuildConfig.VERSION_CODE ->
                        "Na serveru je novější verze " + serverVersionName +
                            " (" + serverVersionCode + ") — můžeš ji stáhnout níže"
                    else -> "Máš nejnovější verzi (" + BuildConfig.VERSION_NAME + ")"
                }
                toastMain(msg)
            }
        }
    }

    LaunchedEffect(serverUrl, token) {
        if (token.trim().isNotEmpty()) checkVersion(false)
    }

    fun updateNow() {
        if (updating) return
        if (serverVersionCode <= 0) {
            Toast.makeText(context, "Nejdřív klepni Zkontrolovat verzi", Toast.LENGTH_SHORT).show()
            return
        }
        updating = true
        Toast.makeText(context, "Stahuji verzi…", Toast.LENGTH_SHORT).show()
        val code = serverVersionCode
        val b = base()
        val t = token.trim()
        thread {
            try {
                val dest = File(context.cacheDir, "updates/strategie-$code.apk")
                dest.parentFile?.mkdirs()
                val c = (URL("$b/api/v1/erp/app/mobile/download")
                    .openConnection() as HttpURLConnection)
                c.setRequestProperty("Authorization", "Bearer $t")
                c.connectTimeout = 10000; c.readTimeout = 60000
                if (c.responseCode == 200) {
                    c.inputStream.use { inp -> dest.outputStream().use { o -> inp.copyTo(o, 64 * 1024) } }
                }
                c.disconnect()
                if (dest.length() > 0) {
                    val uri = FileProvider.getUriForFile(
                        context, context.packageName + ".fileprovider", dest
                    )
                    context.startActivity(Intent(Intent.ACTION_VIEW).apply {
                        setDataAndType(uri, "application/vnd.android.package-archive")
                        addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_ACTIVITY_NEW_TASK)
                    })
                }
            } catch (e: Exception) {
            }
            updating = false
        }
    }

    fun open(path: String) {
        try {
            context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(base() + path)))
        } catch (e: Exception) {
            Toast.makeText(context, "Nelze otevřít prohlížeč", Toast.LENGTH_SHORT).show()
        }
    }

    // Přidá ikonu na plochu (Android 8+). Ikona otevře dané URL přes ACTION_VIEW
    // → pokud je PWA nainstalovaná, otevře se standalone; jinak v prohlížeči.
    // Řeší případ, kdy uživatel smazal ikonu PWA, ale WebAPK zůstala nainstalovaná
    // (Chrome už install znovu nenabídne). Marti 6.6.2026.
    fun pinShortcut(id: String, label: String, path: String, kind: String) {
        try {
            if (!ShortcutManagerCompat.isRequestPinShortcutSupported(context)) {
                Toast.makeText(
                    context,
                    "Launcher neumí přidat ikonu sám — otevři v prohlížeči a použij ⋮ → Přidat na plochu",
                    Toast.LENGTH_LONG
                ).show()
                return
            }
            // Už je na ploše? (Android 11+ umí dotaz na pinned shortcuts) → nedělej duplikát
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                val exists = ShortcutManagerCompat
                    .getShortcuts(context, ShortcutManagerCompat.FLAG_MATCH_PINNED)
                    .any { it.id == id }
                if (exists) {
                    Toast.makeText(context, "Ikona už je na ploše", Toast.LENGTH_SHORT).show()
                    return
                }
            }
            fun doPin(icon: IconCompat) {
                val target = Intent(Intent.ACTION_VIEW, Uri.parse(base() + path))
                    .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                val info = ShortcutInfoCompat.Builder(context, id)
                    .setShortLabel(label)
                    .setIcon(icon)
                    .setIntent(target)
                    .build()
                ShortcutManagerCompat.requestPinShortcut(context, info, null)
            }
            if (kind == "chat") {
                // Fotku Marti-AI stáhni na pozadí, pak slep s energií a vytvoř ikonu
                val urlStr = base() + "/api/v1/erp/app/avatar"
                val tok = token.trim()
                Thread {
                    val av = IconRender.fetchAvatar(urlStr, tok)
                    val icon = IconRender.chat(av)
                    Handler(Looper.getMainLooper()).post { doPin(icon) }
                }.start()
            } else {
                doPin(IconRender.erp())
            }
        } catch (e: Exception) {
            Toast.makeText(context, "Nepodařilo se přidat ikonu", Toast.LENGTH_SHORT).show()
        }
    }

    // „Instalace neznámých aplikací" — bez ní si appka nemůže nainstalovat
    // staženou aktualizaci. Jednorázové povolení per telefon. Marti 5.6.
    fun canInstallUnknown(): Boolean =
        Build.VERSION.SDK_INT < Build.VERSION_CODES.O ||
            context.packageManager.canRequestPackageInstalls()

    fun openInstallSources() {
        try {
            context.startActivity(
                Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES)
                    .setData(Uri.parse("package:" + context.packageName))
            )
        } catch (e: Exception) {
            Toast.makeText(context, "Nastavení nelze otevřít", Toast.LENGTH_SHORT).show()
        }
    }

    // ── Inbox notifikací v appce (Marti 5.6.) — seznam „úkolů od Clauda" ──
    fun loadNotifs() {
        val t = token.trim()
        if (t.isEmpty()) { notifs = emptyList(); return }
        thread {
            try {
                val c = (URL(base() + "/api/v1/erp/app/mobile/commands/pending")
                    .openConnection() as HttpURLConnection)
                c.setRequestProperty("Authorization", "Bearer $t")
                c.connectTimeout = 8000; c.readTimeout = 8000
                if (c.responseCode == 200) {
                    val arr = JSONObject(c.inputStream.bufferedReader().use { it.readText() })
                        .optJSONArray("commands")
                    val list = ArrayList<CmdItem>()
                    if (arr != null) for (i in 0 until arr.length()) {
                        val o = arr.getJSONObject(i)
                        list.add(
                            CmdItem(
                                o.optLong("id", -1L),
                                o.optString("command_type", ""),
                                o.optString("title", "Notifikace"),
                                o.optString("message", ""),
                                o.optString("payload", "")
                            )
                        )
                    }
                    Handler(Looper.getMainLooper()).post { notifs = list }
                }
                c.disconnect()
            } catch (e: Exception) {
            }
        }
    }

    fun cancelCmdNotif(id: Long) {
        try {
            context.getSystemService(NotificationManager::class.java)
                ?.cancel((DialPollService.NOTIF_COMMAND_BASE + id).toInt())
        } catch (e: Exception) {
        }
    }

    fun appDetails() {
        try {
            context.startActivity(
                Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS)
                    .setData(Uri.parse("package:" + context.packageName))
            )
        } catch (e: Exception) {
        }
    }

    // akce na příkaz: pošle rozhodnutí na server (accept/reject/done),
    // zruší jeho notifikaci a obnoví seznam
    fun actCmd(item: CmdItem, decision: String, note: String = "") {
        val t = token.trim()
        cancelCmdNotif(item.id)
        notifSel = -1L
        if (t.isEmpty()) return
        val payload = JSONObject().put("decision", decision)
        if (note.isNotBlank()) payload.put("note", note)
        thread {
            try {
                val c = (URL(base() + "/api/v1/erp/app/command/" + item.id + "/result")
                    .openConnection() as HttpURLConnection)
                c.requestMethod = "POST"
                c.setRequestProperty("Authorization", "Bearer $t")
                c.setRequestProperty("Content-Type", "application/json")
                c.doOutput = true
                c.connectTimeout = 8000; c.readTimeout = 8000
                c.outputStream.use { it.write(payload.toString().toByteArray()) }
                c.responseCode
                c.disconnect()
            } catch (e: Exception) {
            }
            try { Thread.sleep(500) } catch (e: Exception) {}
            loadNotifs()
        }
    }

    // otevři přesné nastavení podle typu doporučení
    fun cmdSetting(item: CmdItem) {
        try {
            when (item.type) {
                "fullscreen" -> if (Build.VERSION.SDK_INT >= 34) context.startActivity(
                    Intent(Settings.ACTION_MANAGE_APP_USE_FULL_SCREEN_INTENT)
                        .setData(Uri.parse("package:" + context.packageName))
                ) else appDetails()
                "battery" -> context.startActivity(
                    Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS)
                        .setData(Uri.parse("package:" + context.packageName))
                )
                "notif" -> context.startActivity(
                    Intent(Settings.ACTION_APP_NOTIFICATION_SETTINGS)
                        .putExtra(Settings.EXTRA_APP_PACKAGE, context.packageName)
                )
                "calllog" -> appDetails()
                "update" -> updateNow()
                else -> {
                    val u = try { JSONObject(item.payload).optString("url", "") } catch (e: Exception) { "" }
                    if (u.isNotBlank()) context.startActivity(
                        Intent(Intent.ACTION_VIEW, Uri.parse(u)).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                    )
                }
            }
        } catch (e: Exception) {
        }
    }

    // načti inbox při otevření + periodicky každých ~12 s
    LaunchedEffect(token) {
        if (token.trim().isNotEmpty()) {
            loadNotifs()
            while (true) {
                delay(12000)
                loadNotifs()
            }
        }
    }

    val callLogPerm = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { _ -> }

    fun startService() {
        prefs.edit().putBoolean(KEY_SERVICE, true).apply()
        DialPollService.start(context)
        serviceOn = true
        Toast.makeText(context, "Naslouchání zapnuto", Toast.LENGTH_SHORT).show()
        if (ContextCompat.checkSelfPermission(
                context, Manifest.permission.READ_CALL_LOG
            ) != PackageManager.PERMISSION_GRANTED
        ) {
            callLogPerm.launch(Manifest.permission.READ_CALL_LOG)
        }
        // Full-screen intent (Android 14+, dialer přes zamykací obrazovku) se
        // NEvynucuje automaticky — otevírání systémového nastavení po instalaci
        // mátlo uživatele. Povolení lze udělit přes doporučení „Zobrazit přes
        // celou obrazovku" (cmdSetting) nebo tlačítkem v nastavení. Marti 6.6.2026.
    }

    val notifPerm = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { _ -> startService() }

    fun toggleService(on: Boolean) {
        if (on) {
            if (token.trim().isEmpty()) {
                Toast.makeText(context, "Nejdřív spáruj telefon (QR) nebo ulož token", Toast.LENGTH_SHORT).show()
                return
            }
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU &&
                ContextCompat.checkSelfPermission(
                    context, Manifest.permission.POST_NOTIFICATIONS
                ) != PackageManager.PERMISSION_GRANTED
            ) {
                notifPerm.launch(Manifest.permission.POST_NOTIFICATIONS)
                return
            }
            startService()
        } else {
            prefs.edit().putBoolean(KEY_SERVICE, false).apply()
            DialPollService.stop(context)
            serviceOn = false
            Toast.makeText(context, "Naslouchání vypnuto", Toast.LENGTH_SHORT).show()
        }
    }

    fun pairFromQr() {
        GmsBarcodeScanning.getClient(context).startScan()
            .addOnSuccessListener { b ->
                val raw = b.rawValue
                if (raw.isNullOrBlank()) {
                    Toast.makeText(context, "Prázdný QR kód", Toast.LENGTH_SHORT).show()
                    return@addOnSuccessListener
                }
                try {
                    val uri = Uri.parse(raw)
                    val u = uri.getQueryParameter("u")
                    val t = uri.getQueryParameter("t")
                    if (!u.isNullOrBlank() && !t.isNullOrBlank()) {
                        serverUrl = u
                        token = t
                        prefs.edit()
                            .putString(KEY_URL, u.trim())
                            .putString(KEY_TOKEN, t.trim())
                            .apply()
                        Toast.makeText(context, "Spárováno ✓", Toast.LENGTH_SHORT).show()
                        toggleService(true)
                    } else {
                        Toast.makeText(context, "QR neobsahuje párovací údaje", Toast.LENGTH_SHORT).show()
                    }
                } catch (e: Exception) {
                    Toast.makeText(context, "QR se nepodařilo přečíst", Toast.LENGTH_SHORT).show()
                }
            }
            .addOnFailureListener {
                Toast.makeText(context, "Skener QR není dostupný", Toast.LENGTH_SHORT).show()
            }
            .addOnCanceledListener { }
    }

    // Po nové instalaci/aktualizaci appky naslouchání VŽDY zapni automaticky
    // (Marti 6.6.2026). Když si ho uživatel později vypne ručně (stejná verze),
    // při dalším otevření ho nenutíme — jen ho na hlavní obrazovce doporučíme.
    var bootChecked by remember { mutableStateOf(false) }
    LaunchedEffect(token) {
        if (bootChecked || token.trim().isEmpty()) return@LaunchedEffect
        bootChecked = true
        val cur = BuildConfig.VERSION_CODE
        val last = prefs.getInt(KEY_LAST_VER, -1)
        if (last != cur) {
            prefs.edit().putInt(KEY_LAST_VER, cur).apply()
            if (!serviceOn) {
                delay(500)  // počkej na popředí (dialog oprávnění)
                toggleService(true)
            }
        }
    }

    // Po automatickém spárování (PairActivity) appka jen uloží token a spustí
    // službu — runtime oprávnění (notifikace / call-log / celá obrazovka) se ale
    // nevyžádají. Bez nich služba na pozadí nevyvolá vytáčení. Když je appka
    // spárovaná a běží, ale některé oprávnění chybí, spustíme stejný řetězec
    // žádostí jako manuální „Spustit službu". Jen jednou na otevření. Marti 5.6.
    var autoPermChecked by remember { mutableStateOf(false) }
    LaunchedEffect(serviceOn, token) {
        if (autoPermChecked) return@LaunchedEffect
        if (!serviceOn || token.trim().isEmpty()) return@LaunchedEffect
        autoPermChecked = true
        delay(600)  // počkej, až je obrazovka v popředí (dialogy oprávnění to vyžadují)
        val needNotif = Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU &&
            ContextCompat.checkSelfPermission(
                context, Manifest.permission.POST_NOTIFICATIONS
            ) != PackageManager.PERMISSION_GRANTED
        val needCallLog = ContextCompat.checkSelfPermission(
            context, Manifest.permission.READ_CALL_LOG
        ) != PackageManager.PERMISSION_GRANTED
        if (needNotif || needCallLog) {
            toggleService(true)
        } else if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O &&
                   !context.packageManager.canRequestPackageInstalls()) {
            // Až jsou základní oprávnění hotová, navedeme na povolení instalace
            // aktualizací (jednou) — pak budoucí verze chodí jako „Aktualizovat?".
            toastMain("Pro hladké aktualizace povol „Instalace neznámých aplikací“ pro STRATEGIE")
            openInstallSources()
        }
    }

    // Stav „Instalace neznámých aplikací" obnov při otevření Nastavení
    // (uživatel se může vrátit z OS nastavení s nově uděleným povolením).
    LaunchedEffect(showSettings) {
        canInstall = canInstallUnknown()
    }

    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // ── Hlavička jako v ERP: modré logo + avatar + „Tvoje Marti" + ⚙ ──
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                "STRATEGIE",
                color = BRAND_BLUE,
                fontWeight = FontWeight.Bold,
                fontSize = 20.sp
            )
            Spacer(Modifier.width(12.dp))
            Box(
                modifier = Modifier.size(36.dp).clip(CircleShape).background(BRAND_BLUE),
                contentAlignment = Alignment.Center
            ) {
                Text("M", color = Color.White, fontWeight = FontWeight.Bold)
                AsyncImage(
                    model = ImageRequest.Builder(context)
                        .data(base() + "/api/v1/erp/app/avatar")
                        .addHeader("Authorization", "Bearer " + token.trim())
                        .crossfade(true)
                        .build(),
                    contentDescription = "Marti-AI",
                    contentScale = ContentScale.Crop,
                    modifier = Modifier.size(36.dp).clip(CircleShape)
                )
            }
            Spacer(Modifier.width(8.dp))
            Text("Tvoje Marti", fontSize = 15.sp, fontWeight = FontWeight.Medium)
            Spacer(Modifier.weight(1f))
            Text(
                if (notifs.isEmpty()) "🔔" else "🔔 " + notifs.size,
                fontSize = 20.sp,
                color = if (notifs.isEmpty()) Color.Unspecified else Color(0xFFE0B070),
                fontWeight = FontWeight.Bold,
                modifier = Modifier
                    .clip(CircleShape)
                    .clickable { showSettings = false; loadNotifs() }
                    .padding(6.dp)
            )
            Spacer(Modifier.width(4.dp))
            Text(
                "⚙",
                fontSize = 24.sp,
                modifier = Modifier
                    .clip(CircleShape)
                    .clickable { showSettings = !showSettings }
                    .padding(6.dp)
            )
        }

        HorizontalDivider()

        if (showSettings) {
            SettingsBody(
                serverUrl = serverUrl,
                token = token,
                onServerUrl = { serverUrl = it },
                onToken = { token = it },
                serviceOn = serviceOn,
                serverVersionCode = serverVersionCode,
                serverVersionName = serverVersionName,
                updating = updating,
                onUpdate = { updateNow() },
                onCheck = { checkVersion(true) },
                canInstall = canInstall,
                onAllowInstall = { openInstallSources() },
                onSave = {
                    prefs.edit()
                        .putString(KEY_URL, serverUrl.trim())
                        .putString(KEY_TOKEN, token.trim())
                        .apply()
                    Toast.makeText(context, "Nastavení uloženo", Toast.LENGTH_SHORT).show()
                },
                onLoginPair = { open("/app-pair") },
                onToggle = { toggleService(it) },
                onBack = { showSettings = false }
            )
        } else {
            HomeBody(
                paired = token.trim().isNotEmpty(),
                serviceOn = serviceOn,
                onLoginPair = { open("/app-pair") },
                onChat = { open("/") },
                onErp = { open("/erp") },
                onPinChat = { pinShortcut("stg_chat", "Marti-AI - STRATEGIE", "/", "chat") },
                onPinErp = { pinShortcut("stg_erp", "ERP - STRATEGIE", "/erp", "erp") },
                onToggle = { toggleService(it) },
                notifs = notifs,
                notifSel = notifSel,
                onSelectNotif = { replyText = ""; notifSel = if (notifSel == it) -1L else it },
                onAct = { item, decision, note -> actCmd(item, decision, note) },
                onSetting = { cmdSetting(it) },
                onRefresh = { loadNotifs() },
                replyText = replyText,
                onReplyChange = { replyText = it }
            )
        }
    }
}

@Composable
private fun HomeBody(
    paired: Boolean,
    serviceOn: Boolean,
    onLoginPair: () -> Unit,
    onChat: () -> Unit,
    onErp: () -> Unit,
    onPinChat: () -> Unit,
    onPinErp: () -> Unit,
    onToggle: (Boolean) -> Unit = {},
    notifs: List<CmdItem> = emptyList(),
    notifSel: Long = -1L,
    onSelectNotif: (Long) -> Unit = {},
    onAct: (CmdItem, String, String) -> Unit = { _, _, _ -> },
    onSetting: (CmdItem) -> Unit = {},
    onRefresh: () -> Unit = {},
    replyText: String = "",
    onReplyChange: (String) -> Unit = {},
) {
    if (!paired) {
        Text(
            "Telefon zatím není spárovaný.",
            style = MaterialTheme.typography.titleMedium
        )
        Text(
            "Stačí se přihlásit — appka se pak nastaví sama.",
            style = MaterialTheme.typography.bodyMedium
        )
        Button(onClick = onLoginPair, modifier = Modifier.fillMaxWidth()) {
            Text("🔗 Přihlásit a spárovat")
        }
    } else {
        // ── Inbox notifikací (úkoly od Clauda) — jako e-maily v Outlooku ──
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                "🔔 Notifikace" + if (notifs.isEmpty()) "" else " (" + notifs.size + ")",
                style = MaterialTheme.typography.titleMedium
            )
            Spacer(Modifier.weight(1f))
            Text(
                "🔄",
                fontSize = 18.sp,
                modifier = Modifier.clip(CircleShape).clickable { onRefresh() }.padding(6.dp)
            )
        }
        if (notifs.isEmpty()) {
            Text(
                "Žádné notifikace.",
                color = Color(0xFF8a96a4),
                style = MaterialTheme.typography.bodyMedium
            )
        } else {
            for (n in notifs) {
                val open = notifSel == n.id
                val icon = when (n.type) {
                    "claude_confirm" -> "✅"
                    "claude_msg" -> "💬"
                    "update" -> "📥"
                    else -> "⚙"
                }
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(10.dp))
                        .background(if (open) Color(0xFF14202c) else Color(0xFF11181f))
                        .clickable { onSelectNotif(n.id) }
                        .padding(12.dp)
                ) {
                    Text(icon + "  " + n.title, fontWeight = FontWeight.Medium, fontSize = 14.sp)
                    if (n.msg.isNotBlank()) {
                        Text(
                            n.msg,
                            color = Color(0xFFbcc6d2),
                            style = MaterialTheme.typography.bodySmall,
                            maxLines = if (open) 12 else 2
                        )
                    }
                    if (open) {
                        if (n.type == "claude_msg") {
                            OutlinedTextField(
                                value = replyText,
                                onValueChange = onReplyChange,
                                label = { Text("Odpovědět Claudovi…") },
                                modifier = Modifier.fillMaxWidth().padding(top = 8.dp)
                            )
                            Row(
                                modifier = Modifier.fillMaxWidth().padding(top = 8.dp),
                                horizontalArrangement = Arrangement.spacedBy(8.dp)
                            ) {
                                Button(
                                    onClick = { onAct(n, "done", replyText) },
                                    enabled = replyText.isNotBlank(),
                                    modifier = Modifier.weight(1f)
                                ) { Text("Odpovědět") }
                                OutlinedButton(
                                    onClick = { onChat(); onAct(n, "done", "") },
                                    modifier = Modifier.weight(1f)
                                ) { Text("Chat") }
                                OutlinedButton(
                                    onClick = { onAct(n, "done", "") },
                                    modifier = Modifier.weight(1f)
                                ) { Text("Zavřít") }
                            }
                        } else {
                            Row(
                                modifier = Modifier.fillMaxWidth().padding(top = 8.dp),
                                horizontalArrangement = Arrangement.spacedBy(8.dp)
                            ) {
                                when (n.type) {
                                    "claude_confirm" -> {
                                        Button(
                                            onClick = { onAct(n, "accept", "") },
                                            modifier = Modifier.weight(1f)
                                        ) { Text("Povolit") }
                                        OutlinedButton(
                                            onClick = { onAct(n, "reject", "") },
                                            modifier = Modifier.weight(1f)
                                        ) { Text("Odmítnout") }
                                    }
                                    else -> {
                                        Button(
                                            onClick = { onSetting(n); onAct(n, "accept", "") },
                                            modifier = Modifier.weight(1f)
                                        ) { Text("Povolit") }
                                        OutlinedButton(
                                            onClick = { onAct(n, "reject", "") },
                                            modifier = Modifier.weight(1f)
                                        ) { Text("Teď ne") }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        HorizontalDivider()
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    if (serviceOn) "🟢 Naslouchání zapnuto" else "🔴 Naslouchání vypnuto",
                    style = MaterialTheme.typography.titleMedium
                )
                Text(
                    if (serviceOn)
                        "Appka přijímá vytáčení z ERP. V liště telefonu svítí ikona."
                    else
                        "Zapni, ať telefon přijímá vytáčení z ERP.",
                    style = MaterialTheme.typography.bodySmall
                )
            }
            Switch(checked = serviceOn, onCheckedChange = onToggle)
        }
        Text(
            "Dvojklik na telefonní číslo v ERP vyvolá na tomto telefonu vytáčení.",
            style = MaterialTheme.typography.bodySmall
        )
    }

    Spacer(Modifier.width(0.dp))
    Text("Přidat ikonu na plochu", style = MaterialTheme.typography.titleMedium)
    Button(onClick = onPinChat, modifier = Modifier.fillMaxWidth()) { Text("📌 Ikonu Chat na plochu") }
    OutlinedButton(onClick = onPinErp, modifier = Modifier.fillMaxWidth()) { Text("📌 Ikonu ERP na plochu") }
    Text(
        "Vytvoří ikonu na ploše (na aktuální stránce). Otevře appku samostatně, bez téhle aplikace.",
        style = MaterialTheme.typography.bodySmall
    )
    Spacer(Modifier.width(0.dp))
    Text("Otevřít rovnou", style = MaterialTheme.typography.titleMedium)
    Button(onClick = onChat, modifier = Modifier.fillMaxWidth()) { Text("📲 Otevřít Chat") }
    OutlinedButton(onClick = onErp, modifier = Modifier.fillMaxWidth()) { Text("📲 Otevřít ERP") }
    Text(
        "Když launcher ikonu nepřidá sám, otevři tu appku a v prohlížeči zvol ⋮ → Přidat na plochu.",
        style = MaterialTheme.typography.bodySmall
    )
}

@Composable
private fun SettingsBody(
    serverUrl: String,
    token: String,
    onServerUrl: (String) -> Unit,
    onToken: (String) -> Unit,
    serviceOn: Boolean,
    serverVersionCode: Int,
    serverVersionName: String,
    updating: Boolean,
    onUpdate: () -> Unit,
    onCheck: () -> Unit,
    canInstall: Boolean,
    onAllowInstall: () -> Unit,
    onSave: () -> Unit,
    onLoginPair: () -> Unit,
    onToggle: (Boolean) -> Unit,
    onBack: () -> Unit,
) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Text(
            "‹ Zpět",
            color = BRAND_BLUE,
            modifier = Modifier.clickable { onBack() }.padding(end = 12.dp)
        )
        Text("Nastavení", style = MaterialTheme.typography.titleMedium)
    }

    // Verze appky (s datem a časem buildu) + ruční kontrola/stažení.
    Text(
        "Verze appky: ${BuildConfig.VERSION_NAME} (${BuildConfig.VERSION_CODE}) · ${BuildConfig.BUILD_TIME}",
        style = MaterialTheme.typography.bodyMedium
    )
    if (serverVersionCode > 0) {
        Text(
            "Na serveru: $serverVersionName ($serverVersionCode)",
            style = MaterialTheme.typography.bodySmall
        )
    }
    if (serverVersionCode > BuildConfig.VERSION_CODE) {
        Text(
            "🔔 Je k dispozici novější verze",
            color = Color(0xFFE0B070),
            style = MaterialTheme.typography.bodySmall
        )
    } else if (serverVersionCode > 0) {
        Text(
            "✓ Máš aktuální verzi",
            color = Color(0xFF7FD6C2),
            style = MaterialTheme.typography.bodySmall
        )
    }
    OutlinedButton(onClick = onCheck, modifier = Modifier.fillMaxWidth()) {
        Text("🔄 Zkontrolovat verzi")
    }
    // Instalace aktualizací — jednorázové povolení, ať budoucí verze chodí hladce
    if (!canInstall) {
        Text(
            "⚠ Pro hladké aktualizace povol instalaci",
            color = Color(0xFFE0B070),
            style = MaterialTheme.typography.bodySmall
        )
        Button(onClick = onAllowInstall, modifier = Modifier.fillMaxWidth()) {
            Text("📥 Povolit instalaci aktualizací")
        }
    } else {
        Text(
            "✓ Instalace aktualizací povolena",
            color = Color(0xFF7FD6C2),
            style = MaterialTheme.typography.bodySmall
        )
    }
    if (serverVersionCode > 0) {
        Button(
            onClick = onUpdate, enabled = !updating,
            modifier = Modifier.fillMaxWidth()
        ) {
            Text(
                when {
                    updating -> "Stahuji…"
                    serverVersionCode > BuildConfig.VERSION_CODE ->
                        "📥 Stáhnout a nainstalovat verzi $serverVersionName"
                    else -> "📥 Přeinstalovat verzi $serverVersionName"
                }
            )
        }
    }
    HorizontalDivider()

    Button(onClick = onLoginPair, modifier = Modifier.fillMaxWidth()) {
        Text("🔗 Přihlásit a spárovat")
    }
    Text(
        "Doporučeno — přihlas se a appka se nastaví sama.",
        style = MaterialTheme.typography.bodySmall
    )

    HorizontalDivider()

    OutlinedTextField(
        value = serverUrl,
        onValueChange = onServerUrl,
        label = { Text("Adresa serveru") },
        singleLine = true,
        keyboardOptions = KeyboardOptions(
            keyboardType = KeyboardType.Uri,
            capitalization = KeyboardCapitalization.None
        ),
        modifier = Modifier.fillMaxWidth()
    )
    OutlinedTextField(
        value = token,
        onValueChange = onToken,
        label = { Text("Token (z ERP → Synchronizace s telefonem)") },
        singleLine = true,
        visualTransformation = PasswordVisualTransformation(),
        modifier = Modifier.fillMaxWidth()
    )
    Button(onClick = onSave, modifier = Modifier.fillMaxWidth()) { Text("Uložit nastavení") }

    HorizontalDivider()

    Row(
        modifier = Modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Column(modifier = Modifier.weight(1f)) {
            Text("Naslouchat vytáčení", style = MaterialTheme.typography.titleMedium)
            Text(
                if (serviceOn) "Běží na pozadí" else "Vypnuto",
                style = MaterialTheme.typography.bodySmall
            )
        }
        Switch(checked = serviceOn, onCheckedChange = onToggle)
    }
}
