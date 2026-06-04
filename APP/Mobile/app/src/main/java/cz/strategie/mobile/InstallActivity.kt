package cz.strategie.mobile

import android.app.Activity
import android.content.Intent
import android.os.Bundle
import androidx.core.content.FileProvider
import java.io.File

/**
 * Tichá aktivita: spustí systémový instalátor pro staženou APK (samo-aktualizace).
 * Cíl tapu na notifikaci „Nová verze". Android 8+ při první instalaci vyžádá
 * povolení „Instalovat neznámé aplikace" pro tuto appku — to je jednorázové.
 */
class InstallActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val path = intent.getStringExtra(EXTRA_APK)
        if (path != null) {
            try {
                val uri = FileProvider.getUriForFile(
                    this, "$packageName.fileprovider", File(path)
                )
                startActivity(Intent(Intent.ACTION_VIEW).apply {
                    setDataAndType(uri, "application/vnd.android.package-archive")
                    addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                    addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                })
            } catch (e: Exception) {
            }
        }
        finish()
    }

    companion object {
        const val EXTRA_APK = "apk_path"
    }
}
