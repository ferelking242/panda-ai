package com.pandaai.gateway

import android.annotation.SuppressLint
import android.os.Bundle
import android.webkit.*
import androidx.appcompat.app.AppCompatActivity
import android.view.View
import android.widget.*

class MainActivity : AppCompatActivity() {
    private lateinit var webView: WebView
    private lateinit var urlInput: EditText
    private lateinit var connectBtn: Button
    private lateinit var statusText: TextView
    private lateinit var container: FrameLayout

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        webView = findViewById(R.id.webView)
        urlInput = findViewById(R.id.urlInput)
        connectBtn = findViewById(R.id.connectBtn)
        statusText = findViewById(R.id.statusText)
        container = findViewById(R.id.container)

        webView.settings.javaScriptEnabled = true
        webView.settings.domStorageEnabled = true
        webView.settings.allowFileAccess = true
        webView.settings.mixedContentMode = WebSettings.MIXED_CONTENT_ALWAYS_ALLOW

        webView.webViewClient = object : WebViewClient() {
            override fun onPageFinished(view: WebView?, url: String?) {
                statusText.text = "● Connected"
                statusText.setTextColor(0xFF22C55E.toInt())
            }

            override fun onReceivedError(view: WebView?, request: WebResourceRequest?, error: WebResourceError?) {
                statusText.text = "● Error"
                statusText.setTextColor(0xFFEF4444.toInt())
            }
        }

        connectBtn.setOnClickListener {
            val url = urlInput.text.toString().trim()
            if (url.isNotEmpty()) {
                statusText.text = "● Connecting..."
                statusText.setTextColor(0xFFFFA500.toInt())
                container.visibility = View.VISIBLE
                webView.loadUrl("$url/app")
            }
        }
    }

    override fun onBackPressed() {
        if (webView.canGoBack()) webView.goBack()
        else super.onBackPressed()
    }
}
