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
    if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
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

  const results=[];
  await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]},sessionId);
  for(const width of [390,1280]) {
    await send('Emulation.setDeviceMetricsOverride',{width,height:844,deviceScaleFactor:1,mobile:width<768},sessionId);
    await send('Page.navigate',{url:baseUrl},sessionId);
    await waitFor('Boolean(document.querySelector("#cover-enter"))','entry');
    assert.equal(await evaluate('Boolean(document.querySelector(".otis-toggle"))'),false,'lazy map');
    await evaluate('document.querySelector("#cover-enter").click()');
    await waitFor('Boolean(window.puntoCeroMap?.isStyleLoaded() && document.querySelector(".otis-toggle"))','map');
    await evaluate('window.otisOriginalPoints=JSON.stringify(puntoCeroMap.getSource("sounds").serialize().data); document.querySelector(".otis-toggle").click()');
    await waitFor('Boolean(puntoCeroMap.getLayer("pc-otis-track-line"))','track');
    assert.equal(await evaluate('document.querySelectorAll(".otis-position").length'),7);
    assert.deepEqual(await evaluate('puntoCeroMap.getSource("pc-otis-track-source").serialize().data.geometry.coordinates'),[[-99.4,14.9],[-99.6,15.7],[-99.7,16.1],[-99.8,16.7],[-99.9,16.8],[-100.3,17.7],[-100.7,18.6]]);
    const winds=[185,241,269,269,259,157,74];
    for(let i=0;i<7;i++) {
      await evaluate(`document.querySelectorAll('.otis-position')[${i}].click()`);
      assert.ok((await evaluate('document.querySelector(".otis-track-card").textContent')).includes(winds[i]+' km/h'));
      assert.equal(await evaluate('document.querySelectorAll(".otis-popup").length'),1);
    }
    await evaluate('document.querySelector(".otis-landfall").click()');
    const text=await evaluate('document.querySelector(".otis-track-card").textContent');
    assert.ok(text.includes('25 de octubre de 2023 \u00b7 00:45 h de Acapulco'));
    assert.ok(text.includes('06:45 UTC'));
    assert.ok(text.includes('Centro estimado al tocar tierra'));
    assert.deepEqual(await evaluate('puntoCeroMap.getCenter().toArray().map(x=>Math.round(x*10)/10)'),[-99.9,16.8]);
    await evaluate('document.querySelector(".otis-popup").dispatchEvent(new KeyboardEvent("keydown",{key:"Escape",bubbles:true}))');
    assert.equal(await evaluate('document.querySelectorAll(".otis-popup").length'),0);
    // Switch the actual base map while retaining audio sources and the overlay.
    await evaluate('window.otisStyleRestored=false; puntoCeroMap.once("style.load",()=>{window.otisStyleRestored=true}); document.querySelector("[data-otis-base=positron]").click(); true');
    await waitFor('Boolean(window.otisStyleRestored && puntoCeroMap.getLayer("pc-otis-track-line"))','style restored');
    await waitFor('Boolean(puntoCeroMap.getSource("sounds"))','audio layers restored');
    assert.equal(await evaluate('document.querySelectorAll(".otis-track-control").length'),1);
    await evaluate('document.querySelector(".otis-toggle").click()');
    assert.equal(await evaluate('document.querySelectorAll(".otis-position").length'),0);
    assert.equal(await evaluate('puntoCeroMap.getLayoutProperty("pc-otis-track-line","visibility")'),'none');
    assert.equal(await evaluate('JSON.stringify(puntoCeroMap.getSource("sounds").serialize().data)===window.otisOriginalPoints'),true,'sound records untouched');
    const bounds=await evaluate('(()=>{let a=document.querySelector(".otis-toggle").getBoundingClientRect(),b=document.querySelector("#map-help-button").getBoundingClientRect();return {inside:a.left>=0&&a.right<=innerWidth,overlap:a.left<b.right&&a.right>b.left&&a.top<b.bottom&&a.bottom>b.top}})()');
    assert.equal(bounds.inside,true);assert.equal(bounds.overlap,false);
    results.push({width,positions:7,selection:true,landfall:true,hide:true,styleReload:true,soundRecordsUnchanged:true,controls:bounds});
  }
  assert.equal(exceptions.length,0,JSON.stringify(exceptions));
  console.log(JSON.stringify(results,null,2));
} finally { socket?.close(); chrome.kill(); }
