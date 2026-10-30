/* voice.js — natural-voice clips for the site's 🔊 buttons.
 *
 * Drop-in: every page already speaks through speechSynthesis.speak(). This
 * wraps speak() / cancel() so that an utterance whose text has a generated
 * clip (tools/gen_en_audio.py) plays that mp3 instead of the robotic device
 * voice. Anything without a clip — or before the manifest has loaded — goes
 * to the device voice exactly as before, so a button is never silent and no
 * page needs any other change.
 *
 *   clips     /audio/en/<hash>.mp3        R2, immutable
 *   manifest  /audio/manifest/<site>.json  text -> hash, one per school
 *
 * The page's own onstart / onend / onerror handlers still fire, so "Play the
 * whole conversation" chains and is-speaking highlights keep working.
 */
(function () {
  var synth = window.speechSynthesis;
  if (!synth || !window.Audio || !window.fetch || synth.__chbVoice) return;
  synth.__chbVoice = true;

  var CLIPS = '/audio/en/', MANIFESTS = '/audio/manifest/';
  var CLIP_RATE = 0.92;   // clips are generated at -8% (RATE in gen_en_audio.py)

  // /schools/<slug>/… -> slug; /resources/… -> resources; must match site_of()
  var m = location.pathname.match(/^\/(?:schools\/)?([^\/]+)\//);
  var manifest = null;
  fetch(MANIFESTS + (m ? m[1] : 'home') + '.json')
    .then(function (r) { return r.ok ? r.json() : {}; })
    .then(function (j) { manifest = j; }, function () { manifest = {}; });

  // One shared element: iOS only lets an element play without a fresh tap once
  // a tap has started it, and chained lines start from the previous 'ended'.
  var audio = new Audio();
  audio.preload = 'auto';

  var deviceSpeak = synth.speak.bind(synth), deviceCancel = synth.cancel.bind(synth);
  var queue = [], cur = null, curIsClip = false;

  // must match key() in gen_en_audio.py
  function key(t) { return String(t || '').replace(/\s+/g, ' ').trim(); }

  function fire(u, type, error) {
    var e = new Event(type);
    e.utterance = u; e.charIndex = 0; e.elapsedTime = 0;
    if (error) e.error = error;
    u.dispatchEvent(e);
  }

  function next() { cur = null; curIsClip = false; run(); }

  function device(u) {
    cur = u; curIsClip = false;
    var after = function () {
      u.removeEventListener('end', after); u.removeEventListener('error', after);
      if (cur === u) next();
    };
    u.addEventListener('end', after); u.addEventListener('error', after);
    deviceSpeak(u);
  }

  function run() {
    if (cur || !queue.length) return;
    var u = queue.shift();
    var h = manifest && manifest[key(u.text)];
    if (!h) return device(u);

    cur = u; curIsClip = true;
    // Pages slow the robot voice down with u.rate (0.82–0.92); the clips are
    // already a little slow, so only the difference is applied.
    var rate = Math.min(1.1, Math.max(0.7, (u.rate || 1) / CLIP_RATE));
    audio.defaultPlaybackRate = rate;   // a new src resets playbackRate to this
    audio.src = CLIPS + h + '.mp3';
    audio.playbackRate = rate;
    audio.volume = u.volume >= 0 && u.volume <= 1 ? u.volume : 1;
    audio.onended = function () { if (cur === u) { next(); fire(u, 'end'); } };
    // Clip missing or blocked: say it with the device voice instead. Both the
    // error event and the play() promise report a 404, hence the curIsClip
    // check — device() clears it, so the line is only said once.
    var fallback = function () { if (cur === u && curIsClip) device(u); };
    audio.onerror = fallback;
    var p = audio.play();
    if (p && p.catch) p.catch(function (e) { if (e.name !== 'AbortError') fallback(); });
    fire(u, 'start');
  }

  synth.speak = function (u) {
    if (!u || typeof u.text !== 'string') return deviceSpeak(u);
    queue.push(u);
    run();
  };

  synth.cancel = function () {
    var u = cur, wasClip = curIsClip;
    queue.length = 0; cur = null; curIsClip = false;
    audio.onended = audio.onerror = null;
    audio.pause();
    deviceCancel();
    // The device voice reports cut-off speech a moment later, which is how
    // pages reset their buttons; do the same for a clip. Pages that only set
    // onend get 'end', so their highlight still clears.
    if (u && wasClip) setTimeout(function () {
      if (u.onerror) fire(u, 'error', 'interrupted'); else fire(u, 'end');
    }, 0);
  };
})();
