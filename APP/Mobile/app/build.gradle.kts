import java.io.FileInputStream
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Properties

plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.compose)
}

// Release podpis: hesla + klíč jen lokálně v keystore.properties (gitignored).
// Bez toho souboru se release build podepíše debug klíčem (vývoj). Marti 4.6.
val keystorePropsFile = rootProject.file("keystore.properties")
val keystoreProps = Properties().apply {
    if (keystorePropsFile.exists()) load(FileInputStream(keystorePropsFile))
}

// Verze z version.properties; RELEASE build ji automaticky zvýší (predchozi+1:
// versionCode++ a posledni segment versionName, napr. 1.2 -> 1.3). Marti 5.6.
fun bumpLastSegment(v: String): String {
    val parts = v.split(".").toMutableList()
    val last = parts.lastOrNull()?.toIntOrNull() ?: return "$v.1"
    parts[parts.size - 1] = (last + 1).toString()
    return parts.joinToString(".")
}
val versionPropsFile = rootProject.file("version.properties")
val versionProps = Properties().apply {
    if (versionPropsFile.exists()) load(FileInputStream(versionPropsFile))
}
var appVersionCode = (versionProps.getProperty("versionCode") ?: "1").trim().toInt()
var appVersionName = (versionProps.getProperty("versionName") ?: "1.0").trim()
val isReleaseBuild = gradle.startParameter.taskNames.any {
    it.contains("Release", ignoreCase = true)
}
if (isReleaseBuild && versionPropsFile.exists()) {
    appVersionCode += 1
    appVersionName = bumpLastSegment(appVersionName)
    versionProps.setProperty("versionCode", appVersionCode.toString())
    versionProps.setProperty("versionName", appVersionName)
    versionPropsFile.outputStream().use { versionProps.store(it, "auto-bump (release build)") }
}

android {
    namespace = "cz.strategie.mobile"
    compileSdk {
        version = release(36) {
            minorApiLevel = 1
        }
    }

    defaultConfig {
        applicationId = "cz.strategie.mobile"
        minSdk = 26
        targetSdk = 36
        versionCode = appVersionCode
        versionName = appVersionName
        // Datum + čas buildu (zobrazí se u verze v appce).
        buildConfigField(
            "String", "BUILD_TIME",
            "\"" + SimpleDateFormat("yyyy-MM-dd HH:mm").format(Date()) + "\""
        )

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    signingConfigs {
        create("release") {
            if (keystorePropsFile.exists()) {
                storeFile = rootProject.file(keystoreProps["storeFile"] as String)
                storePassword = keystoreProps["storePassword"] as String
                keyAlias = keystoreProps["keyAlias"] as String
                keyPassword = keystoreProps["keyPassword"] as String
            }
        }
    }

    buildTypes {
        release {
            // Pokud existuje keystore.properties → release podpis (stálý klíč pro
            // auto-update napříč verzemi). Jinak fallback na debug podpis.
            signingConfig = if (keystorePropsFile.exists())
                signingConfigs.getByName("release") else signingConfigs.getByName("debug")
            // R8 ZAPNUTY (Jirka 27.7.2026) — doporuceni Google Play u vydani 1.74
            // ("Optimalizaci R8 muzete zlepsit pamet a vykon aplikace").
            // ⚠️ Keep pravidla pro JS most (@JavascriptInterface, 33 metod) jsou
            // v app/proguard-rules.pro — BEZ NICH SE APPKA ROZBIJE. Nemazat.
            optimization {
                enable = true
            }
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
            // Nativni debug symboly do AAB (Play doporuceni u buildu s nativnim
            // kodem z knihoven) - lepsi analyza padu/ANR v produkci. Projevi se
            // az pri pristim buildu (soucasny interni v73 ho jeste nema). Jirka 29.6.
            ndk {
                debugSymbolLevel = "FULL"
            }
        }
    }

    // Dvě distribuční varianty (Jirka 26.6.2026, kvůli Google Play review):
    //  - play     = AAB do Google Play. BEZ SMS oprávnění (sedí s /privacy, projde
    //               review). SMS deklarace jsou jen ve flavoru `internal` (manifest
    //               app/src/internal/AndroidManifest.xml).
    //  - internal = sideload APK (54 uživatelů + gateway telefon). SE SMS bránou.
    // Oba sdílí applicationId cz.strategie.mobile (plynulý přechod sideload→Play).
    flavorDimensions += "distribution"
    productFlavors {
        create("play") {
            dimension = "distribution"
        }
        create("internal") {
            dimension = "distribution"
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }
    buildFeatures {
        compose = true
        buildConfig = true
    }
}

dependencies {
    implementation(platform(libs.androidx.compose.bom))
    implementation(libs.androidx.activity.compose)
    implementation(libs.androidx.compose.material3)
    implementation(libs.androidx.compose.ui)
    implementation(libs.androidx.compose.ui.graphics)
    implementation(libs.androidx.compose.ui.tooling.preview)
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.lifecycle.runtime.ktx)
    // Vynuceni novejsi androidx.fragment (Google Play hlasilo zastaralou
    // tranzitivni verzi u vydani 72). Jirka 29.6.2026.
    implementation(libs.androidx.fragment)
    // QR skener pro spárování s PC (Google Code Scanner — UI z Play Services)
    implementation("com.google.android.gms:play-services-code-scanner:16.1.0")
    // Avatar Marti-AI v hlavičce (načtení obrázku ze serveru s Bearer tokenem)
    implementation("io.coil-kt:coil-compose:2.7.0")
    testImplementation(libs.junit)
    androidTestImplementation(platform(libs.androidx.compose.bom))
    androidTestImplementation(libs.androidx.compose.ui.test.junit4)
    androidTestImplementation(libs.androidx.espresso.core)
    androidTestImplementation(libs.androidx.junit)
    debugImplementation(libs.androidx.compose.ui.test.manifest)
    debugImplementation(libs.androidx.compose.ui.tooling)
}