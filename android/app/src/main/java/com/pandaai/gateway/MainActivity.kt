package com.pandaai.gateway

import android.annotation.SuppressLint
import android.os.Bundle
import android.webkit.*
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView

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

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun GatewayScreen() {
    var serverUrl by remember { mutableStateOf("http://10.0.2.2:8000") }
    var isConnected by remember { mutableStateOf(false) }
    var showWebView by remember { mutableStateOf(false) }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("🐼 Panda AI", color = Color.White) },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = Color(0xFF0f172a)
                )
            )
        },
        containerColor = Color(0xFF0d1117)
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            Text(
                "Panda AI Gateway",
                fontSize = 24.sp,
                fontWeight = FontWeight.Bold,
                color = Color(0xFF00d4ff)
            )
            Text(
                "Browser-based OpenAI-compatible proxy",
                fontSize = 14.sp,
                color = Color(0xFF888888)
            )

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
                )
            )

            Button(
                onClick = { showWebView = true },
                colors = ButtonDefaults.buttonColors(
                    containerColor = Color(0xFF00d4ff)
                ),
                modifier = Modifier.fillMaxWidth()
            ) {
                Text("Open Dashboard", color = Color(0xFF0d1117), fontWeight = FontWeight.Bold)
            }

            Button(
                onClick = { showWebView = true },
                colors = ButtonDefaults.buttonColors(
                    containerColor = Color(0xFF7b2ff7)
                ),
                modifier = Modifier.fillMaxWidth()
            ) {
                Text("Chat (Test Client)", color = Color.White, fontWeight = FontWeight.Bold)
            }

            if (showWebView) {
                AndroidView(
                    factory = { context ->
                        WebView(context).apply {
                            settings.javaScriptEnabled = true
                            settings.domStorageEnabled = true
                            settings.allowFileAccess = true
                            webViewClient = object : WebViewClient() {
                                override fun onPageFinished(view: WebView?, url: String?) {
                                    isConnected = true
                                }
                            }
                            loadUrl("$serverUrl/client")
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
