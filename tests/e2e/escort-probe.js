// escort-probe — exercise the GUARANTEED-CARD path end-to-end over HTTP, on a real env.
//
//   1) POST /get-started   -> a member is born WITH a card (the primary door; _provision_card born path)
//   2) POST /me/setup-card  -> SAME member, now carded -> {already:true} (the escort endpoint + idempotent guard)
//
// Why this covers the escort: both doors call the ONE function `_provision_card`. Step 1 proves the
// born path runs on the live box. Step 2 proves the escort endpoint authenticates, doesn't 500, and
// refuses to mint a second card. The only branch left for a human is the escort's born path reached
// via a truly cardless social login — that's the new-user runbook's job.
//
// Usage: node tests/e2e/escort-probe.js [staging|prod|local]   (default: staging)
// Note: creates one throwaway member on the target (escort.probe+<stamp>@…). Fine on staging (demo env).
process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';
const TARGET = process.argv[2] || 'staging';
const HOSTS = {
  staging: 'https://staging-bottega.lapiazza.app',
  prod:    'https://bottega.lapiazza.app',
  local:   'https://helix.local',
};
const BASE = HOSTS[TARGET];
if (!BASE) { console.error('unknown target', TARGET); process.exit(2); }
const API = BASE + '/api/v1/compute/bottega';   // the bottega router's mount prefix

let fails = 0;
const ok = (c, m) => { console.log(`  ${c ? '✅' : '❌'} ${m}`); if (!c) fails++; };
const form = (o) => new URLSearchParams(o);

(async () => {
  console.log(`\n════ ESCORT PROBE — ${TARGET} (${BASE}) ════\n`);
  const stamp = Date.now();
  const email = `escort.probe+${stamp}@example.com`;
  const name  = `Escort Probe ${stamp}`;
  const about = 'I build bridges between enterprise systems and tend a small garden of automated tests.';

  // 1 · primary door — born WITH a card
  console.log('— 1 · /get-started (member born with a card) —');
  let token = null;
  try {
    const r = await fetch(`${API}/get-started`, { method: 'POST', body: form({
      name, email, password: 'probe_pass_123', about, tos_accepted: '1', age_confirmed: '1',
    })});
    const j = await r.json().catch(() => ({}));
    ok(r.status === 200, `status 200 (got ${r.status})`);
    ok(!!j.token, 'returned an auto-login token');
    ok(!!(j.profile && j.profile.bio), 'card born: profile.bio populated by _provision_card');
    token = j.token;
    if (j.profile) console.log(`        slug=${j.slug}  tagline="${(j.profile.tagline || '').slice(0, 60)}"`);
  } catch (e) { ok(false, 'get-started threw: ' + e.message); }

  // 2 · the escort endpoint — same (now-carded) member -> idempotent guard
  console.log('\n— 2 · /me/setup-card (escort endpoint + idempotent guard) —');
  if (!token) { ok(false, 'no token from step 1 — cannot probe escort'); }
  else {
    try {
      const r = await fetch(`${API}/me/setup-card`, {
        method: 'POST',
        headers: { Authorization: 'Bearer ' + token },
        body: form({ about }),
      });
      const j = await r.json().catch(() => ({}));
      ok(r.status === 200, `status 200, no 500 (got ${r.status})`);
      ok(j.already === true, 'idempotent: already-carded member -> {already:true} (no duplicate card)');
      ok(!!(j.profile && j.profile.slug), 'escort returns the existing card');
    } catch (e) { ok(false, 'setup-card threw: ' + e.message); }
  }

  console.log(`\n════ ${fails} failure(s) ════`);
  console.log(fails ? '🔴 escort probe failed' : '🟢 escort path verified (born + idempotent guard)');
  process.exit(fails ? 1 : 0);
})();
