package com.pandaai.gateway

import android.annotation.SuppressLint
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.webkit.*
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.net.HttpURLConnection
import java.net.URL

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            PandaAITheme {
                GatewayScreen()
            }
        }
    }
}

@SuppressLint("SetJavaScriptEnabled")
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun GatewayScreen() {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()

    var serverUrl by remember { mutableStateOf("http://localhost:8000") }
    var isBackendRunning by remember { mutableStateOf(false) }
    var isChecking by remember { mutableStateOf(true) }
    var showWebView by remember { mutableStateOf(false) }
    var currentView by remember { mutableStateOf("home") } // home, dashboard, chat

    // Auto-detect backend on startup
    LaunchedEffect(Unit) {
        scope.launch(Dispatchers.IO) {
            val running = checkBackend(serverUrl)
            isBackendRunning = running
            isChecking = false
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text("🐼 ", fontSize = 20.sp)
                        Text("Panda AI", color = Color.White, fontWeight = FontWeight.Bold)
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = Color(0xFF0f172a)
                ),
                actions = {
                    // Status indicator
                    val statusColor = when {
                        isChecking -> Color(0xFFFFA500)
                        isBackendRunning -> Color(0xFF22c55e)
                        else -> Color(0xFFef4444)
                    }
                    val statusText = when {
                        isChecking -> "Checking..."
                        isBackendRunning -> "Online"
                        else -> "Offline"
                    }
                    Text(
                        "● $statusText",
                        color = statusColor,
                        fontSize = 12.sp,
                        modifier = Modifier.padding(end = 12.dp)
                    )
                }
            )
        },
        containerColor = Color(0xFF0d1117)
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            if (!showWebView) {
                // ── Home screen ───────────────────────────────
                Text(
                    "Panda AI Gateway",
                    fontSize = 28.sp,
                    fontWeight = FontWeight.Bold,
                    color = Color(0xFF00d4ff)
                )
                Text(
                    "Turn any AI account into an API",
                    fontSize = 14.sp,
                    color = Color(0xFF888888)
                )

                Spacer(modifier = Modifier.height(8.dp))

                // Server URL input
                OutlinedTextField(
                    value = serverUrl,
                    onValueChange = { serverUrl = it },
                    label = { Text("Gateway URL") },
                    modifier = Modifier.fillMaxWidth(),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedTextColor = Color.White,
                        unfocusedTextColor = Color.White,
                        focusedBorderColor = Color(0xFF00d4ff),
                        unfocusedBorderColor = Color(0xFF333333)
                    ),
                    singleLine = true
                )

                // Check connection button
                OutlinedButton(
                    onClick = {
                        isChecking = true
                        scope.launch(Dispatchers.IO) {
                            val running = checkBackend(serverUrl)
                            isBackendRunning = running
                            isChecking = false
                        }
                    },
                    modifier = Modifier.fillMaxWidth(),
                    colors = OutlinedButtonDefaults.outlinedButtonColors(
                        contentColor = Color(0xFF00d4ff)
                    )
                ) {
                    Text(if (isChecking) "Checking..." else "Test Connection")
                }

                Spacer(modifier = Modifier.height(8.dp))

                // Action buttons
                Button(
                    onClick = {
                        currentView = "dashboard"
                        showWebView = true
                    },
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF00d4ff)),
                    modifier = Modifier.fillMaxWidth(),
                    enabled = isBackendRunning
                ) {
                    Text("📊 Dashboard", color = Color(0xFF0d1117), fontWeight = FontWeight.Bold)
                }

                Button(
                    onClick = {
                        currentView = "chat"
                        showWebView = true
                    },
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF7b2ff7)),
                    modifier = Modifier.fillMaxWidth(),
                    enabled = isBackendRunning
                ) {
                    Text("💬 Test Client", color = Color.White, fontWeight = FontWeight.Bold)
                }

                Button(
                    onClick = {
                        currentView = "docs"
                        showWebView = true
                    },
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF16a34a)),
                    modifier = Modifier.fillMaxWidth(),
                    enabled = isBackendRunning
                ) {
                    Text("📖 API Docs", color = Color.White, fontWeight = FontWeight.Bold)
                }

                Spacer(modifier = Modifier.height(16.dp))

                // Termux helper
                if (!isBackendRunning) {
                    Card(
                        colors = CardDefaults.cardColors(containerColor = Color(0xFF1a1a2e)),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Column(modifier = Modifier.padding(16.dp)) {
                            Text(
                                "📱 Run locally with Termux",
                                color = Color(0xFF00d4ff),
                                fontWeight = FontWeight.Bold,
                                fontSize = 14.sp
                            )
                            Spacer(modifier = Modifier.height(8.dp))
                            Text(
                                "1. Install Termux from F-Droid\n" +
                                "2. pkg install git && git clone https://github.com/ferelking242/panda-ai\n" +
                                "3. cd panda-ai && bash android/setup-termux.sh\n" +
                                "4. bash start-panda.sh",
                                color = Color(0xFFaaaaaa),
                                fontSize = 12.sp,
                                lineHeight = 18.sp
                            )
                            Spacer(modifier = Modifier.height(8.dp))
                            OutlinedButton(
                                onClick = {
                                    val intent = Intent(Intent.ACTION_VIEW, Uri.parse("https://f-droid.org/packages/com.termux/"))
                                    context.startActivity(intent)
                                },
                                colors = OutlinedButtonDefaults.outlinedButtonColors(
                                    contentColor = Color(0xFF00d4ff)
                                )
                            ) {
                                Text("Install Termux →", fontSize = 12.sp)
                            }
                        }
                    }
                }

            } else {
                // ── WebView screen ─────────────────────────────
                val url = when (currentView) {
                    "chat" -> "$serverUrl/client"
                    "docs" -> "$serverUrl/docs"
                    else -> "$serverUrl/client"
                }

                // Back button
                OutlinedButton(
                    onClick = { showWebView = false },
                    colors = OutlinedButtonDefaults.outlinedButtonColors(
                        contentColor = Color(0xFF00d4ff)
                    ),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text("← Back")
                }

                AndroidView(
                    factory = { ctx ->
                        WebView(ctx).apply {
                            settings.javaScriptEnabled = true
                            settings.domStorageEnabled = true
                            settings.allowFileAccess = true
                            settings.allowContentAccess = true
                            settings.mixedContentMode = WebSettings.MIXED_CONTENT_ALWAYS_ALLOW
                            webViewClient = object : WebViewClient() {
                                override fun onPageFinished(view: WebView?, url: String?) {
                                    // Page loaded
                                }
                            }
                            loadUrl(url)
                        }
                    },
                    modifier = Modifier
                        .fillMaxWidth()
                        .weight(1f)
                )
            }
        }
    }
}

private suspend fun checkBackend(url: String): Boolean {
    return withContext(Dispatchers.IO) {
        try {
            val connection = URL("$url/healthz").openConnection() as HttpURLConnection
            connection.connectTimeout = 3000
            connection.readTimeout = 3000
            connection.requestMethod = "GET"
            val code = connection.responseCode
            connection.disconnect()
            code == 200
        } catch (e: Exception) {
            false
        }
    }
}

@Composable
fun PandaAITheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = darkColorScheme(
            primary = Color(0xFF00d4ff),
            secondary = Color(0xFF7b2ff7),
            background = Color(0xFF0d1117),
            surface = Color(0xFF1a1a2e),
            onPrimary = Color(0xFF0d1117),
            onBackground = Color.White,
            onSurface = Color.White,
        ),
        content = content
    )
}
