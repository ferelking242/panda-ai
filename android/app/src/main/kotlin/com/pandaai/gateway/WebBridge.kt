package com.pandaai.gateway

import android.webkit.JavascriptInterface

/**
 * JavaScript bridge injected into the WebView.
 * Allows the gateway's web dashboard to call native Android functions.
 */
class WebBridge(private val activity: MainActivity) {

    @JavascriptInterface
    fun getGatewayUrl(): String = activity.getGatewayUrl()

    @JavascriptInterface
    fun setGatewayUrl(url: String) {
        activity.setGatewayUrl(url)
    }

    @JavascriptInterface
    fun isConnected(): Boolean = activity.isGatewayConnected()

    @JavascriptInterface
    fun vibrate(durationMs: Int) {
        activity.runOnUiThread {
            @Suppress("DEPRECATION")
            val vibrator = activity.getSystemService(android.content.Context.VIBRATOR_SERVICE)
                    as? android.os.Vibrator
            vibrator?.vibrate(android.os.VibrationEffect.createOneShot(
                durationMs.toLong(), android.os.VibrationEffect.DEFAULT_AMPLITUDE
            ))
        }
    }
}
