package com.xingcheng.story;

import android.app.Activity;
import android.os.Bundle;
import android.os.Build;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.WebSettings;
import android.view.KeyEvent;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;
import android.widget.TextView;
import android.graphics.Color;
import android.util.Log;
import android.content.Intent;

public class MainActivity extends Activity {
    private static final String TAG = "XingCheng";
    private WebView webView;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setupCrashHandler();
        try {
            // 隐藏标题栏 + 全屏沉浸式（去掉顶部灰色「星橙故事铺」色块）
            requestWindowFeature(Window.FEATURE_NO_TITLE);
            getWindow().setFlags(
                WindowManager.LayoutParams.FLAG_FULLSCREEN,
                WindowManager.LayoutParams.FLAG_FULLSCREEN
            );
            // 隐藏系统导航栏，让内容真正全屏
            getWindow().getDecorView().setSystemUiVisibility(
                View.SYSTEM_UI_FLAG_LAYOUT_STABLE
                | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
                | View.SYSTEM_UI_FLAG_FULLSCREEN
                | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
            );

            webView = new WebView(this);
            // 注：本工程为纯文字阅读 App，无语音朗读（TTS 已移除），
            // 故恢复硬件加速（第一版即开启，毛玻璃为 GPU 加速，流畅）。
            WebSettings ws = webView.getSettings();
            ws.setJavaScriptEnabled(true);
            ws.setDomStorageEnabled(true);
            ws.setAllowFileAccess(true);
            ws.setAllowContentAccess(true);
            ws.setMediaPlaybackRequiresUserGesture(false);
            ws.setMixedContentMode(WebSettings.MIXED_CONTENT_ALWAYS_ALLOW);
            ws.setCacheMode(WebSettings.LOAD_DEFAULT);
            ws.setDatabaseEnabled(true);
            ws.setSupportZoom(false);
            ws.setUseWideViewPort(true);
            ws.setLoadWithOverviewMode(true);

            webView.setWebViewClient(new WebViewClient() {
                @Override
                public void onPageFinished(WebView view, String url) {
                    super.onPageFinished(view, url);
                    webView.evaluateJavascript("document.body.classList.add('native-app')", null);
                    Log.i(TAG, "星橙故事铺 页面加载完成（全屏无标题栏）");
                }
            });
            setContentView(webView);
            webView.loadUrl("file:///android_asset/index.html");
            Log.i(TAG, "星橙故事铺 WebView 启动（全屏无标题栏，已移除语音朗读）");
        } catch (Throwable t) {
            showError(t);
        }
    }

    /** 把启动期的任何 Java 异常显示在屏幕上，而不是让 APP 直接闪退。 */
    private void showError(Throwable t) {
        StringBuilder sb = new StringBuilder();
        sb.append("星橙故事铺启动出错（已捕获，未闪退）：\n\n");
        sb.append(t.toString()).append("\n\n调用栈：\n");
        for (StackTraceElement e : t.getStackTrace()) {
            sb.append(e.toString()).append("\n");
        }
        TextView tv = new TextView(this);
        tv.setText(sb.toString());
        tv.setTextColor(Color.WHITE);
        tv.setBackgroundColor(Color.rgb(11, 18, 41));
        tv.setTextSize(12);
        tv.setPadding(24, 24, 24, 24);
        setContentView(tv);
        Log.e(TAG, "启动异常", t);
    }

    /** 兜底：捕获异步线程未处理异常，写入 crash.txt 便于排查。 */
    private void setupCrashHandler() {
        final Thread.UncaughtExceptionHandler def = Thread.getDefaultUncaughtExceptionHandler();
        Thread.setDefaultUncaughtExceptionHandler(new Thread.UncaughtExceptionHandler() {
            @Override
            public void uncaughtException(Thread t, Throwable e) {
                try {
                    java.io.File dir = getExternalFilesDir(null);
                    if (dir != null) {
                        java.io.File f = new java.io.File(dir, "crash.txt");
                        java.io.FileWriter w = new java.io.FileWriter(f);
                        w.write("thread=" + t.getName() + "\n");
                        w.write(Log.getStackTraceString(e));
                        w.close();
                    }
                } catch (Exception ignore) {}
                if (def != null) def.uncaughtException(t, e);
            }
        });
    }

    @Override
    public boolean onKeyDown(int keyCode, KeyEvent event) {
        if (keyCode == KeyEvent.KEYCODE_BACK && webView != null && webView.canGoBack()) {
            webView.goBack();
            return true;
        }
        return super.onKeyDown(keyCode, event);
    }

    @Override
    protected void onDestroy() {
        if (webView != null) { webView.destroy(); webView = null; }
        super.onDestroy();
    }
}
