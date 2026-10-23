package com.pricetyper.android

import android.accessibilityservice.AccessibilityService
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.Build
import android.os.Bundle
import android.os.SystemClock
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo
import java.util.ArrayDeque

/**
 * Types only into TikTok's currently focused editable field. It never reads node text,
 * chat rows, comments, event text, credentials, or cookies.
 */
class TikTokAccessibilityService : AccessibilityService() {
    private val prefs by lazy { getSharedPreferences(AppProtocol.PREFS, Context.MODE_PRIVATE) }
    private val sent = ArrayDeque<Pair<Long, String>>()

    private val candidateReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context?, intent: Intent?) {
            val candidate = intent?.getStringExtra(AppProtocol.EXTRA_CANDIDATE) ?: return
            val target = intent.getStringExtra(AppProtocol.PREF_TIKTOK_PACKAGE)
                ?: prefs.getString(AppProtocol.PREF_TIKTOK_PACKAGE, AppProtocol.DEFAULT_TIKTOK_PACKAGE)
                ?: AppProtocol.DEFAULT_TIKTOK_PACKAGE
            val submit = intent.getBooleanExtra(AppProtocol.PREF_SUBMIT, true)
            sendOnce(candidate, target, submit)
        }
    }

    override fun onServiceConnected() {
        super.onServiceConnected()
        val filter = IntentFilter(AppProtocol.ACTION_SEND_CANDIDATE)
        if (Build.VERSION.SDK_INT >= 33) registerReceiver(candidateReceiver, filter, Context.RECEIVER_NOT_EXPORTED)
        else @Suppress("DEPRECATION") registerReceiver(candidateReceiver, filter)
        publish("Quyền nhập TikTok đã sẵn sàng. App vẫn disarmed.")
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        // Android events are not inspected; the sender checks the active app window at action time.
    }

    override fun onInterrupt() = Unit

    override fun onDestroy() {
        runCatching { unregisterReceiver(candidateReceiver) }
        super.onDestroy()
    }

    private fun sendOnce(candidate: String, target: String, submit: Boolean) {
        if (!prefs.getBoolean(AppProtocol.PREF_LISTENING, false) ||
            !prefs.getBoolean(AppProtocol.PREF_ARMED, false) ||
            prefs.getBoolean(AppProtocol.PREF_DRY_RUN, true)
        ) return
        if (!candidate.matches(Regex("@[0-9]{1,15}"))) {
            disarm("Candidate không phải @ + số ASCII. Đã disarm.")
            return
        }
        val now = SystemClock.elapsedRealtime()
        while (sent.isNotEmpty() && now - sent.first().first >= 60_000L) sent.removeFirst()
        if (sent.any { it.second == candidate && now - it.first < 10_000L }) {
            publish("Bỏ qua $candidate · cooldown cùng số.")
            return
        }
        if (sent.isNotEmpty() && now - sent.last().first < 1_500L) {
            publish("Bỏ qua $candidate · cooldown.")
            return
        }
        if (sent.size >= 10) {
            publish("Bỏ qua $candidate · đạt giới hạn 10 thao tác/phút.")
            return
        }

        val root = rootInActiveWindow?.takeIf { it.packageName?.toString() == target }
            ?: windows.asSequence()
                .filter { it.type == android.view.accessibility.AccessibilityWindowInfo.TYPE_APPLICATION && it.isActive }
                .mapNotNull { it.root }
                .firstOrNull { it.packageName?.toString() == target }
        if (root == null || root.packageName?.toString() != target) {
            disarm("Không có cửa sổ TikTok đang hoạt động. Không thao tác; đã disarm.")
            return
        }
        val focused = root.findFocus(AccessibilityNodeInfo.FOCUS_INPUT)
        if (focused == null || !focused.isEditable || !focused.isFocused) {
            disarm("Không thấy ô nhập TikTok đang focus. Không thao tác; đã disarm.")
            return
        }

        // ACTION_SET_TEXT replaces the focused draft. User must keep the chat field empty.
        val args = Bundle().apply {
            putCharSequence(AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE, candidate)
        }
        val filled = try {
            focused.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT, args)
        } catch (_: Exception) {
            false
        }
        if (!filled) {
            disarm("TikTok không chấp nhận thao tác điền. Không thử lại; đã disarm.")
            return
        }
        sent.addLast(now to candidate)

        if (!submit) {
            publish("Đã yêu cầu điền $candidate vào ô focus · comment chưa gửi.")
            return
        }
        val enterSent = try {
            focused.performAction(AccessibilityNodeInfo.AccessibilityAction.ACTION_IME_ENTER.id)
        } catch (_: Exception) {
            false
        }
        if (enterSent) {
            publish("Đã phát yêu cầu Enter cho $candidate · chưa xác minh TikTok hiển thị comment.")
        } else {
            disarm("Đã điền $candidate nhưng TikTok không nhận yêu cầu Enter · không thử lại; đã disarm.")
        }
    }

    private fun disarm(message: String) {
        prefs.edit().putBoolean(AppProtocol.PREF_ARMED, false).apply()
        publish(message)
    }

    private fun publish(message: String) {
        prefs.edit().putString(AppProtocol.EXTRA_STATUS, message).apply()
        sendBroadcast(Intent(AppProtocol.ACTION_STATUS).setPackage(packageName).putExtra(AppProtocol.EXTRA_STATUS, message))
    }
}
