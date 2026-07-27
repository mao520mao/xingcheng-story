/**
 * 星橙故事铺 — Edge TTS 中转服务（Cloudflare Worker）
 * ---------------------------------------------------------------
 * 作用：浏览器/WebView 无法在 WebSocket 握手时自定义请求头，
 *       而微软 Edge TTS 现在要求带 Edg UA + Cookie muid + Origin 等头，
 *       否则拒绝连接（non-101）。本 Worker 在服务端代发这些头去连微软，
 *       再把音频流式转发回客户端。国内手机直连微软常失败，走此中转即可。
 *
 * 部署（免费，无需信用卡绑卡也可）：
 *   1) 打开 https://dash.cloudflare.com → 左侧「Workers 和 Pages」→「创建」→ 选「Worker」。
 *   2) 取名（如 xingcheng-tts），选 Hello World 模板，「部署」。
 *   3) 部署后点「编辑代码」，把本文件全部内容粘贴覆盖，点「部署」。
 *   4) 记下分配的地址，形如 https://xingcheng-tts.<你的子域>.workers.dev
 *   5) 在 App「设置 → 朗读设置 → 中转地址」里填入：wss://xingcheng-tts.<你的子域>.workers.dev
 *      （注意协议是 wss:// 不是 https://）
 *
 * 客户端（星橙 App）只需把合成请求（speech.config + ssml）发到本 Worker，
 * 本 Worker 透明转发到微软并回传音频，不解析任何内容。
 */
const TRUSTED = '6A5AA1D4EAFF4E9FB37E23D68491D6F4';
const GEC_VER = '1-143.0.3650.75';
const WIN_EPOCH = 11644473600;

// 与 edge-tts 7.2.8 / app/js/tts_edge.js 完全一致的令牌算法（JS 浮点），保证与微软校验一致
function genTokenInput() {
  let ticks = Date.now() / 1000 + WIN_EPOCH;
  ticks -= ticks % 300;
  ticks *= 1e7;
  return ticks.toFixed(0) + TRUSTED;
}
async function sha256Hex(str) {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(str));
  return [...new Uint8Array(buf)].map((b) => b.toString(16).pad('0', 2)).join('').toUpperCase();
}
function randHex(n) {
  const a = new Uint8Array(n);
  crypto.getRandomValues(a);
  return [...a].map((b) => b.toString(16).padStart(2, '0')).join('').toUpperCase();
}

export default {
  async fetch(request) {
    if (request.headers.get('Upgrade') !== 'websocket') {
      return new Response('星橙 TTS 中转：请用 WebSocket 连接', { status: 400 });
    }

    const [client, server] = Object.values(new WebSocketPair());
    server.binaryType = 'arraybuffer';
    server.accept({ allowHalfOpen: true });

    const token = await sha256Hex(genTokenInput());
    const connId = randHex(8);
    const upstreamUrl =
      'wss://speech.platform.bing.com/consumer/speech/synthesize/readaloud/edge/v1' +
      '?TrustedClientToken=' + TRUSTED +
      '&ConnectionId=' + connId +
      '&Sec-MS-GEC=' + token +
      '&Sec-MS-GEC-Version=' + GEC_VER;

    const headers = {
      'Upgrade': 'websocket',
      'Pragma': 'no-cache',
      'Cache-Control': 'no-cache',
      'Origin': 'chrome-extension://jdiccldimpdaibmpdkjnbmckianbfold',
      'User-Agent':
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ' +
        '(KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0',
      'Cookie': 'muid=' + randHex(16) + ';',
    };

    try {
      const resp = await fetch(upstreamUrl, { headers });
      const upstream = resp.webSocket;
      if (!upstream) {
        server.close(1011, '上游连接失败');
        return new Response(null, { status: 101, webSocket: client });
      }
      upstream.binaryType = 'arraybuffer';
      upstream.accept({ allowHalfOpen: true });

      upstream.addEventListener('message', (e) => { try { server.send(e.data); } catch (_) {} });
      upstream.addEventListener('close', () => { try { server.close(); } catch (_) {} });
      upstream.addEventListener('error', () => { try { server.close(); } catch (_) {} });
      server.addEventListener('message', (e) => { try { upstream.send(e.data); } catch (_) {} });
      server.addEventListener('close', () => { try { upstream.close(); } catch (_) {} });
      server.addEventListener('error', () => { try { upstream.close(); } catch (_) {} });
    } catch (err) {
      try { server.close(1011, '中转异常'); } catch (_) {}
    }

    return new Response(null, { status: 101, webSocket: client });
  },
};
