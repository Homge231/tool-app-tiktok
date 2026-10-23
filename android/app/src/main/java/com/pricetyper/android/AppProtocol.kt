package com.pricetyper.android

internal object AppProtocol {
    const val PREFS = "numbertyper"
    const val PREF_DRY_RUN = "dry_run"
    const val PREF_ARMED = "armed"
    const val PREF_SUBMIT = "submit_with_enter"
    const val PREF_TIKTOK_PACKAGE = "tiktok_package"
    const val PREF_LISTENING = "listening"

    const val DEFAULT_TIKTOK_PACKAGE = "com.zhiliaoapp.musically"
    const val ACTION_STATUS = "com.pricetyper.android.STATUS"
    const val ACTION_SEND_CANDIDATE = "com.pricetyper.android.SEND_CANDIDATE"
    const val EXTRA_STATUS = "status"
    const val EXTRA_TEXT = "text"
    const val EXTRA_CANDIDATE = "candidate"
    const val EXTRA_RESULT = "result"
    const val EXTRA_RESULT_CODE = "result_code"
    const val EXTRA_PROJECTION_DATA = "projection_data"
}
