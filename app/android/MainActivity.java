package com.xingcheng.story;

import android.app.Activity;
import android.os.Bundle;
import android.os.Build;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.WebSettings;
import android.webkit.JavascriptInterface;
import android.view.KeyEvent;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;
import android.util.Log;
import android.content.Intent;
import android.speech.tts.TextToSpeech;
import android.speech.tts.UtteranceProgressListener;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import org.json.JSONArray;

public class MainActivity extends Activity {
    private static final String TAG = "XingCheng";
    private WebView webView;
    private TTSBridge ttsBridge;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
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

        super.onCreate(savedInstanceState);
        webView = new WebView(this);
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

        // 让 WebView 的 User-Agent 携带 Edg/ 标记：
        // 微软 Edge TTS 要求 wss 握手 UA 必须含 "Edg/"，否则连接会被直接拒绝（non-101）。
        // 版本号须与 H5 端 tts_edge.js 的 Sec-MS-GEC-Version(1-143.0.3650.75) 对应。
        String edgeUA = ws.getUserAgentString();
        if (edgeUA == null || edgeUA.isEmpty()) {
            edgeUA = "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Mobile Safari/537.36";
        }
        ws.setUserAgentString(edgeUA + " Edg/143.0.0.0");

        // 注入原生 TTS 桥接（小米系统自带中文离线 TTS，WebView 自身不支持 Web Speech API）
        ttsBridge = new TTSBridge();
        webView.addJavascriptInterface(ttsBridge, "AndroidTTS");

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public void onPageFinished(WebView view, String url) {
                super.onPageFinished(view, url);
                // 注入原生标记，CSS 据此切换满屏模式
                webView.evaluateJavascript("document.body.classList.add('native-app')", null);
                Log.i(TAG, "星橙故事铺 页面加载完成（全屏无标题栏 + 原生 TTS 桥接已注入）");
            }
        });
        webView.loadUrl("file:///android_asset/index.html");
        setContentView(webView);
        Log.i(TAG, "星橙故事铺 WebView 启动（全屏无标题栏）");
    }

    @Override
    public boolean onKeyDown(int keyCode, KeyEvent event) {
        if (keyCode == KeyEvent.KEYCODE_BACK && webView.canGoBack()) {
            webView.goBack();
            return true;
        }
        return super.onKeyDown(keyCode, event);
    }

    @Override
    protected void onDestroy() {
        if (ttsBridge != null) ttsBridge.shutdown();
        if (webView != null) { webView.destroy(); webView = null; }
        super.onDestroy();
    }

    /* ============================================================
       原生 TTS 桥接
       JS 侧通过 window.AndroidTTS 调用；回调统一走
       window.TTSNativeBridgeCallbacks（由 js/tts.js 定义）。
       底层使用安卓系统 TextToSpeech（小米自带中文离线语音）。
       ============================================================ */
    private class TTSBridge implements TextToSpeech.OnInitListener {
        private TextToSpeech tts;
        private boolean ready = false;
        private boolean suppressError = false;
        private List<String> queue = new ArrayList<>();
        private int idx = 0;
        private float rate = 1.0f;
        private boolean paused = false;
        private boolean pendingPlay = false;

        TTSBridge() {
            tts = new TextToSpeech(MainActivity.this, this);
        }

        @Override
        public void onInit(int status) {
            if (status == TextToSpeech.SUCCESS) {
                int avail = tts.isLanguageAvailable(new Locale("zh", "CN"));
                if (avail >= TextToSpeech.LANG_AVAILABLE) {
                    tts.setLanguage(new Locale("zh", "CN"));
                    ready = true;
                } else {
                    // 缺少中文语音数据，尝试引导系统安装
                    ready = false;
                    try {
                        Intent install = new Intent(TextToSpeech.Engine.ACTION_INSTALL_TTS_DATA);
                        startActivity(install);
                    } catch (Exception e) {
                        Log.w(TAG, "无法引导安装 TTS 数据", e);
                    }
                }
                tts.setSpeechRate(rate);
                tts.setOnUtteranceProgressListener(new UtteranceProgressListener() {
                    @Override
                    public void onStart(String u) {
                        emit("playing", "{}");
                    }
                    @Override
                    public void onDone(String u) {
                        final int i = parseIdx(u);
                        runOnUiThread(new Runnable() {
                            @Override public void run() {
                                if (i + 1 < queue.size()) {
                                    idx = i + 1;
                                    speakIdx(idx);
                                } else {
                                    idx = i;
                                    emit("finished", "{\"index\":" + i + "}");
                                }
                            }
                        });
                    }
                    @Override
                    public void onError(String u) {
                        if (suppressError) return;
                        emit("error", "{\"message\":\"朗读出错\"}");
                    }
                });
            } else {
                ready = false;
            }
            emit("idle", "{}");
            final boolean r = ready;
            runOnUiThread(new Runnable() {
                @Override public void run() {
                    js("window.TTSNativeBridgeCallbacks.onReady(" + r + ");");
                }
            });
            if (pendingPlay) { pendingPlay = false; play(); }
        }

        @JavascriptInterface
        public void setQueue(final String json) {
            runOnUiThread(new Runnable() {
                @Override public void run() {
                    try {
                        JSONArray arr = new JSONArray(json);
                        queue.clear();
                        for (int i = 0; i < arr.length(); i++) queue.add(arr.optString(i));
                    } catch (Exception e) {
                        queue.clear();
                    }
                    idx = 0;
                }
            });
        }

        @JavascriptInterface
        public void setRate(float r) {
            rate = (r > 0) ? r : 1.0f;
            if (tts != null) tts.setSpeechRate(rate);
        }

        @JavascriptInterface
        public void play() {
            runOnUiThread(new Runnable() {
                @Override public void run() {
                    if (!ready) { pendingPlay = true; return; }
                    paused = false;
                    if (idx >= queue.size()) idx = 0;
                    speakIdx(idx);
                }
            });
        }

        @JavascriptInterface
        public void pause() {
            runOnUiThread(new Runnable() {
                @Override public void run() {
                    suppressError = true;
                    if (tts != null) tts.stop();
                    paused = true;
                    emit("paused", "{}");
                }
            });
        }

        @JavascriptInterface
        public void resume() {
            runOnUiThread(new Runnable() {
                @Override public void run() {
                    paused = false;
                    speakIdx(idx);
                }
            });
        }

        @JavascriptInterface
        public void stop() {
            runOnUiThread(new Runnable() {
                @Override public void run() {
                    suppressError = true;
                    if (tts != null) tts.stop();
                    suppressError = false;
                    paused = false;
                    idx = 0;
                    emit("idle", "{}");
                }
            });
        }

        @JavascriptInterface
        public void next() {
            runOnUiThread(new Runnable() {
                @Override public void run() {
                    if (idx < queue.size() - 1) { idx++; speakIdx(idx); }
                }
            });
        }

        @JavascriptInterface
        public void prev() {
            runOnUiThread(new Runnable() {
                @Override public void run() {
                    if (idx > 0) { idx--; speakIdx(idx); }
                }
            });
        }

        @JavascriptInterface
        public void seek(int i) {
            runOnUiThread(new Runnable() {
                @Override public void run() {
                    if (i >= 0 && i < queue.size()) { idx = i; speakIdx(idx); }
                }
            });
        }

        @JavascriptInterface
        public boolean isReady() { return ready; }

        private void speakIdx(int i) {
            if (!ready || i < 0 || i >= queue.size()) return;
            suppressError = false;
            emit("requesting", "{\"index\":" + i + "}");
            // 提前高亮当前句（即便个别系统 onStart 不回调也能稳定跟随）
            js("window.TTSNativeBridgeCallbacks.onSentence(" + i + ");");
            String u = "s" + i;
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
                Bundle params = new Bundle();
                tts.speak(queue.get(i), TextToSpeech.QUEUE_FLUSH, params, u);
            } else {
                HashMap<String, String> params = new HashMap<String, String>();
                params.put(TextToSpeech.Engine.KEY_PARAM_UTTERANCE_ID, u);
                tts.speak(queue.get(i), TextToSpeech.QUEUE_FLUSH, params);
            }
        }

        private int parseIdx(String u) {
            try { return Integer.parseInt(u.substring(1)); } catch (Exception e) { return 0; }
        }

        private void emit(String s, String infoJson) {
            js("window.TTSNativeBridgeCallbacks.onState('" + s + "', " + (infoJson == null ? "{}" : infoJson) + ");");
        }

        private void js(final String code) {
            runOnUiThread(new Runnable() {
                @Override public void run() {
                    if (webView != null) webView.evaluateJavascript(code, null);
                }
            });
        }

        void shutdown() {
            if (tts != null) { tts.stop(); tts.shutdown(); tts = null; }
        }
    }
}
