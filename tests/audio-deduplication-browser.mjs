import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const baseUrl = process.argv[2] || 'http://127.0.0.1:8765/';
const port = Number(process.env.CDP_PORT || 9841);
const profile = mkdtempSync(join(tmpdir(), 'punto-cero-dedupe-'));
const chrome = spawn(process.env.CHROME_PATH || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe', [
  `--remote-debugging-port=${port}`, `--user-data-dir=${profile}`,
  '--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check', 'about:blank'
], { windowsHide: true, stdio: 'ignore' });
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
let socket;
try {
  let info;
  for (let i = 0; i < 100; i++) {
    try { info = await (await fetch(`http://127.0.0.1:${port}/json/version`)).json(); break; } catch { await sleep(100); }
  }
  assert.ok(info, 'Chrome started');
  socket = new WebSocket(info.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => {
    socket.addEventListener('open', resolve, { once: true });
    socket.addEventListener('error', reject, { once: true });
  });
  const pending = new Map();
  const exceptions = [];
  const requests = [];
  let nextId = 0;
  socket.addEventListener('message', event => {
    const message = JSON.parse(event.data);
    if (message.id && pending.has(message.id)) {
      const entry = pending.get(message.id); pending.delete(message.id);
      clearTimeout(entry.timer);
      message.error ? entry.reject(new Error(message.error.message)) : entry.resolve(message.result);
    }
    if (message.method === 'Runtime.exceptionThrown') exceptions.push(message.params.exceptionDetails);
    if (message.method === 'Network.requestWillBeSent') requests.push(message.params.request.url);
  });
  function send(method, params = {}, sessionId) {
    const id = ++nextId;
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => { pending.delete(id); reject(new Error(`Timeout: ${method}`)); }, 30000);
      pending.set(id, { resolve, reject, timer });
      socket.send(JSON.stringify({ id, method, params, ...(sessionId ? { sessionId } : {}) }));
    });
  }
  const { targetId } = await send('Target.createTarget', { url: 'about:blank' });
  const { sessionId } = await send('Target.attachToTarget', { targetId, flatten: true });
  await send('Page.enable', {}, sessionId);
  await send('Runtime.enable', {}, sessionId);
  await send('Network.enable', {}, sessionId);
  async function evaluate(expression) {
    const result = await send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true, userGesture: true }, sessionId);
    if (result.exceptionDetails) throw new Error(result.exceptionDetails.text);
    return result.result.value;
  }
  async function waitFor(expression, label, attempts = 120) {
    for (let i = 0; i < attempts; i++) {
      const value = await evaluate(expression);
      if (value) return value;
      await sleep(250);
    }
    const debug = await evaluate('({ audios: Array.from(document.querySelectorAll("audio")).map(a => ({ src: a.currentSrc, paused: a.paused, time: a.currentTime, ready: a.readyState, error: a.error?.message })), statuses: Array.from(document.querySelectorAll("[data-protected-audio-status]")).map(e => e.textContent) })');
    throw new Error(`Timed out waiting for ${label}: ${JSON.stringify(debug)}`);
  }
  const results = [];
  for (const width of [390, 1280]) {
    await send('Emulation.setDeviceMetricsOverride', { width, height: 844, deviceScaleFactor: 1, mobile: width < 768 }, sessionId);
    await send('Page.navigate', { url: baseUrl }, sessionId);
    await waitFor('Boolean(document.querySelector("#cover-enter"))', 'map entry');
    await evaluate('document.querySelector("#cover-enter").click()');
    await waitFor('window.PUNTO_CERO_APPROVED_TESTIMONIES?.length === 19', '19 unique approved points');
    await waitFor('window.puntoCeroMap?.getSource("sounds") && document.querySelectorAll(".point-item").length > 0', 'rendered map');
    const state = await evaluate(`(() => {
      const points = window.PUNTO_CERO_APPROVED_TESTIMONIES;
      return {
        count: points.length, uniqueHashes: new Set(points.map(p => p.audio_sha256)).size,
        ids: points.map(p => p.approved_submission_id),
        duplicates: window.PUNTO_CERO_AUDIO_DUPLICATES.length,
        unverified: window.PUNTO_CERO_UNVERIFIED_AUDIO_IDS,
        rows: document.querySelectorAll('.point-item').length,
        coverCount: document.querySelector('#cover-sound-count')?.textContent,
        sourceCount: window.puntoCeroMap.getSource('sounds').serialize().data.features.length
      };
    })()`);
    assert.equal(state.count, 19);
    assert.equal(state.uniqueHashes, 19);
    assert.equal(state.duplicates, 3);
    assert.equal(state.unverified.length, 0);
    for (const id of ['397cd3a0-382b-43ab-965b-ed19028a46be', '00ced058-392a-4c4d-9b3d-efcb8227e724', '432871f9-2d90-4d89-bed8-c5488a838823']) assert.ok(state.ids.includes(id));
    for (const id of ['a971be2d-10f2-452f-916a-4c0a635820f6', '2e9b48f3-266c-485e-970f-c3a0f580797c', '4e7c55c7-f109-45ba-881a-97529eff38c4']) assert.ok(!state.ids.includes(id));
    assert.equal(state.coverCount, '80 piezas sonoras');
    assert.equal(state.sourceCount, 79, 'Punto Cero has a separate marker');
    await evaluate(`document.querySelector('[data-id="supabase-00ced058-392a-4c4d-9b3d-efcb8227e724"]').click()`);
    if (width < 768) await evaluate('window.openMobilePointDetails(window.PUNTO_CERO_APPROVED_TESTIMONIES.find(p => p.approved_submission_id === "00ced058-392a-4c4d-9b3d-efcb8227e724"))');
    await waitFor('Boolean(document.querySelector("[data-protected-audio-toggle]"))', 'audio control');
    await evaluate('document.querySelector("[data-protected-audio-toggle]").click()');
    await waitFor('(() => { const a = document.querySelector("audio[data-protected-audio]"); return a && !a.paused && a.currentTime > 0; })()', 'retained audio playback');
    const playback = await evaluate('(() => { const a = document.querySelector("audio[data-protected-audio]"); const result = { playing: !a.paused, currentTime: a.currentTime, error: a.error?.code || null }; a.pause(); return result; })()');
    results.push({ width, ...state, playback });
  }
  assert.equal(exceptions.length, 0, 'no uncaught browser exceptions');
  console.log(JSON.stringify({ baseUrl, results, exceptions, fingerprintAudioDownloads: requests.filter(url => /storage\/v1\/object\/sign\//.test(url)).length }, null, 2));
} finally {
  socket?.close();
  chrome.kill();
}
