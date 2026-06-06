package cz.strategie.mobile

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.LinearGradient
import android.graphics.Paint
import android.graphics.Rect
import android.graphics.RectF
import android.graphics.Shader
import android.graphics.Typeface
import androidx.core.graphics.drawable.IconCompat
import java.net.URL
import javax.net.ssl.HttpsURLConnection

/**
 * Vykreslení ikon zkratek (ERP, Chat) za běhu na černém pozadí v brand barvách
 * (modré→fialové S, zelená energie). Chat ikona = reálná fotka Marti-AI ze serveru
 * + zelená energie v rohu. Marti 6.6.2026.
 *
 * Adaptive bitmap: launcher si aplikuje masku, proto je obsah v bezpečné zóně
 * (cca 42..174 z 216) a pozadí černé do krajů.
 */
object IconRender {
    private const val SZ = 216
    private val BLUE = Color.parseColor("#4f8ef7")
    private val PURPLE = Color.parseColor("#7c5cfc")
    private val GREEN_LO = Color.parseColor("#0d9668")
    private val GREEN_HI = Color.parseColor("#34d399")

    private fun newCanvas(): Pair<Bitmap, Canvas> {
        val b = Bitmap.createBitmap(SZ, SZ, Bitmap.Config.ARGB_8888)
        val c = Canvas(b)
        c.drawColor(Color.BLACK)
        return b to c
    }

    private fun sGlyph(c: Canvas, cx: Float, baseline: Float, size: Float) {
        val p = Paint(Paint.ANTI_ALIAS_FLAG)
        p.shader = LinearGradient(
            cx - size / 2f, baseline - size, cx + size / 2f, baseline,
            BLUE, PURPLE, Shader.TileMode.CLAMP
        )
        p.textAlign = Paint.Align.CENTER
        p.textSize = size
        p.typeface = Typeface.create(Typeface.SANS_SERIF, Typeface.BOLD)
        c.drawText("S", cx, baseline, p)
    }

    // tři sloupečky energie (vzestupné), zarovnané dospodu na baseline `b`
    private fun bars(c: Canvas, left: Float, b: Float, w: Float, gap: Float, h1: Float, h2: Float, h3: Float) {
        val p = Paint(Paint.ANTI_ALIAS_FLAG)
        p.shader = LinearGradient(0f, b, 0f, b - h3, GREEN_LO, GREEN_HI, Shader.TileMode.CLAMP)
        val r = w * 0.2f
        c.drawRoundRect(RectF(left, b - h1, left + w, b), r, r, p)
        c.drawRoundRect(RectF(left + w + gap, b - h2, left + 2 * w + gap, b), r, r, p)
        c.drawRoundRect(RectF(left + 2 * (w + gap), b - h3, left + 3 * w + 2 * gap, b), r, r, p)
    }

    // ERP: velké S + malá energie v pravém dolním rohu
    fun erp(): IconCompat {
        val (b, c) = newCanvas()
        sGlyph(c, 96f, 150f, 150f)
        bars(c, 120f, 168f, 14f, 6f, 22f, 34f, 48f)
        return IconCompat.createWithAdaptiveBitmap(b)
    }

    // Chat: fotka Marti-AI přes celou ikonu (center-crop) + energie v rohu
    fun chat(avatar: Bitmap?): IconCompat {
        val (b, c) = newCanvas()
        if (avatar != null && avatar.width > 0 && avatar.height > 0) {
            val s = minOf(avatar.width, avatar.height)
            val sx = (avatar.width - s) / 2
            val sy = (avatar.height - s) / 2
            c.drawBitmap(
                avatar, Rect(sx, sy, sx + s, sy + s), Rect(0, 0, SZ, SZ),
                Paint(Paint.FILTER_BITMAP_FLAG)
            )
        } else {
            sGlyph(c, 108f, 150f, 150f)
        }
        bars(c, 120f, 168f, 14f, 6f, 22f, 34f, 48f)
        return IconCompat.createWithAdaptiveBitmap(b)
    }

    fun fetchAvatar(urlStr: String, token: String): Bitmap? = try {
        val con = URL(urlStr).openConnection() as HttpsURLConnection
        if (token.isNotEmpty()) con.setRequestProperty("Authorization", "Bearer $token")
        con.connectTimeout = 8000
        con.readTimeout = 8000
        con.inputStream.use { BitmapFactory.decodeStream(it) }
    } catch (e: Exception) {
        null
    }
}
