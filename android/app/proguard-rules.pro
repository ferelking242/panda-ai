# WebView JavaScript interface
-keepclassmembers class com.pandaai.gateway.WebBridge {
    @android.webkit.JavascriptInterface <methods>;
}

# Keep WebView class
-keep class android.webkit.** { *; }
