package org.marcgames.iphone3gs

import android.app.Activity
import android.app.AlertDialog
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.RectF
import android.os.Bundle
import android.view.Gravity
import android.view.View
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView

class MainActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.statusBarColor = Color.rgb(18, 20, 25)
        window.navigationBarColor = Color.rgb(18, 20, 25)
        window.decorView.systemUiVisibility = 0

        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER_HORIZONTAL
            setPadding(dp(20), dp(18), dp(20), dp(18))
            setBackgroundColor(Color.rgb(18, 20, 25))
        }
        val title = TextView(this).apply {
            text = "iPhone 3GS Emulator"
            setTextColor(Color.WHITE)
            textSize = 23f
            gravity = Gravity.CENTER
        }
        val subtitle = TextView(this).apply {
            text = "iOS 6 • Development build"
            setTextColor(Color.rgb(166, 177, 194))
            textSize = 14f
            gravity = Gravity.CENTER
            setPadding(0, dp(5), 0, dp(10))
        }
        val device = IPhonePreviewView(this)
        val deviceParams = LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT, 0, 1f
        ).apply {
            topMargin = dp(8)
            bottomMargin = dp(8)
        }
        val status = TextView(this).apply {
            text = "UI prototype only — QEMU runtime is not connected yet."
            setTextColor(Color.rgb(255, 204, 102))
            textSize = 13f
            gravity = Gravity.CENTER
            setPadding(dp(8), dp(8), dp(8), dp(12))
        }
        val start = Button(this).apply {
            text = "Start emulation"
            isAllCaps = false
            setOnClickListener {
                AlertDialog.Builder(this@MainActivity)
                    .setTitle("Emulator runtime not ready")
                    .setMessage("This development build contains the centered iPhone preview. The QEMU ARM runtime and iOS 6 boot chain still need to be ported and connected before it can boot iOS.")
                    .setPositiveButton("OK", null)
                    .show()
            }
        }
        root.addView(title)
        root.addView(subtitle)
        root.addView(device, deviceParams)
        root.addView(status)
        root.addView(start, LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT
        ))
        setContentView(root)
    }

    private fun dp(value: Int): Int = (value * resources.displayMetrics.density).toInt()
}

private class IPhonePreviewView(context: android.content.Context) : View(context) {
    private val paint = Paint(Paint.ANTI_ALIAS_FLAG)

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        val w = width.toFloat()
        val h = height.toFloat()
        val phoneW = minOf(w * 0.68f, h * 0.48f, dp(300).toFloat())
        val phoneH = minOf(h * 0.91f, phoneW * 1.78f)
        val left = (w - phoneW) / 2f
        val top = (h - phoneH) / 2f
        val frame = RectF(left, top, left + phoneW, top + phoneH)

        paint.color = Color.rgb(8, 9, 11)
        canvas.drawRoundRect(frame, phoneW * 0.105f, phoneW * 0.105f, paint)

        paint.color = Color.rgb(72, 75, 80)
        canvas.drawRoundRect(
            RectF(frame.left + phoneW * .025f, frame.top + phoneH * .018f,
                frame.right - phoneW * .025f, frame.bottom - phoneH * .018f),
            phoneW * .09f, phoneW * .09f, paint
        )

        val screen = RectF(
            frame.left + phoneW * .085f, frame.top + phoneH * .135f,
            frame.right - phoneW * .085f, frame.bottom - phoneH * .17f
        )
        paint.color = Color.rgb(18, 33, 48)
        canvas.drawRect(screen, paint)

        // A simple, original iOS 6-inspired home-screen placeholder, not Apple's assets.
        paint.color = Color.rgb(55, 116, 168)
        canvas.drawRect(screen.left, screen.top, screen.right, screen.top + screen.height() * .22f, paint)
        paint.color = Color.WHITE
        paint.textAlign = Paint.Align.CENTER
        paint.textSize = screen.width() * .105f
        canvas.drawText("iOS 6", screen.centerX(), screen.top + screen.height() * .13f, paint)

        val gridTop = screen.top + screen.height() * .31f
        val cell = screen.width() * .19f
        val gapX = screen.width() * .055f
        val gapY = screen.height() * .065f
        val colors = intArrayOf(
            Color.rgb(72, 167, 91), Color.rgb(55, 136, 218),
            Color.rgb(232, 170, 52), Color.rgb(180, 79, 75),
            Color.rgb(113, 91, 174), Color.rgb(71, 158, 167),
            Color.rgb(208, 91, 135), Color.rgb(115, 133, 146)
        )
        for (i in 0 until 8) {
            val row = i / 4
            val col = i % 4
            val x = screen.left + gapX + col * (cell + gapX)
            val y = gridTop + row * (cell + gapY)
            paint.color = colors[i]
            canvas.drawRoundRect(RectF(x, y, x + cell, y + cell), cell * .22f, cell * .22f, paint)
        }

        paint.color = Color.rgb(35, 42, 52)
        canvas.drawRoundRect(
            RectF(screen.left, screen.bottom - screen.height() * .16f,
                screen.right, screen.bottom), 5f, 5f, paint
        )
        paint.color = Color.rgb(15, 16, 18)
        val speaker = RectF(frame.centerX() - phoneW * .13f, frame.top + phoneH * .055f,
            frame.centerX() + phoneW * .13f, frame.top + phoneH * .068f)
        canvas.drawRoundRect(speaker, 10f, 10f, paint)
        paint.color = Color.rgb(25, 26, 28)
        canvas.drawCircle(frame.centerX(), frame.bottom - phoneH * .083f, phoneW * .055f, paint)
        paint.color = Color.rgb(104, 107, 112)
        canvas.drawCircle(frame.centerX(), frame.bottom - phoneH * .083f, phoneW * .034f, paint)
    }

    private fun dp(value: Int): Int = (value * resources.displayMetrics.density).toInt()
}
