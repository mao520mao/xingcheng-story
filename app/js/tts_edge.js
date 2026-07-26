/*
 * tts_edge.js — 浏览器端微软 Edge 免费神经语音客户端（星橙故事铺 V19）
 * 无需 API key、无需服务器、无需任何自定义请求头（实测微软不校验 Origin/MUID）。
 * 仅在 WebView 内通过 WebSocket 直连 speech.platform.bing.com，需手机联网。
 * 因 WebView 处于 file:// 非安全上下文，window.crypto.subtle 不可用，故内置同步 SHA256。
 */
(function (global) {
  'use strict';

  /* ---------- 内置 SHA256（同步，纯 JS，避免依赖 crypto.subtle） ---------- */
  /* 仅处理 ASCII 输入（本模块输入均为「数字+十六进制」字符串，满足约束）。k 常量缓存复用。 */
  function sha256(msg) {
    function rrot(n, x) { return (x >>> n) | (x << (32 - n)); }
    var maxWord = Math.pow(2, 32);
    var asciiBitLength = msg.length * 8;

    // k 常量只推导一次并缓存（常量，不变）
    var k = sha256.k;
    if (!k) {
      k = sha256.k = [];
      var isComposite = {};
      var primeCounter = 0;
      for (var candidate = 2; primeCounter < 64; candidate++) {
        if (!isComposite[candidate]) {
          for (var i = 0; i < 313; i += candidate) isComposite[i] = true;
          k[primeCounter++] = (Math.pow(candidate, 1 / 3) * maxWord) | 0;
        }
      }
    }
    // 每次调用使用全新的初始向量（切勿复用/污染）
    var H = [0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19];

    // 按 512-bit(64 字节) 分块，零填充 words，避免 undefined
    var blockCount = ((asciiBitLength + 64) >> 9) + 1;
    var words = new Array(blockCount * 16).fill(0);
    for (var n = 0; n < msg.length; n++) {
      var c = msg.charCodeAt(n) & 0xff; // ASCII
      words[n >> 2] |= c << (24 - (n % 4) * 8);
    }
    var p = msg.length; // 0x80 紧跟在最后字节之后
    words[p >> 2] |= 0x80 << (24 - (p % 4) * 8);
    words[blockCount * 16 - 1] = asciiBitLength; // 长度(低 32 位)置于末字

    for (var n = 0; n < words.length; n += 16) {
      var w = words.slice(n, n + 16);
      for (var i = 16; i < 64; i++) {
        var w15 = w[i - 15], w2 = w[i - 2];
        var sa = rrot(7, w15) ^ rrot(18, w15) ^ (w15 >>> 3);
        var sb = rrot(17, w2) ^ rrot(19, w2) ^ (w2 >>> 10);
        w[i] = (w[i - 16] + sa + w[i - 7] + sb) | 0;
      }
      var a = H[0], b = H[1], c = H[2], d = H[3], e = H[4], f = H[5], g = H[6], h = H[7];
      for (var i = 0; i < 64; i++) {
        var T1 = (h + (rrot(6, e) ^ rrot(11, e) ^ rrot(25, e)) + ((e & f) ^ (~e & g)) + k[i] + w[i]) | 0;
        var T2 = ((rrot(2, a) ^ rrot(13, a) ^ rrot(22, a)) + ((a & b) ^ (a & c) ^ (b & c))) | 0;
        h = g; g = f; f = e; e = (d + T1) | 0; d = c; c = b; b = a; a = (T1 + T2) | 0;
      }
      H[0] = (H[0] + a) | 0; H[1] = (H[1] + b) | 0; H[2] = (H[2] + c) | 0; H[3] = (H[3] + d) | 0;
      H[4] = (H[4] + e) | 0; H[5] = (H[5] + f) | 0; H[6] = (H[6] + g) | 0; H[7] = (H[7] + h) | 0;
    }
    var out = '';
    for (var n = 0; n < 8; n++) out += ('00000000' + (H[n] >>> 0).toString(16)).slice(-8);
    return out.toUpperCase();
  }

  /* ---------- 常量（与 edge-tts 7.2.8 对齐） ---------- */
  var TRUSTED = '6A5AA1D4EAFF4E9FB37E23D68491D6F4';
  var GEC_VER = '1-143.0.3650.75';
  var WIN_EPOCH = 11644473600; // 1601-01-01 与 1970-01-01 的秒差
  var OUTPUT_FORMAT = 'audio-24khz-48kbitrate-mono-mp3';

  function genToken() {
    var ticks = Date.now() / 1000 + WIN_EPOCH;
    ticks -= ticks % 300;           // 向下取整到 5 分钟
    ticks *= 1e7;                   // 100 纳秒间隔（注意：该量级超出安全整数，需与 Python 的 f"{ticks:.0f}" 同样四舍五入）
    return sha256(ticks.toFixed(0) + TRUSTED).toUpperCase();
  }

  function escapeXml(s) {
    return String(s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&apos;');
  }

  // 把长文本切成 ≤max 字符的分片（按句/段切），避免超出接口单次长度限制
  function chunkText(text, max) {
    max = max || 1500;
    var segs = String(text).match(/[^。！？；!?;\n]*[。！？；!?;\n]?/g) || [text];
    var chunks = [], cur = '';
    for (var i = 0; i < segs.length; i++) {
      var s = segs[i];
      if (!s.trim()) continue;
      if (cur.length + s.length > max && cur) { chunks.push(cur); cur = s; }
      else cur += s;
    }
    if (cur) chunks.push(cur);
    return chunks.length ? chunks : [text];
  }

  // 计算（近似）句子切分，用于高亮与时长估算
  function splitSentences(text) {
    var out = [], idx = 0;
    var re = /[^。！？；!?;\n]+[。！？；!?;\n]?/g, m;
    while ((m = re.exec(text)) !== null) {
      var seg = m[0].trim();
      if (!seg) continue;
      out.push({ text: seg, start: idx, end: idx + seg.length });
      idx += seg.length;
    }
    return out;
  }

  var VOICES = [
    { id: 'zh-CN-XiaoxiaoNeural', name: '晓晓（温柔女声·推荐）' },
    { id: 'zh-CN-YunxiNeural', name: '云希（活力男声）' },
    { id: 'zh-CN-YunyangNeural', name: '云扬（沉稳男声）' }
  ];

  /*
   * speak(opts)
   *   opts: {
   *     text: string,
   *     voice: string (默认 zh-CN-XiaoxiaoNeural),
   *     rate: string (如 '-10%' / '0%' / '10%'),
   *     audio: optional <audio> 元素（不传则内部创建隐藏元素）,
   *     onState: function(state, info)  state: 'connecting'|'playing'|'paused'|'ended'|'error',
   *     onProgress: function(currentSec, totalSec),
   *     onSentence: function(index, sentenceText)  // 当前高亮句
   *   }
   * 返回 controller: { audio, pause(), resume(), stop(), state }
   */
  function speak(opts) {
    opts = opts || {};
    var text = (opts.text || '').trim();
    var voice = opts.voice || 'zh-CN-XiaoxiaoNeural';
    var rate = opts.rate || '-10%';
    var onState = opts.onState || function () {};
    var onProgress = opts.onProgress || function () {};
    var onSentence = opts.onSentence || function () {};

    if (!text) { onState('error', 'empty text'); return null; }
    if (typeof global.WebSocket === 'undefined') { onState('error', 'WebSocket 不可用'); return null; }

    var audio = opts.audio || (function () { var a = new Audio(); a.style.display = 'none'; document.body.appendChild(a); return a; })();
    var useMS = (typeof global.MediaSource !== 'undefined') && MediaSource.isTypeSupported('audio/mpeg');

    var chunks = chunkText(text, 1500);
    var sentences = splitSentences(text);
    // 估算总时长：中文约 4.5 字/秒（rate -10% 略慢），用于进度条与高亮映射
    var estTotal = Math.max(1, text.length / 4.5);

    var token = genToken();
    var connId = (function () { var s = ''; for (var i = 0; i < 16; i++) s += Math.floor(Math.random() * 16).toString(16); return s; })();
    var wsUrl = 'wss://speech.platform.bing.com/consumer/speech/synthesize/readaloud/edge/v1'
      + '?TrustedClientToken=' + TRUSTED
      + '&ConnectionId=' + connId
      + '&Sec-MS-GEC=' + token
      + '&Sec-MS-GEC-Version=' + GEC_VER;

    var ws = null, sb = null, ms = null, audioQueue = [], sentIdx = 0, allSent = false, finalized = false, started = false;
    var sbReady = false, wsReady = false;
    var curSentence = -1, controller = { audio: audio, state: 'connecting', pause: pause, resume: resume, stop: stop };

    function ts() { return new Date().toUTCString(); }
    function configMsg() {
      return 'X-Timestamp:' + ts() + '\r\nContent-Type:application/json; charset=utf-8\r\nPath:speech.config\r\n\r\n'
        + '{"context":{"synthesis":{"audio":{"metadataoptions":{"sentenceBoundaryEnabled":"false","wordBoundaryEnabled":"false"},'
        + '"outputFormat":"' + OUTPUT_FORMAT + '"}}}}\r\n';
    }
    function ssmlMsg(chunk) {
      var ssml = "<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='zh-CN'>"
        + "<voice name='" + voice + "'><prosody pitch='0%' rate='" + rate + "' volume='0%'>"
        + escapeXml(chunk) + "</prosody></voice></speak>";
      return 'X-RequestId:' + connId + '\r\nContent-Type:application/ssml+xml\r\nX-Timestamp:' + ts() + 'Z\r\nPath:ssml\r\n\r\n' + ssml;
    }
    function maybeSend() {
      // 仅在「音频缓冲就绪」且「WebSocket 就绪」时发送下一段，确保每段只发一次
      if (sbReady && wsReady && sentIdx < chunks.length && ws && ws.readyState === 1) {
        ws.send(ssmlMsg(chunks[sentIdx])); sentIdx++;
      }
    }
    function appendNext() {
      if (!sb || sb.updating || !audioQueue.length) return;
      try { sb.appendBuffer(audioQueue.shift()); } catch (e) { /* ignore */ }
    }
    function finalize() {
      if (finalized) return; finalized = true;
      if (ms && ms.readyState === 'open') { try { ms.endOfStream(); } catch (e) {} }
      if (ws && ws.readyState === 1) { try { ws.close(); } catch (e) {} }
    }

    function onAudioChunk(ab) {
      audioQueue.push(ab);
      appendNext();
      if (!started) {
        started = true;
        audio.play().then(function () { controller.state = 'playing'; onState('playing'); }).catch(function (e) { onState('error', '播放失败:' + e.message); });
      }
    }

    // 进度与高亮
    audio.addEventListener('timeupdate', function () {
      var cur = audio.currentTime || 0;
      onProgress(cur, estTotal);
      var pos = Math.floor((cur / estTotal) * text.length);
      var si = -1;
      for (var i = 0; i < sentences.length; i++) { if (pos >= sentences[i].start && pos < sentences[i].end) { si = i; break; } }
      if (si === -1 && pos >= text.length && sentences.length) si = sentences.length - 1;
      if (si !== curSentence) { curSentence = si; if (si >= 0) onSentence(si, sentences[si].text); }
    });
    audio.addEventListener('ended', function () { controller.state = 'ended'; onState('ended'); });
    audio.addEventListener('pause', function () { if (controller.state === 'playing') { controller.state = 'paused'; onState('paused'); } });
    audio.addEventListener('play', function () { if (controller.state === 'paused') { controller.state = 'playing'; onState('playing'); } });

    function pump() {
      ms = new MediaSource();
      audio.src = URL.createObjectURL(ms);
      ms.addEventListener('sourceopen', function () {
        try { sb = ms.addSourceBuffer('audio/mpeg'); } catch (e) { onState('error', '音频解码不支持'); return; }
        sb.addEventListener('updateend', appendNext);
        sbReady = true;
        maybeSend(); // 首段会在 ws 就绪后由 maybeSend 统一发送
      });
    }

    onState('connecting');
    try {
      if (useMS) {
        pump();
      } else {
        onState('error', '当前 WebView 不支持 MediaSource 流式播放');
        return controller;
      }
    } catch (e) {
      onState('error', '初始化失败:' + e.message);
      return controller;
    }

    // WebSocket 连接（在 pump 之后建立，确保 sb 就绪前先缓存音频）
    try {
      ws = new WebSocket(wsUrl);
    } catch (e) {
      onState('error', 'WebSocket 创建失败:' + e.message);
      return controller;
    }
    ws.binaryType = 'arraybuffer';
    ws.addEventListener('open', function () {
      ws.send(configMsg());
      wsReady = true;
      maybeSend(); // 发送第一段（如 sb 尚未就绪则待 sourceopen 触发）
    });
    ws.addEventListener('message', function (ev) {
      var data = ev.data;
      var buf = (data instanceof ArrayBuffer) ? new Uint8Array(data) : null;
      if (!buf || buf.length < 2) return;
      var hl = (buf[0] << 8) | buf[1]; // 头部长度（大端）
      if (hl > buf.length) return;
      var header = '';
      for (var i = 2; i < 2 + hl; i++) header += String.fromCharCode(buf[i]);
      if (header.indexOf('Path:audio') !== -1 && header.indexOf('Content-Type:audio') !== -1) {
        onAudioChunk(buf.slice(2 + hl)); // 拷贝出独立 Uint8Array，避免底层缓冲复用导致串音
      } else if (header.indexOf('Path:turn.end') !== -1) {
        if (sentIdx < chunks.length) maybeSend();
        else { allSent = true; if (!audioQueue.length) finalize(); }
      }
    });
    ws.addEventListener('error', function (e) { onState('error', '网络错误或微软接口不可达（请检查联网）' + (e && e.message ? '：' + e.message : '')); });
    ws.addEventListener('close', function () { if (allSent && !audioQueue.length) finalize(); });

    // 缓冲排空后收尾
    var drainTimer = setInterval(function () {
      if (finalized || !allSent) return;
      if (!audioQueue.length) { clearInterval(drainTimer); finalize(); }
    }, 500);

    function pause() { try { audio.pause(); } catch (e) {} }
    function resume() { if (controller.state === 'paused') { audio.play().catch(function () {}); } }
    function stop() {
      clearInterval(drainTimer);
      try { audio.pause(); audio.currentTime = 0; } catch (e) {}
      try { if (ws && ws.readyState === 1) ws.close(); } catch (e) {}
      try { if (ms && ms.readyState === 'open') ms.endOfStream(); } catch (e) {}
      audioQueue = [];
      controller.state = 'stopped';
      onState('stopped');
    }

    return controller;
  }

  global.EdgeTTS = { speak: speak, VOICES: VOICES, sha256: sha256 };
})(typeof window !== 'undefined' ? window : this);
