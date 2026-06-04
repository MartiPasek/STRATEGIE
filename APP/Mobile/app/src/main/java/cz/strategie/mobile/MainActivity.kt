package cz.strategie.mobile

import android.Manifest
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
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
import coil.compose.AsyncImage
import coil.request.ImageRequest
import com.google.android.gms.codescanner.GmsBarcodeScanning
import cz.strategie.mobile.ui.theme.STRATEGIEMobileTheme

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

    fun base(): String = serverUrl.trim().trimEnd('/')

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
                onSave = {
                    prefs.edit()
                        .putString(KEY_URL, serverUrl.trim())
                        .putString(KEY_TOKEN, token.trim())
                        .apply()
                    Toast.makeText(context, "Nastavení uloženo", Toast.LENGTH_SHORT).show()
                },
                onPair = { pairFromQr() },
                onToggle = { toggleService(it) },
                onBack = { showSettings = false }
            )
        } else {
            HomeBody(
                paired = token.trim().isNotEmpty(),
                serviceOn = serviceOn,
                onPair = { pairFromQr() },
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
    onPair: () -> Unit,
    onChat: () -> Unit,
    onErp: () -> Unit,
) {
    if (!paired) {
        Text(
            "Telefon zatím není spárovaný.",
            style = MaterialTheme.typography.titleMedium
        )
        Text(
            "V ERP otevři „Synchronizace s telefonem“ a naskenuj QR kód.",
            style = MaterialTheme.typography.bodyMedium
        )
        Button(onClick = onPair, modifier = Modifier.fillMaxWidth()) {
            Text("📷 Spárovat QR kódem")
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
    Text("Otevřít aplikace", style = MaterialTheme.typography.titleMedium)
    Button(onClick = onChat, modifier = Modifier.fillMaxWidth()) { Text("Otevřít Chat") }
    OutlinedButton(onClick = onErp, modifier = Modifier.fillMaxWidth()) { Text("Otevřít ERP") }
}

@Composable
private fun SettingsBody(
    serverUrl: String,
    token: String,
    onServerUrl: (String) -> Unit,
    onToken: (String) -> Unit,
    serviceOn: Boolean,
    onSave: () -> Unit,
    onPair: () -> Unit,
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

    Button(onClick = onPair, modifier = Modifier.fillMaxWidth()) {
        Text("📷 Spárovat QR kódem z PC")
    }
    Text(
        "Doporučeno — naskenuj QR z ERP, vyplní adresu i token a zapne naslouchání.",
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
