import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { webcrypto } from 'node:crypto';
import vm from 'node:vm';
import test from 'node:test';

const root = new URL('../', import.meta.url);
const source = readFileSync(new URL('map-core.js', root), 'utf8');
const manifest = JSON.parse(readFileSync(new URL('data/audio-fingerprints.json', root), 'utf8'));
// Public audit fixture includes only fields needed to reproduce map publication.
const auditPath = process.env.AUDIO_AUDIT_PATH || new URL('tests/fixtures/approved-audio-20261014.json', root);
const names = ['normalizeSoundKey', 'getSoundPieceKey', 'dedupeSoundPoints',
  'countUniqueSoundPieces', 'publicLocation', 'approvedAudioStorageKey',
  'loadApprovedAudioFingerprintManifest', 'fingerprintApprovedAudio',
  'fingerprintApprovedRows', 'sortApprovedRowsForPublication',
  'publicCoordinateOrNull', 'approvedRowToPoint', 'loadApprovedTestimonies'];

function harness(rows = [], files = {}) {
  let downloads = 0;
  const context = {
    window: { crypto: webcrypto }, console: { warn() {} }, AbortSignal,
    SUPABASE_BUCKET: 'testimonios-audio', SOUND_POINTS: [], BASE_SOUND_POINT_COUNT: 0,
    approvedAudioFingerprintCache: Object.create(null),
    normalizeAudioPath: path => String(path || '').replace(/^\/+/, ''),
    updateHeroSoundCount() {},
    supabaseFetch: async () => ({ ok: true, json: async () => structuredClone(rows) }),
    createSignedAudioUrl: async (bucket, path) => path,
    fetch: async url => {
      if (url.startsWith('data/audio-fingerprints.json')) return { ok: true, json: async () => manifest };
      downloads++;
      if (!Object.hasOwn(files, url)) throw new Error('unreadable audio');
      const buffer = Buffer.from(files[url]);
      return { ok: true, arrayBuffer: async () => buffer.buffer.slice(buffer.byteOffset, buffer.byteOffset + buffer.byteLength) };
    }
  };
  vm.createContext(context);
  for (const name of names) {
    const start = source.search(new RegExp('(?:async )?function ' + name + '\\('));
    assert.ok(start >= 0, name);
    const end = source.indexOf('\n}', start) + 2;
    vm.runInContext(source.slice(start, end), context, { filename: fileURLToPath(new URL('map-core.js', root)) });
  }
  return { context, downloads: () => downloads };
}

function row(id, path, latitude = 16.88, longitude = -99.87) {
  return { id, status: 'approved', audio_bucket: 'testimonios-audio',
    audio_path: path, audio_size_bytes: 4, latitude, longitude, curated_at: '2026-10-14' };
}

test('same bytes under different filenames and routes produce one map point', async () => {
  const { context, downloads } = harness([row('b', 'new/one.m4a'), row('a', 'new/two.wav')],
    { 'new/one.m4a': 'same', 'new/two.wav': 'same' });
  const points = await context.loadApprovedTestimonies();
  assert.equal(points.length, 1);
  assert.equal(points[0].approved_submission_id, 'a');
  assert.equal(context.window.PUNTO_CERO_AUDIO_DUPLICATES.length, 1);
  assert.equal(downloads(), 2);
  await context.loadApprovedTestimonies();
  assert.equal(downloads(), 2, 'refresh reuses verified session hashes');
});

test('different contents with the same generic filename remain separate', async () => {
  const { context } = harness([row('a', 'a/historia.wav'), row('b', 'b/historia.wav')],
    { 'a/historia.wav': 'aaaa', 'b/historia.wav': 'bbbb' });
  assert.equal((await context.loadApprovedTestimonies()).length, 2);
});

test('null, blank and out-of-range coordinates are omitted; valid zero is preserved', () => {
  const { context } = harness();
  for (const [lat, lng] of [[null, null], ['', -99], [16, ' '], [91, -99], [16, -181], ['bad', -99]]) {
    assert.equal(context.approvedRowToPoint({ ...row('a', 'a', lat, lng), _verified_audio_sha256: 'hash' }), null);
  }
  assert.equal(context.approvedRowToPoint({ ...row('a', 'a', 0, 0), _verified_audio_sha256: 'hash' }).coords.join(','), '0,0');
});

test('unverified files stay off the map and are retried after read failure', async () => {
  const files = {};
  const { context } = harness([row('a', 'new/a.wav')], files);
  assert.equal((await context.loadApprovedTestimonies()).length, 0);
  assert.equal(context.window.PUNTO_CERO_UNVERIFIED_AUDIO_IDS[0], 'a');
  files['new/a.wav'] = 'aaaa';
  assert.equal((await context.loadApprovedTestimonies()).length, 1);
});

test('changed file sizes invalidate the precomputed fingerprint', async () => {
  const key = Object.keys(manifest.files)[0];
  const path = key.slice('testimonios-audio/'.length);
  const { context, downloads } = harness([row('replacement', path)], { [path]: 'changed' });
  await context.loadApprovedTestimonies();
  assert.equal(downloads(), 1);
});

test('case-sensitive Spotify IDs and storage paths remain distinct', () => {
  const { context } = harness();
  const points = context.dedupeSoundPoints([
    { id: 1, spotify: 'https://open.spotify.com/episode/AbC?si=1' },
    { id: 2, spotify: 'https://open.spotify.com/embed/episode/AbC?si=2' },
    { id: 3, spotify: 'https://open.spotify.com/episode/abc' },
    { id: 4, audio_path: 'Pending/A.wav' }, { id: 5, audio_path: 'pending/a.wav' }
  ], 'test');
  assert.equal(points.length, 4);
});

test('public corpus keeps 19 valid unique testimonies, including Cacahuatepec', async () => {
  const rows = JSON.parse(readFileSync(auditPath, 'utf8'));
  const { context, downloads } = harness(rows.reverse());
  const points = await context.loadApprovedTestimonies();
  assert.equal(points.length, 19);
  assert.equal(downloads(), 0, 'existing corpus requires no audio downloads');
  assert.equal(new Set(points.map(p => p.audio_sha256)).size, points.length);
  const ids = new Set(points.map(p => p.approved_submission_id));
  for (const id of ['397cd3a0-382b-43ab-965b-ed19028a46be', '00ced058-392a-4c4d-9b3d-efcb8227e724', '432871f9-2d90-4d89-bed8-c5488a838823']) assert.ok(ids.has(id));
  for (const id of ['a971be2d-10f2-452f-916a-4c0a635820f6', '2e9b48f3-266c-485e-970f-c3a0f580797c', '4e7c55c7-f109-45ba-881a-97529eff38c4']) assert.ok(!ids.has(id));
  assert.equal(context.window.PUNTO_CERO_AUDIO_DUPLICATES.length, 3);
  assert.equal(context.countUniqueSoundPieces(points), 19);
});
