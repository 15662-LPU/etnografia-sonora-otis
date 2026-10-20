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
  for(const width of [390,1280]) {
    await send('Emulation.setDeviceMetricsOverride',{width,height:844,deviceScaleFactor:1,mobile:width<768},sessionId);
    await send('Page.navigate',{url:baseUrl},sessionId);
    await waitFor('Boolean(document.querySelector("#cover-enter"))','entry');
    await evaluate('document.querySelector("#cover-enter").click()');
    await waitFor('Boolean(document.querySelector(".otis-satellite-button"))','satellite control');

    assert.equal(await evaluate('document.querySelector("#otis-satellite-dialog video").hasAttribute("src")'),false);
    const before=requests.filter(x=>x.includes('otis-goes18-720p.mp4')).length;
    await evaluate('document.querySelector(".otis-satellite-button").click()');
    const state=await evaluate('(()=>{let d=document.querySelector("#otis-satellite-dialog"),v=d.querySelector("video"),b=d.getBoundingClientRect();return {open:d.open,paused:v.paused,preload:v.preload,controls:v.controls,autoplay:v.autoplay,fit:getComputedStyle(v).objectFit,inside:b.left>=0&&b.right<=innerWidth&&b.top>=0&&b.bottom<=innerHeight}})()');
    assert.deepEqual(state,{open:true,paused:true,preload:'none',controls:true,autoplay:false,fit:'contain',inside:true});
    await sleep(500);
    assert.equal(requests.filter(x=>x.includes('otis-goes18-720p.mp4')).length,before,'no video download before play');
    await evaluate('document.querySelector("#otis-satellite-dialog video").play().then(()=>true)');
    await waitFor('document.querySelector("#otis-satellite-dialog video").currentTime>0','playback');
    assert.equal(await evaluate('document.querySelector("#otis-satellite-dialog video").videoWidth'),1280);
    await evaluate('document.querySelector("#otis-satellite-dialog video").currentTime=12; true');
    await waitFor('document.querySelector("#otis-satellite-dialog video").currentTime>=12','seeking');
    await evaluate('document.querySelector(".otis-satellite-close").click()');
    await waitFor('document.activeElement===document.querySelector(".otis-satellite-button")','focus');
    assert.equal(await evaluate('document.querySelector("#otis-satellite-dialog video").paused'),true);
    await evaluate('document.querySelector(".otis-satellite-button").click()');
    await send('Input.dispatchKeyEvent',{type:'keyDown',key:'Escape',code:'Escape',windowsVirtualKeyCode:27},sessionId);
    await send('Input.dispatchKeyEvent',{type:'keyUp',key:'Escape',code:'Escape',windowsVirtualKeyCode:27},sessionId);
    await waitFor('!document.querySelector("#otis-satellite-dialog").open','Escape');
    assert.equal(await evaluate('document.activeElement===document.querySelector(".otis-satellite-button")'),true);
    results.push({width,...state,playback:true,seeking:true,close:true,escape:true,focusRestored:true,noInitialDownload:true});

  }
  assert.equal(exceptions.length,0,JSON.stringify(exceptions));
  console.log(JSON.stringify({results},null,2));
} finally {socket?.close();chrome.kill();}
