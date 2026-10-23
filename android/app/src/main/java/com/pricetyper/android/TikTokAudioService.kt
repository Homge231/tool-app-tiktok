package com.pricetyper.android

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.content.pm.ServiceInfo
import android.media.AudioAttributes
import android.media.AudioFormat
import android.media.AudioRecord
import android.media.projection.MediaProjection
import android.media.projection.MediaProjectionManager
import android.os.Build
import android.os.IBinder
import android.os.SystemClock
import android.util.Log
import android.accessibilityservice.AccessibilityServiceInfo
import android.content.ComponentName
import android.view.accessibility.AccessibilityManager
import androidx.core.app.NotificationCompat
import com.k2fsa.sherpa.onnx.FeatureConfig
import com.k2fsa.sherpa.onnx.OfflineModelConfig
import com.k2fsa.sherpa.onnx.OfflineRecognizer
import com.k2fsa.sherpa.onnx.OfflineRecognizerConfig
import com.k2fsa.sherpa.onnx.OfflineTransducerModelConfig
import com.k2fsa.sherpa.onnx.SileroVadModelConfig
import com.k2fsa.sherpa.onnx.Vad
import com.k2fsa.sherpa.onnx.VadModelConfig
import java.util.concurrent.ArrayBlockingQueue
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger
import kotlin.math.sqrt

/** Captures only media playback from the user-selected TikTok package and keeps audio in memory. */
class TikTokAudioService : Service() {
    private data class AudioFrame(val samples: FloatArray, val generation: Int, val rms: Float)

    private val prefs by lazy { getSharedPreferences(AppProtocol.PREFS, Context.MODE_PRIVATE) }
    private val queue = ArrayBlockingQueue<AudioFrame>(32)
    private val generation = AtomicInteger(0)
    @Volatile private var running = false
    private var projection: MediaProjection? = null
    private var captureThread: Thread? = null
    private var asrThread: Thread? = null
    private var lastQueueWarningAt = 0L

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent?.action == ACTION_STOP) {
            prefs.edit().putBoolean(AppProtocol.PREF_ARMED, false).apply()
            publishStatus("Đã dừng audio và disarm.")
            stopSelf()
            return START_NOT_STICKY
        }
        if (running) return START_NOT_STICKY
        try {
            createNotificationChannel()
            val notification = makeNotification()
            if (Build.VERSION.SDK_INT >= 29) {
                startForeground(NOTIFICATION_ID, notification, ServiceInfo.FOREGROUND_SERVICE_TYPE_MEDIA_PROJECTION)
            } else {
                startForeground(NOTIFICATION_ID, notification)
            }
            startCapture(intent ?: throw IllegalArgumentException("Thiếu thông tin MediaProjection"))
        } catch (error: Exception) {
            publishStatus("Không bắt đầu được audio TikTok: ${error.message ?: error.javaClass.simpleName}")
            stopSelf()
        }
        return START_NOT_STICKY
    }

    private fun startCapture(intent: Intent) {
        val resultCode = intent.getIntExtra(AppProtocol.EXTRA_RESULT_CODE, 0)
        val data = if (Build.VERSION.SDK_INT >= 33) {
            intent.getParcelableExtra(AppProtocol.EXTRA_PROJECTION_DATA, Intent::class.java)
        } else {
            @Suppress("DEPRECATION")
            intent.getParcelableExtra(AppProtocol.EXTRA_PROJECTION_DATA)
        } ?: throw IllegalArgumentException("MediaProjection chưa được cấp")
        val packageName = intent.getStringExtra(AppProtocol.PREF_TIKTOK_PACKAGE)
            ?: prefs.getString(AppProtocol.PREF_TIKTOK_PACKAGE, AppProtocol.DEFAULT_TIKTOK_PACKAGE)
            ?: AppProtocol.DEFAULT_TIKTOK_PACKAGE
        val appInfo = packageManager.getApplicationInfo(packageName, 0)
        val manager = getSystemService(MediaProjectionManager::class.java)
        projection = manager.getMediaProjection(resultCode, data)
            ?: throw IllegalStateException("Android không tạo được MediaProjection")
        projection?.registerCallback(object : MediaProjection.Callback() {
            override fun onStop() {
                if (!running) return
                prefs.edit().putBoolean(AppProtocol.PREF_ARMED, false).apply()
                publishStatus("Android đã dừng quyền MediaProjection. Ứng dụng disarm.")
                stopSelf()
            }
        }, null)

        val captureConfig = android.media.AudioPlaybackCaptureConfiguration.Builder(projection!!)
            .addMatchingUsage(AudioAttributes.USAGE_MEDIA)
            .addMatchingUid(appInfo.uid)
            .build()
        val format = AudioFormat.Builder()
            .setEncoding(AudioFormat.ENCODING_PCM_16BIT)
            .setSampleRate(SAMPLE_RATE)
            .setChannelMask(AudioFormat.CHANNEL_IN_MONO)
            .build()
        val minimum = AudioRecord.getMinBufferSize(
            SAMPLE_RATE,
            AudioFormat.CHANNEL_IN_MONO,
            AudioFormat.ENCODING_PCM_16BIT,
        )
        if (minimum <= 0) throw IllegalStateException("AudioRecord không hỗ trợ 16 kHz mono trên thiết bị này")
        val recorder = AudioRecord.Builder()
            .setAudioFormat(format)
            .setAudioPlaybackCaptureConfig(captureConfig)
            .setBufferSizeInBytes(maxOf(minimum * 2, 4096))
            .build()
        if (recorder.state != AudioRecord.STATE_INITIALIZED) {
            recorder.release()
            throw IllegalStateException("Android không khởi tạo được playback capture cho TikTok")
        }

        running = true
        prefs.edit().putBoolean(AppProtocol.PREF_ARMED, false).putBoolean(AppProtocol.PREF_LISTENING, true).apply()
        captureThread = Thread({ captureLoop(recorder) }, "NumberTyper-Android-Audio").apply { start() }
        asrThread = Thread({ asrLoop() }, "NumberTyper-Android-ASR").apply { start() }
        publishStatus("Đang nghe audio TikTok · dry-run · disarmed. Nếu TikTok chặn capture, sẽ không có tín hiệu audio.")
    }

    private fun captureLoop(recorder: AudioRecord) {
        val input = ShortArray(1024)
        val frame = FloatArray(VAD_WINDOW)
        var frameOffset = 0
        try {
            recorder.startRecording()
            while (running) {
                val count = recorder.read(input, 0, input.size, AudioRecord.READ_BLOCKING)
                if (count < 0) throw IllegalStateException("AudioRecord.read lỗi $count")
                var cursor = 0
                while (cursor < count) {
                    val copyCount = minOf(VAD_WINDOW - frameOffset, count - cursor)
                    for (i in 0 until copyCount) {
                        val sample = input[cursor + i].toFloat() / 32768.0f
                        frame[frameOffset + i] = sample
                    }
                    frameOffset += copyCount
                    cursor += copyCount
                    if (frameOffset == VAD_WINDOW) {
                        val sum = frame.sumOf { (it * 32768.0f).toDouble() * (it * 32768.0f).toDouble() }
                        val rms = sqrt(sum / VAD_WINDOW).toFloat()
                        enqueueFrame(AudioFrame(frame.copyOf(), generation.get(), rms))
                        frameOffset = 0
                    }
                }
            }
        } catch (error: Exception) {
            if (running) {
                prefs.edit().putBoolean(AppProtocol.PREF_ARMED, false).apply()
                publishStatus("Audio TikTok bị ngắt: ${error.message ?: error.javaClass.simpleName}. Đã disarm.")
                stopSelf()
            }
        } finally {
            runCatching { recorder.stop() }
            recorder.release()
        }
    }

    private fun enqueueFrame(frame: AudioFrame) {
        if (queue.offer(frame)) return
        queue.clear()
        val nextGeneration = generation.incrementAndGet()
        prefs.edit().putBoolean(AppProtocol.PREF_ARMED, false).apply()
        val now = SystemClock.elapsedRealtime()
        if (now - lastQueueWarningAt >= 5_000L) {
            publishStatus("ASR xử lý chậm; đã bỏ audio cũ, reset nhận dạng và disarm.")
            lastQueueWarningAt = now
        }
        queue.offer(frame.copy(generation = nextGeneration))
    }

    private fun asrLoop() {
        var recognizer: OfflineRecognizer? = null
        var vad: Vad? = null
        try {
            val modelConfig = OfflineModelConfig(
                transducer = OfflineTransducerModelConfig(
                    encoder = "model/encoder.int8.onnx",
                    decoder = "model/decoder.onnx",
                    joiner = "model/joiner.int8.onnx",
                ),
                tokens = "model/tokens.txt",
                modelType = "transducer",
                modelingUnit = "cjkchar",
                numThreads = 2,
                provider = "cpu",
            )
            recognizer = OfflineRecognizer(
                assets,
                OfflineRecognizerConfig(
                    featConfig = FeatureConfig(sampleRate = SAMPLE_RATE, featureDim = 80),
                    modelConfig = modelConfig,
                ),
            )
            vad = Vad(
                assets,
                VadModelConfig(
                    sileroVadModelConfig = SileroVadModelConfig(
                        model = "model/silero_vad.onnx",
                        threshold = 0.5f,
                        minSilenceDuration = 0.25f,
                        minSpeechDuration = 0.25f,
                        windowSize = VAD_WINDOW,
                        maxSpeechDuration = 12.0f,
                    ),
                    sampleRate = SAMPLE_RATE,
                    numThreads = 1,
                    provider = "cpu",
                ),
            )
            publishStatus("Model offline đã nạp. Đang chờ audio từ TikTok.")
            var activeGeneration = generation.get()
            var suppressNextFinal = false
            var speechSince = 0L
            var lastAsrAt = SystemClock.elapsedRealtime()
            var asrStallWarned = false
            var silenceSince = SystemClock.elapsedRealtime()
            var silenceWarned = false
            while (running) {
                val frame = queue.poll(200, TimeUnit.MILLISECONDS) ?: run {
                    if (speechSince != 0L && !asrStallWarned && SystemClock.elapsedRealtime() - lastAsrAt >= ASR_STALL_MS) {
                        prefs.edit().putBoolean(AppProtocol.PREF_ARMED, false).apply()
                        publishStatus("CẢNH BÁO: VAD nghe thấy lời nói nhưng ASR chưa trả kết quả 15 giây. Đã disarm.")
                        asrStallWarned = true
                    }
                    continue
                }
                if (frame.generation != activeGeneration) {
                    vad.reset()
                    activeGeneration = frame.generation
                    suppressNextFinal = true
                    speechSince = 0L
                    lastAsrAt = SystemClock.elapsedRealtime()
                }
                if (frame.rms < 10f) {
                    if (!silenceWarned && SystemClock.elapsedRealtime() - silenceSince >= NO_SIGNAL_MS) {
                        publishStatus("Không có tín hiệu audio TikTok trong 30 giây. TikTok có thể chặn playback capture.")
                        silenceWarned = true
                    }
                } else {
                    silenceSince = SystemClock.elapsedRealtime()
                    if (silenceWarned) publishStatus("Audio TikTok đã hoạt động trở lại. Vẫn disarmed; cần arm thủ công.")
                    silenceWarned = false
                }

                vad.acceptWaveform(frame.samples)
                if (vad.isSpeechDetected() && speechSince == 0L) speechSince = SystemClock.elapsedRealtime()
                while (!vad.empty()) {
                    val segment = vad.front()
                    vad.pop()
                    val forcedLongSegment = segment.samples.size >= SAMPLE_RATE * MAX_SPEECH_SECONDS
                    val stream = recognizer.createStream()
                    try {
                        stream.acceptWaveform(segment.samples, SAMPLE_RATE)
                        recognizer.decode(stream)
                        val text = recognizer.getResult(stream).text.trim()
                        val speechDecodeTimedOut = speechSince != 0L &&
                            SystemClock.elapsedRealtime() - speechSince >= ASR_STALL_MS
                        if (speechDecodeTimedOut && !asrStallWarned) {
                            prefs.edit().putBoolean(AppProtocol.PREF_ARMED, false).apply()
                            publishStatus("CẢNH BÁO: ASR xử lý một đoạn speech quá 15 giây. Đã disarm.")
                            asrStallWarned = true
                        }
                        if (text.isNotEmpty()) {
                            lastAsrAt = SystemClock.elapsedRealtime()
                            speechSince = 0L
                            val numbers = VietnameseNumberParser.parseAll(text)
                            val candidate = numbers.lastOrNull()?.let { "@$it" }
                            val finalAllowed = !suppressNextFinal && !forcedLongSegment
                            suppressNextFinal = forcedLongSegment
                            publishRecognition(text, candidate)
                            if (asrStallWarned) {
                                asrStallWarned = false
                                publishStatus("ASR đã trả kết quả trở lại. Vẫn disarmed; cần arm thủ công.")
                            }
                            if (forcedLongSegment) publishStatus("Đoạn speech vượt 12 giây; chỉ preview, không gửi.")
                            if (candidate != null && finalAllowed && canDispatch()) dispatchCandidate(candidate)
                            updateNotification(candidate)
                        }
                        if (forcedLongSegment) {
                            vad.reset()
                            suppressNextFinal = true
                            publishStatus("Đoạn speech vượt 12 giây; chỉ preview, không gửi.")
                        }
                    } finally {
                        runCatching { stream.release() }
                    }
                }
            }
        } catch (error: Exception) {
            if (running) {
                prefs.edit().putBoolean(AppProtocol.PREF_ARMED, false).apply()
                publishStatus("Khởi tạo/nhận dạng ASR lỗi: ${error.message ?: error.javaClass.simpleName}. Đã disarm.")
                Log.e(TAG, "Android ASR failed", error)
                stopSelf()
            }
        } finally {
            runCatching { vad?.release() }
            runCatching { recognizer?.release() }
        }
    }

    private fun canDispatch(): Boolean {
        if (!running || !prefs.getBoolean(AppProtocol.PREF_LISTENING, false) ||
            !prefs.getBoolean(AppProtocol.PREF_ARMED, false) || prefs.getBoolean(AppProtocol.PREF_DRY_RUN, true)
        ) return false
        val manager = getSystemService(AccessibilityManager::class.java)
        val serviceComponent = ComponentName(this, TikTokAccessibilityService::class.java)
        val enabled = manager.getEnabledAccessibilityServiceList(AccessibilityServiceInfo.FEEDBACK_ALL_MASK)
            .any { ComponentName.unflattenFromString(it.id) == serviceComponent }
        if (!enabled) {
            prefs.edit().putBoolean(AppProtocol.PREF_ARMED, false).apply()
            publishStatus("AccessibilityService đã tắt. App đã disarm; bật lại và arm thủ công.")
            return false
        }
        return true
    }

    private fun dispatchCandidate(candidate: String) {
        sendBroadcast(
            Intent(AppProtocol.ACTION_SEND_CANDIDATE)
                .setPackage(packageName)
                .putExtra(AppProtocol.EXTRA_CANDIDATE, candidate)
                .putExtra(AppProtocol.PREF_SUBMIT, prefs.getBoolean(AppProtocol.PREF_SUBMIT, true))
                .putExtra(AppProtocol.PREF_TIKTOK_PACKAGE, prefs.getString(AppProtocol.PREF_TIKTOK_PACKAGE, AppProtocol.DEFAULT_TIKTOK_PACKAGE)),
        )
    }

    private fun publishRecognition(text: String, candidate: String?) {
        val intent = Intent(AppProtocol.ACTION_STATUS)
            .setPackage(packageName)
            .putExtra(AppProtocol.EXTRA_TEXT, text)
        if (candidate != null) intent.putExtra(AppProtocol.EXTRA_CANDIDATE, candidate)
        sendBroadcast(intent)
        // Do not persist transcript or captured audio.
    }

    private fun publishStatus(message: String) {
        prefs.edit().putString(AppProtocol.EXTRA_STATUS, message).apply()
        sendBroadcast(Intent(AppProtocol.ACTION_STATUS).setPackage(packageName).putExtra(AppProtocol.EXTRA_STATUS, message))
    }

    private fun updateNotification(candidate: String?) {
        val content = if (candidate == null) "Đang nghe TikTok · audio xử lý cục bộ" else "Số nhận dạng: $candidate"
        getSystemService(NotificationManager::class.java).notify(NOTIFICATION_ID, makeNotification(content))
    }

    private fun makeNotification(content: String = "Audio xử lý cục bộ · mặc định disarmed"): Notification {
        val stopIntent = Intent(this, TikTokAudioService::class.java).setAction(ACTION_STOP)
        val stopPending = PendingIntent.getService(
            this,
            2,
            stopIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )
        val openIntent = PendingIntent.getActivity(
            this,
            1,
            Intent(this, MainActivity::class.java),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setSmallIcon(android.R.drawable.ic_btn_speak_now)
            .setContentTitle("NumberTyper đang nghe TikTok")
            .setContentText(content)
            .setContentIntent(openIntent)
            .setOngoing(true)
            .addAction(android.R.drawable.ic_media_pause, "Dừng khẩn", stopPending)
            .build()
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= 26) {
            val manager = getSystemService(NotificationManager::class.java)
            manager.createNotificationChannel(NotificationChannel(CHANNEL_ID, "NumberTyper audio", NotificationManager.IMPORTANCE_LOW))
        }
    }

    override fun onDestroy() {
        running = false
        prefs.edit().putBoolean(AppProtocol.PREF_ARMED, false).putBoolean(AppProtocol.PREF_LISTENING, false).apply()
        projection?.stop()
        captureThread?.interrupt()
        asrThread?.interrupt()
        queue.clear()
        stopForeground(STOP_FOREGROUND_REMOVE)
        super.onDestroy()
    }

    companion object {
        const val ACTION_STOP = "com.pricetyper.android.STOP_CAPTURE"
        private const val CHANNEL_ID = "numbertyper_audio"
        private const val NOTIFICATION_ID = 701
        private const val TAG = "NumberTyperAndroid"
        private const val SAMPLE_RATE = 16000
        private const val VAD_WINDOW = 512
        private const val MAX_SPEECH_SECONDS = 12
        private const val NO_SIGNAL_MS = 30_000L
        private const val ASR_STALL_MS = 15_000L
    }
}
