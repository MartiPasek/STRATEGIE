package cz.strategie.mobile

import android.Manifest
import android.app.NotificationManager
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
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
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
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

    fun base(): String = serverUrl.trim().trimEnd('/')

    // Zjisti nejnovější verzi na serveru (pro indikaci „nová verze" v nastavení).
    LaunchedEffect(serverUrl, token) {
        val t = token.trim()
        if (t.isEmpty()) return@LaunchedEffect
        thread {
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
                    }
                }
                c.disconnect()
            } catch (e: Exception) {
            }
        }
    }

    fun updateNow() {
        if (updating || serverVersionCode <= 0) return
        updating = true
        Toast.makeText(context, "Stahuji novou verzi…", Toast.LENGTH_SHORT).show()
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
        // Android 14+: aby po odemčení vyskočil rovnou dialer (full-screen intent),
        // appka potřebuje speciální povolení. Když chybí, otevři jeho nastavení.
        if (Build.VERSION.SDK_INT >= 34) {
            val nm = context.getSystemService(NotificationManager::class.java)
            if (nm != null && !nm.canUseFullScreenIntent()) {
                Toast.makeText(
                    context,
                    "Povol „Zobrazit přes celou obrazovku“ — pak dialer naskočí hned po odemčení",
                    Toast.LENGTH_LONG
                ).show()
                try {
                    context.startActivity(
                        Intent(Settings.ACTION_MANAGE_APP_USE_FULL_SCREEN_INTENT)
                            .setData(Uri.parse("package:" + context.packageName))
                    )
                } catch (e: Exception) {
                }
            }
        }
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
        val nm = context.getSystemService(NotificationManager::class.java)
        val needFsi = Build.VERSION.SDK_INT >= 34 &&
            nm != null && !nm.canUseFullScreenIntent()
        if (needNotif || needCallLog || needFsi) {
            toggleService(true)
        }
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
                onErp = { open("/erp") }
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
        Text(
            if (serviceOn) "✓ Naslouchání běží na pozadí"
            else "Naslouchání je vypnuté (zapni v ⚙ nastavení)",
            style = MaterialTheme.typography.titleMedium
        )
        Text(
            "Dvojklik na telefonní číslo v ERP vyvolá na tomto telefonu vytáčení.",
            style = MaterialTheme.typography.bodySmall
        )
    }

    Spacer(Modifier.width(0.dp))
    Text("Nainstalovat na plochu", style = MaterialTheme.typography.titleMedium)
    Button(onClick = onChat, modifier = Modifier.fillMaxWidth()) { Text("📲 Chat STRATEGIE") }
    OutlinedButton(onClick = onErp, modifier = Modifier.fillMaxWidth()) { Text("📲 ERP STRATEGIE") }
    Text(
        "Otevře se v prohlížeči — pak v nabídce (⋮) zvol „Přidat na plochu / Nainstalovat aplikaci“.",
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

    // Verze appky (s datem a časem buildu) + indikace nové verze na serveru.
    Text(
        "Verze appky: ${BuildConfig.VERSION_NAME} (${BuildConfig.VERSION_CODE}) · ${BuildConfig.BUILD_TIME}",
        style = MaterialTheme.typography.bodyMedium
    )
    if (serverVersionCode > BuildConfig.VERSION_CODE) {
        Text(
            "🔔 Na serveru je nová verze $serverVersionName",
            color = Color(0xFFE0B070),
            style = MaterialTheme.typography.bodySmall
        )
        Button(
            onClick = onUpdate, enabled = !updating,
            modifier = Modifier.fillMaxWidth()
        ) { Text(if (updating) "Stahuji…" else "📥 Stáhnout a nainstalovat novou verzi") }
    } else if (serverVersionCode > 0) {
        Text(
            "✓ Máš aktuální verzi",
            color = Color(0xFF7FD6C2),
            style = MaterialTheme.typography.bodySmall
        )
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
