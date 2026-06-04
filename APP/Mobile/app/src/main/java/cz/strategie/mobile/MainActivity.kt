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
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
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
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.input.KeyboardCapitalization
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import cz.strategie.mobile.ui.theme.STRATEGIEMobileTheme

private const val PREFS = "strategie_prefs"
private const val KEY_URL = "server_url"
private const val KEY_TOKEN = "token"
private const val KEY_SERVICE = "service_enabled"
private const val DEFAULT_URL = "https://strategie-ai.com"

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            STRATEGIEMobileTheme {
                Scaffold(modifier = Modifier.fillMaxSize()) { innerPadding ->
                    SettingsScreen(modifier = Modifier.padding(innerPadding))
                }
            }
        }
    }
}

@Composable
fun SettingsScreen(modifier: Modifier = Modifier) {
    val context = LocalContext.current
    val prefs = remember { context.getSharedPreferences(PREFS, Context.MODE_PRIVATE) }

    var serverUrl by remember {
        mutableStateOf(prefs.getString(KEY_URL, DEFAULT_URL) ?: DEFAULT_URL)
    }
    var token by remember {
        mutableStateOf(prefs.getString(KEY_TOKEN, "") ?: "")
    }
    var serviceOn by remember {
        mutableStateOf(prefs.getBoolean(KEY_SERVICE, false))
    }

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
    ) { _ -> /* bez něj jen nečteme call-log; vytáčení běží dál */ }

    fun startService() {
        prefs.edit().putBoolean(KEY_SERVICE, true).apply()
        DialPollService.start(context)
        serviceOn = true
        Toast.makeText(context, "Naslouchání zapnuto", Toast.LENGTH_SHORT).show()
        // Doba/start hovoru z call-logu — vyžádej READ_CALL_LOG (nepovinné).
        if (ContextCompat.checkSelfPermission(
                context, Manifest.permission.READ_CALL_LOG
            ) != PackageManager.PERMISSION_GRANTED
        ) {
            callLogPerm.launch(Manifest.permission.READ_CALL_LOG)
        }
    }

    val notifPerm = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { _ ->
        // I bez povolení notifikací poll běží — jen by nebyla vidět notifikace.
        startService()
    }

    fun toggleService(on: Boolean) {
        if (on) {
            if (token.trim().isEmpty()) {
                Toast.makeText(context, "Nejdřív ulož token", Toast.LENGTH_SHORT).show()
                return
            }
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU &&
                ContextCompat.checkSelfPermission(
                    context, Manifest.permission.POST_NOTIFICATIONS
                ) != PackageManager.PERMISSION_GRANTED
            ) {
                notifPerm.launch(Manifest.permission.POST_NOTIFICATIONS)
                return  // služba se spustí po udělení v callbacku
            }
            startService()
        } else {
            prefs.edit().putBoolean(KEY_SERVICE, false).apply()
            DialPollService.stop(context)
            serviceOn = false
            Toast.makeText(context, "Naslouchání vypnuto", Toast.LENGTH_SHORT).show()
        }
    }

    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        Text("STRATEGIE", style = MaterialTheme.typography.headlineMedium)
        Text("Mobilní pomocník", style = MaterialTheme.typography.bodyMedium)

        OutlinedTextField(
            value = serverUrl,
            onValueChange = { serverUrl = it },
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
            onValueChange = { token = it },
            label = { Text("Token (z ERP → Synchronizace s telefonem)") },
            singleLine = true,
            visualTransformation = PasswordVisualTransformation(),
            modifier = Modifier.fillMaxWidth()
        )

        Button(
            onClick = {
                prefs.edit()
                    .putString(KEY_URL, serverUrl.trim())
                    .putString(KEY_TOKEN, token.trim())
                    .apply()
                Toast.makeText(context, "Nastavení uloženo", Toast.LENGTH_SHORT).show()
            },
            modifier = Modifier.fillMaxWidth()
        ) { Text("Uložit nastavení") }

        HorizontalDivider(modifier = Modifier.padding(vertical = 6.dp))

        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text("Naslouchat vytáčení", style = MaterialTheme.typography.titleMedium)
                Text(
                    if (serviceOn) "Běží na pozadí — dvojklik na telefon v ERP vyvolá vytáčení"
                    else "Vypnuto",
                    style = MaterialTheme.typography.bodySmall
                )
            }
            Switch(checked = serviceOn, onCheckedChange = { toggleService(it) })
        }

        HorizontalDivider(modifier = Modifier.padding(vertical = 6.dp))

        Text("Otevřít aplikace", style = MaterialTheme.typography.titleMedium)

        Button(
            onClick = { open("/") },
            modifier = Modifier.fillMaxWidth()
        ) { Text("Otevřít Chat") }

        OutlinedButton(
            onClick = { open("/erp") },
            modifier = Modifier.fillMaxWidth()
        ) { Text("Otevřít ERP") }
    }
}

@Preview(showBackground = true)
@Composable
fun SettingsPreview() {
    STRATEGIEMobileTheme {
        SettingsScreen()
    }
}
