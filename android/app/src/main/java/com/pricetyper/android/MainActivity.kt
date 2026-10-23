package com.pricetyper.android

import android.Manifest
import android.accessibilityservice.AccessibilityServiceInfo
import android.app.Activity
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.media.projection.MediaProjectionManager
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.view.accessibility.AccessibilityManager
import android.widget.Button
import android.widget.CheckBox
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.ComponentActivity
import androidx.core.content.ContextCompat

class MainActivity : ComponentActivity() {
    private val prefs by lazy { getSharedPreferences(AppProtocol.PREFS, Context.MODE_PRIVATE) }
    private lateinit var dryRun: CheckBox
    private lateinit var submitWithEnter: CheckBox
    private lateinit var armButton: Button
    private lateinit var statusView: TextView
    private lateinit var transcriptView: TextView
    private lateinit var candidateView: TextView
    private var pendingStart = false

    private val projectionLauncher = registerForActivityResult(ActivityResultContracts.StartActivityForResult()) { result ->
        if (result.resultCode == Activity.RESULT_OK && result.data != null) {
            val service = Intent(this, TikTokAudioService::class.java)
                .putExtra(AppProtocol.EXTRA_RESULT_CODE, result.resultCode)
                .putExtra(AppProtocol.EXTRA_PROJECTION_DATA, result.data)
                .putExtra(AppProtocol.PREF_TIKTOK_PACKAGE, currentPackage())
            ContextCompat.startForegroundService(this, service)
            setStatus("Đang khởi tạo thu audio TikTok…")
        } else {
            setStatus("Bạn đã từ chối quyền thu audio. App chưa bắt đầu.")
        }
    }

    private val audioPermissionLauncher = registerForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        if (granted && pendingStart) {
            pendingStart = false
            requestProjection()
        } else {
            pendingStart = false
            setStatus("Cần quyền RECORD_AUDIO để Android cho phép thu playback audio.")
        }
    }

    private val statusReceiver = object : android.content.BroadcastReceiver() {
        override fun onReceive(context: Context?, intent: Intent?) {
            intent ?: return
            intent.getStringExtra(AppProtocol.EXTRA_STATUS)?.let(::setStatus)
            intent.getStringExtra(AppProtocol.EXTRA_TEXT)?.let { transcriptView.text = "Nghe được: $it" }
            if (intent.hasExtra(AppProtocol.EXTRA_TEXT)) {
                candidateView.text = "Số trích được: ${intent.getStringExtra(AppProtocol.EXTRA_CANDIDATE) ?: "—"}"
            }
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        prefs.edit().putBoolean(AppProtocol.PREF_ARMED, false).putBoolean(AppProtocol.PREF_DRY_RUN, true).apply()
        buildUi()
        dryRun.isChecked = true
        submitWithEnter.isChecked = prefs.getBoolean(AppProtocol.PREF_SUBMIT, true)
        updateArmButton()
        if (Build.VERSION.SDK_INT >= 33 && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != android.content.pm.PackageManager.PERMISSION_GRANTED) {
            requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS), 101)
        }
        registerStatusReceiver()
        if (intent?.action == ACTION_STOP) stopCapture()
    }

    override fun onResume() {
        super.onResume()
        prefs.getString(AppProtocol.EXTRA_STATUS, null)?.let(::setStatus)
        updateArmButton()
    }

    override fun onDestroy() {
        runCatching { unregisterReceiver(statusReceiver) }
        super.onDestroy()
    }

    private fun buildUi() {
        val page = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(20), dp(20), dp(20), dp(28))
            setBackgroundColor(0xFFF6F7F9.toInt())
        }
        fun label(text: String, size: Float = 16f, bold: Boolean = false): TextView = TextView(this).apply {
            this.text = text
            textSize = size
            if (bold) setTypeface(typeface, android.graphics.Typeface.BOLD)
            setTextColor(0xFF202124.toInt())
            setPadding(0, dp(7), 0, dp(7))
        }
        fun button(text: String, action: () -> Unit): Button = Button(this).apply {
            this.text = text
            setOnClickListener { action() }
            isAllCaps = false
        }

        page.addView(label("NumberTyper Android", 25f, true))
        page.addView(label("TikTok Live · nhận dạng tiếng Việt trên điện thoại", 15f))

        statusView = label("Sẵn sàng · mặc định dry-run và disarmed", 14f)
        statusView.setTextColor(0xFF6B2E00.toInt())
        page.addView(statusView)

        page.addView(label("Gói TikTok Android: ${AppProtocol.DEFAULT_TIKTOK_PACKAGE}", 14f, true))

        page.addView(button("Bắt đầu nghe audio TikTok", ::beginCapture))
        page.addView(button("Dừng khẩn (disarm + dừng nghe)", ::stopCapture))
        page.addView(button("Mở TikTok", ::openTikTok))

        dryRun = CheckBox(this).apply {
            text = "Chạy thử — không nhập/gửi comment thật"
            setTextColor(0xFF202124.toInt())
            setOnCheckedChangeListener { _, checked ->
                prefs.edit().putBoolean(AppProtocol.PREF_DRY_RUN, checked).apply()
                prefs.edit().putBoolean(AppProtocol.PREF_ARMED, false).apply()
                updateArmButton()
            }
        }
        page.addView(dryRun)

        submitWithEnter = CheckBox(this).apply {
            text = "Nhấn Enter sau khi điền @số"
            setTextColor(0xFF202124.toInt())
            setOnCheckedChangeListener { _, checked -> prefs.edit().putBoolean(AppProtocol.PREF_SUBMIT, checked).apply() }
        }
        page.addView(submitWithEnter)

        armButton = button("Arm thao tác", ::toggleArm)
        page.addView(armButton)
        page.addView(button("Bật quyền trợ năng để nhập TikTok", ::openAccessibilitySettings))

        page.addView(label("Trạng thái nhận dạng", 17f, true))
        transcriptView = label("Nghe được: —", 15f)
        page.addView(transcriptView)
        candidateView = label("Số trích được: —", 18f, true)
        page.addView(candidateView)
        page.addView(label("Mở TikTok Live trước. Android sẽ hỏi quyền MediaProjection. Nếu TikTok chặn playback capture, ứng dụng báo không có tín hiệu và sẽ không tự chuyển sang microphone.", 13f))
        page.addView(label("Khi bật thao tác thật, NumberTyper chỉ dùng ô nhập TikTok đang focus. Hãy để ô trống; việc nhấn Enter là yêu cầu chưa được xác nhận TikTok đã hiển thị comment.", 13f))

        val scroll = ScrollView(this).apply { addView(page) }
        setContentView(scroll)
    }

    private fun beginCapture() {
        if (prefs.getBoolean(AppProtocol.PREF_LISTENING, false)) {
            setStatus("Audio đã chạy. Dừng trước khi bắt đầu phiên mới.")
            return
        }
        val packageName = currentPackage()
        prefs.edit().putString(AppProtocol.PREF_TIKTOK_PACKAGE, packageName)
            .putBoolean(AppProtocol.PREF_ARMED, false)
            .putBoolean(AppProtocol.PREF_DRY_RUN, true)
            .apply()
        dryRun.isChecked = true
        if (!isPackageInstalled(packageName)) {
            setStatus("Không tìm thấy ứng dụng $packageName. Kiểm tra package ID TikTok trên điện thoại.")
            return
        }
        val modelFiles = assets.list("model")?.toSet().orEmpty()
        if (!modelFiles.containsAll(setOf("silero_vad.onnx", "encoder.int8.onnx", "decoder.onnx", "joiner.int8.onnx", "tokens.txt"))) {
            setStatus("Thiếu model offline trong APK. Build lại khi thư mục models/ của repo có Zipformer-VI và Silero VAD.")
            return
        }
        if (checkSelfPermission(Manifest.permission.RECORD_AUDIO) != android.content.pm.PackageManager.PERMISSION_GRANTED) {
            pendingStart = true
            audioPermissionLauncher.launch(Manifest.permission.RECORD_AUDIO)
            return
        }
        requestProjection()
    }

    private fun requestProjection() {
        val manager = getSystemService(MediaProjectionManager::class.java)
        projectionLauncher.launch(manager.createScreenCaptureIntent())
    }

    private fun stopCapture() {
        prefs.edit().putBoolean(AppProtocol.PREF_ARMED, false)
            .putBoolean(AppProtocol.PREF_DRY_RUN, true)
            .putBoolean(AppProtocol.PREF_LISTENING, false)
            .apply()
        dryRun.isChecked = true
        stopService(Intent(this, TikTokAudioService::class.java))
        setStatus("Đã dừng và disarm.")
        updateArmButton()
    }

    private fun toggleArm() {
        val armed = prefs.getBoolean(AppProtocol.PREF_ARMED, false)
        val next = !armed
        if (next && !prefs.getBoolean(AppProtocol.PREF_LISTENING, false)) {
            setStatus("Bắt đầu nghe TikTok trước khi arm.")
            return
        }
        if (next && !dryRun.isChecked && !isAccessibilityEnabled()) {
            setStatus("Bật NumberTyper phone typing trong cài đặt Trợ năng trước khi arm.")
            return
        }
        prefs.edit().putBoolean(AppProtocol.PREF_ARMED, next).apply()
        setStatus(if (next) "ARMED · thao tác chỉ khi TikTok đang mở và ô chat được focus." else "LISTENING · disarmed.")
        updateArmButton()
    }

    private fun openTikTok() {
        val launch = packageManager.getLaunchIntentForPackage(currentPackage())
        if (launch == null) setStatus("Không mở được TikTok với package ID hiện tại.") else startActivity(launch)
    }

    private fun openAccessibilitySettings() {
        startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
    }

    private fun currentPackage(): String = AppProtocol.DEFAULT_TIKTOK_PACKAGE

    private fun isPackageInstalled(name: String): Boolean = try {
        packageManager.getApplicationInfo(name, 0)
        true
    } catch (_: Exception) {
        false
    }

    private fun isAccessibilityEnabled(): Boolean {
        val manager = getSystemService(ACCESSIBILITY_SERVICE) as AccessibilityManager
        val expected = ComponentName(this, TikTokAccessibilityService::class.java)
        return manager.getEnabledAccessibilityServiceList(AccessibilityServiceInfo.FEEDBACK_ALL_MASK)
            .any { ComponentName.unflattenFromString(it.id) == expected }
    }

    private fun updateArmButton() {
        if (!::armButton.isInitialized) return
        val armed = prefs.getBoolean(AppProtocol.PREF_ARMED, false)
        armButton.text = if (armed) "Disarm" else "Arm thao tác"
        armButton.setBackgroundColor(if (armed) 0xFFFFD8D3.toInt() else 0xFFDAE8FF.toInt())
    }

    private fun setStatus(text: String) {
        if (::statusView.isInitialized) statusView.text = text
        prefs.edit().putString(AppProtocol.EXTRA_STATUS, text).apply()
    }

    private fun registerStatusReceiver() {
        val filter = IntentFilter(AppProtocol.ACTION_STATUS)
        if (Build.VERSION.SDK_INT >= 33) registerReceiver(statusReceiver, filter, Context.RECEIVER_NOT_EXPORTED)
        else @Suppress("DEPRECATION") registerReceiver(statusReceiver, filter)
    }

    private fun dp(value: Int): Int = (value * resources.displayMetrics.density).toInt()
    companion object {
        const val ACTION_STOP = "com.pricetyper.android.STOP_FROM_NOTIFICATION"
    }
}
