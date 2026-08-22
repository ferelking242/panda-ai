package com.pandaai.gateway

import android.annotation.SuppressLint
import android.content.Context
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import android.os.Bundle
import android.view.View
import android.view.inputmethod.InputMethodManager
import android.webkit.*
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import com.pandaai.gateway.databinding.ActivityMainBinding
import kotlinx.coroutines.*
import java.net.HttpURLConnection
import java.net.URL

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private var gatewayUrl: String = "http://localhost:8000"
    private var isConnected: Boolean = false
    private var healthCheckJob: Job? = null

    companion object {
        private const val PREFS_NAME = "panda_ai_prefs"
        private const val KEY_GATEWAY_URL = "gateway_url"
        private const val HEALTH_CHECK_INTERVAL_MS = 5000L
        private const val CONNECT_TIMEOUT_MS = 3000
    }

    // ── Lifecycle ──────────────────────────────────────────────

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        // Load saved URL
        val prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        gatewayUrl = prefs.getString(KEY_GATEWAY_URL, gatewayUrl) ?: gatewayUrl

        setupWebView()
        setupUI()

        // Start health check
        startHealthCheck()
    }

    override fun onResume() {
        super.onResume()
        if (!isConnected) startHealthCheck()
    }

    override fun onPause() {
        super.onPause()
        healthCheckJob?.cancel()
    }

    override fun onDestroy() {
        super.onDestroy()
        binding.webview.destroy()
    }

    // ── WebView Setup ──────────────────────────────────────────

    @SuppressLint("SetJavaScriptEnabled")
    private fun setupWebView() {
        binding.webview.apply {
            settings.javaScriptEnabled = true
            settings.domStorageEnabled = true
            settings.allowFileAccess = true
            settings.allowContentAccess = true
            settings.mediaPlaybackRequiresUserGesture = false
            settings.mixedContentMode = WebSettings.MIXED_CONTENT_ALWAYS_ALLOW

            // Desktop user agent to get the full dashboard
            settings.userAgentString = settings.userAgentString
                .replace(Regex("Android\\s[\\d.]+"), "")

            webViewClient = object : WebViewClient() {
                override fun onReceivedError(
                    view: WebView?,
                    request: WebResourceRequest?,
                    error: WebResourceError?
                ) {
                    if (request?.isForMainFrame == true) {
                        runOnUiThread {
                            showSplash("Connection failed. Retrying...")
                            binding.webview.visibility = View.GONE
                            binding.splashOverlay.visibility = View.VISIBLE
                        }
                        isConnected = false
                    }
                }

                override fun onReceivedHttpError(
                    view: WebView?,
                    request: WebResourceRequest?,
                    errorResponse: WebResourceResponse?
                ) {
                    if (request?.isForMainFrame == true && errorResponse?.statusCode == 401) {
                        runOnUiThread {
                            Toast.makeText(
                                this@MainActivity,
                                "Authentication required — set API_TOKEN in .env",
                                Toast.LENGTH_LONG
                            ).show()
                        }
                    }
                }

                override fun onPageFinished(view: WebView?, url: String?) {
                    super.onPageFinished(view, url)
                    isConnected = true
                    runOnUiThread {
                        binding.webview.visibility = View.VISIBLE
                        binding.splashOverlay.visibility = View.GONE
                    }
                }
            }

            webChromeClient = object : WebChromeClient() {
                override fun onConsoleMessage(msg: ConsoleMessage?): Boolean {
                    return true // Suppress console noise
                }
            }

            // Inject JavaScript bridge
            addJavascriptInterface(WebBridge(this@MainActivity), "AndroidBridge")
        }
    }

    // ── UI Setup ───────────────────────────────────────────────

    private fun setupUI() {
        binding.urlInput.setText(gatewayUrl)

        binding.connectButton.setOnClickListener {
            val url = binding.urlInput.text.toString().trim()
            if (url.isBlank()) {
                Toast.makeText(this, "Enter a gateway URL", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }

            // Save URL
            gatewayUrl = url.trimEnd('/')
            getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
                .edit()
                .putString(KEY_GATEWAY_URL, gatewayUrl)
                .apply()

            // Hide keyboard
            val imm = getSystemService(INPUT_METHOD_SERVICE) as InputMethodManager
            imm.hideSoftInputFromWindow(binding.urlInput.windowToken, 0)

            // Try connecting
            showSplash("Connecting to $gatewayUrl...")
            tryConnect()
        }
    }

    // ── Health Check ───────────────────────────────────────────

    private fun startHealthCheck() {
        healthCheckJob?.cancel()
        healthCheckJob = lifecycleScope.launch {
            while (isActive) {
                val wasConnected = isConnected
                isConnected = checkHealth()

                withContext(Dispatchers.Main) {
                    if (isConnected && !wasConnected) {
                        // Just connected — load dashboard
                        loadDashboard()
                    } else if (!isConnected && wasConnected) {
                        // Just disconnected — show splash
                        showSplash("Gateway disconnected. Retrying...")
                        binding.webview.visibility = View.GONE
                        binding.splashOverlay.visibility = View.VISIBLE
                        binding.urlInputLayout.visibility = View.VISIBLE
                        binding.connectButton.visibility = View.VISIBLE
                    } else if (!isConnected) {
                        // Still not connected
                        showSplash("Connecting to gateway...")
                        binding.urlInputLayout.visibility = View.VISIBLE
                        binding.connectButton.visibility = View.VISIBLE
                    }
                }

                delay(HEALTH_CHECK_INTERVAL_MS)
            }
        }
    }

    private fun checkHealth(): Boolean {
        return try {
            val conn = URL("$gatewayUrl/healthz").openConnection() as HttpURLConnection
            conn.connectTimeout = CONNECT_TIMEOUT_MS
            conn.readTimeout = CONNECT_TIMEOUT_MS
            conn.requestMethod = "GET"
            val code = conn.responseCode
            conn.disconnect()
            code == 200
        } catch (e: Exception) {
            false
        }
    }

    // ── Navigation ─────────────────────────────────────────────

    private fun loadDashboard() {
        binding.webview.loadUrl("$gatewayUrl/client")
    }

    private fun tryConnect() {
        lifecycleScope.launch {
            val ok = withContext(Dispatchers.IO) { checkHealth() }
            if (ok) {
                loadDashboard()
            } else {
                showSplash("Cannot reach gateway at $gatewayUrl")
                binding.urlInputLayout.visibility = View.VISIBLE
                binding.connectButton.visibility = View.VISIBLE
            }
        }
    }

    private fun showSplash(message: String) {
        binding.statusText.text = message
        binding.splashOverlay.visibility = View.VISIBLE
    }

    // ── Public accessors for WebBridge ─────────────────────────

    fun getGatewayUrl(): String = gatewayUrl

    fun setGatewayUrl(url: String) {
        gatewayUrl = url.trimEnd('/')
        getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            .edit()
            .putString(KEY_GATEWAY_URL, gatewayUrl)
            .apply()
    }

    fun isGatewayConnected(): Boolean = isConnected

    // ── Back button ────────────────────────────────────────────

    @Deprecated("Deprecated in Java")
    override fun onBackPressed() {
        if (binding.webview.canGoBack()) {
            binding.webview.goBack()
        } else {
            @Suppress("DEPRECATION")
            super.onBackPressed()
        }
    }
}
