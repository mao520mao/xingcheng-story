/**
 * 星橙故事铺 — 阿里云百炼 TTS 朗读模块
 * 使用非实时语音合成 HTTP API (qwen3-tts-flash + Serena 温柔女声)
 * 支持长文本自动分块、逐段合成、串行播放
 */
(function () {
  'use strict';

  var API_KEY = 'sk-ws-H.ERLXIRL.vTuY.MEUCIQD5UTs8EQ0VhsqvLMyOp11fs-3zDOG1LrvshzCRPVr51AIgWYLm3Q4Jd3us5z62wXdtDeRN0YY06RW_eA8wqp_Vy_Q';
  var PROXY_URL = 'https://bailian-tts.m476504127.workers.dev'; // Cloudflare Worker 代理，解决 file:// 跨域
  var DIRECT_URL = 'https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation';
  var USE_PROXY = true;  // true=走代理, false=直连
  var API_URL = USE_PROXY ? PROXY_URL : DIRECT_URL;
  var MODEL = 'qwen3-tts-flash';
  var VOICE = 'Serena';   // 苏瑶 — 温柔小姐姐

  /**
   * 合成单段文本，返回音频 URL
   */
  function synthesizeChunk(text, voice) {
    return new Promise(function (resolve, reject) {
      var xhr = new XMLHttpRequest();
      xhr.open('POST', API_URL, true);
      if (!USE_PROXY) {
        xhr.setRequestHeader('Authorization', 'Bearer ' + API_KEY);
      }
      xhr.setRequestHeader('Content-Type', 'application/json');
      xhr.timeout = 60000; // 60s 超时（移动网络可能较慢）

      xhr.onload = function () {
        try {
          var resp = JSON.parse(xhr.responseText);
          if (xhr.status === 200 && resp.output && resp.output.audio && resp.output.audio.url) {
            resolve({
              url: resp.output.audio.url,
              characters: (resp.usage && resp.usage.characters) || text.length
            });
          } else {
            var msg = resp.message || resp.code || '';
            reject(new Error('合成失败 HTTP' + xhr.status + (msg ? ': ' + msg : '')));
          }
        } catch (e) {
          reject(new Error('解析响应失败 HTTP' + xhr.status));
        }
      };

      xhr.onerror = function () {
        reject(new Error('网络错误(状态码' + (xhr.status || '0') + ', 可能需部署Worker)'));
      };

      xhr.ontimeout = function () {
        reject(new Error('请求超时(>60s)'));
      };

      var body = USE_PROXY
        ? { text: text, voice: voice || VOICE, language_type: 'Chinese' }
        : { model: MODEL, input: { text: text, voice: voice || VOICE, language_type: 'Chinese' } };

      xhr.send(JSON.stringify(body));
    });
  }

  /**
   * 按句子边界分块，尽量不在句子中间截断
   */
  function chunkText(text, maxChars) {
    maxChars = maxChars || 1500;
    if (text.length <= maxChars) return [text];

    var chunks = [];
    // 按句末标点拆分
    var sentences = text.match(/[^。！？；\n]+[。！？；\n]?/g) || [text];
    var current = '';

    for (var i = 0; i < sentences.length; i++) {
      var s = sentences[i];
      if (current.length + s.length > maxChars && current.length > 200) {
        chunks.push(current.trim());
        current = s;
      } else {
        current += s;
      }
    }
    if (current.trim()) chunks.push(current.trim());
    return chunks.length ? chunks : [text];
  }

  /**
   * 合成完整文本（自动分块），返回 [{url, characters}, ...]
   */
  function synthesize(text, options) {
    options = options || {};
    var voice = options.voice || VOICE;
    var onProgress = options.onProgress || function () {};

    var chunks = chunkText(text);
    var results = [];
    var total = chunks.length;

    function processNext(index) {
      if (index >= total) {
        return Promise.resolve(results);
      }
      onProgress(index, total);
      return synthesizeChunk(chunks[index], voice).then(function (result) {
        results.push(result);
        return processNext(index + 1);
      });
    }

    return processNext(0);
  }

  window.BailianTTS = {
    synthesize: synthesize,
    MODEL: MODEL,
    VOICE: VOICE,
    voices: [
      { id: 'Serena',   name: '苏瑶', desc: '温柔小姐姐' },
      { id: 'Maia',     name: '四月', desc: '知性与温柔的碰撞' },
      { id: 'Katerina', name: '卡捷琳娜', desc: '御姐音色' },
      { id: 'Seren',    name: '小婉', desc: '温和舒缓' },
      { id: 'Cherry',   name: '芊悦', desc: '亲切自然' }
    ]
  };
})();
