// Reusable single-shot barcode scanner for Banco POS (BL-89, hardened BL-90).
// Wraps the vendored html5-qrcode so every screen (counter sale, catalog
// create/edit, receiving) shares ONE scanner implementation instead of each
// copying ~50 lines. Rear camera, single-shot, RETAIL 1D formats + QR (our
// own labels for unbarcoded goods).
//
// BL-90 "scan once, known forever" hardening — two changes that stop the same
// item being captured under different / garbage barcodes:
//   1. RETAIL formats only (EAN/UPC). We dropped CODE_128/CODE_39/ITF because
//      packs print a second logistics/case code in those symbologies (and GS1
//      codes carry a \x1D group-separator) — the decoder was grabbing the WRONG
//      barcode off the same product.
//   2. STABLE read: a value is only accepted after it decodes IDENTICALLY twice
//      in a row. Kills partial/misreads that otherwise land on the first frame.
//
// Usage:
//   PosScanner.start('reader-id', text => {...}, err => {...}, {onProgress})
//   PosScanner.stop()          // always release on close/cancel/decode
//   PosScanner.beep()          // short audible confirm
//   onProgress(text)           // optional: each raw (unconfirmed) read — show it live
(function () {
  const SCAN_FORMATS = () => {
    const F = window.Html5QrcodeSupportedFormats;
    // Retail point-of-sale symbologies (manufacturer goods) PLUS QR_CODE for
    // the labels WE mint (shelf tags for unbarcoded items, our delivery slips).
    // Still NO CODE_128/CODE_39/ITF — those are the logistics/case codes that
    // caused duplicate captures (BL-90). QR is additive: EAN/UPC untouched.
    return [F.EAN_13, F.EAN_8, F.UPC_A, F.UPC_E, F.QR_CODE];
  };

  // A clean retail barcode is digits only (EAN/UPC). Reject anything with a
  // control char (e.g. GS1 \x1D group separator) or non-digit noise.
  const isCleanRetail = (text) => /^[0-9]{6,14}$/.test(text);
  // A QR payload is one we minted (a SKU/code/short URL) — accept any short,
  // printable string; reject empty or control-char garbage.
  const isCleanQr = (text) =>
    text.length >= 1 && text.length <= 512 && !/[\x00-\x08\x0e-\x1f]/.test(text);
  // html5-qrcode passes the matched format on the result; fall back to "looks
  // non-numeric => QR" when the structure isn't present.
  const isQrResult = (decoded, text) => {
    const fmt = decoded && decoded.result && decoded.result.format
      && decoded.result.format.formatName;
    if (fmt) return fmt === 'QR_CODE';
    return !/^[0-9]+$/.test(text);
  };

  window.PosScanner = {
    _scanner: null,
    _busy: false,
    _lastVal: null,        // last raw decode (for the 2-in-a-row stability gate)
    _lastCount: 0,

    async start(readerId, onDecode, onError, opts) {
      if (typeof window.Html5Qrcode === 'undefined') {
        onError && onError(new Error('scanner-not-loaded'));
        return;
      }
      this._busy = false;
      this._lastVal = null;
      this._lastCount = 0;
      const onProgress = opts && opts.onProgress;
      try {
        this._scanner = new window.Html5Qrcode(readerId, {
          formatsToSupport: SCAN_FORMATS(), verbose: false,
        });
        await this._scanner.start(
          { facingMode: 'environment' },                 // rear camera
          { fps: 10, qrbox: (vw) => {                     // wide box suits 1D codes
              const w = Math.max(160, Math.min(300, vw - 40));
              return { width: w, height: Math.floor(w * 0.55) };
          } },
          (raw, decoded) => {
            if (this._busy) return;                       // single-shot
            const text = (raw || '').trim();
            onProgress && onProgress(text);               // show what's being read
            // Retail codes must be clean digits; QR (our own labels) just needs
            // to be a sane printable payload.
            const ok = isQrResult(decoded, text) ? isCleanQr(text) : isCleanRetail(text);
            if (!ok) {                                    // ignore noise/logistics codes
              this._lastVal = null; this._lastCount = 0;
              return;
            }
            if (text === this._lastVal) {
              this._lastCount += 1;
            } else {
              this._lastVal = text; this._lastCount = 1;
            }
            if (this._lastCount < 2) return;              // need 2 identical in a row
            this._busy = true;                            // confirmed — accept
            this.stop().then(() => onDecode && onDecode(text));
          },
          () => { /* per-frame no-read: ignore */ }
        );
      } catch (err) {
        await this.stop();
        onError && onError(err);
      }
    },

    async stop() {
      if (!this._scanner) return;
      try {
        if (this._scanner.isScanning) await this._scanner.stop();
        await this._scanner.clear();
      } catch (e) { /* already stopped */ }
      this._scanner = null;
    },

    beep() {
      try {
        const Ctx = window.AudioContext || window.webkitAudioContext;
        if (!Ctx) return;
        const ctx = new Ctx();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'square';
        osc.frequency.value = 880;
        gain.gain.value = 0.1;
        osc.connect(gain); gain.connect(ctx.destination);
        osc.start();
        osc.stop(ctx.currentTime + 0.12);
        osc.onended = () => ctx.close();
      } catch (e) { /* no audio */ }
    },

    vibrate(ms) {
      try { navigator.vibrate && navigator.vibrate(ms || 60); } catch (e) {}
    },

    // No-camera fallback (desktop/laptop): decode a barcode from a still photo the
    // operator picked off disc. Same retail-format gate as the live scanner. Uses a
    // throwaway off-screen Html5Qrcode instance so it never disturbs the live one.
    // Returns the decoded text (string) or '' when nothing readable was found.
    async decodeFile(file) {
      if (typeof window.Html5Qrcode === 'undefined') throw new Error('scanner-not-loaded');
      const host = document.createElement('div');
      host.id = 'posscan-file-' + Date.now();
      // off-screen but with real layout (the lib draws to an internal canvas)
      host.style.cssText = 'position:fixed;left:-9999px;top:0;width:1px;height:1px;overflow:hidden;';
      document.body.appendChild(host);
      const inst = new window.Html5Qrcode(host.id, {
        formatsToSupport: SCAN_FORMATS(), verbose: false,
      });
      try {
        let text = '';
        try {
          const r = await inst.scanFileV2(file, false);
          text = (r && (r.decodedText || (r.result && r.result.text))) || '';
        } catch (e) {
          // Older API shape, or no code at full frame — try the plain scanFile.
          const r = await inst.scanFile(file, false);
          text = (typeof r === 'string') ? r : (r && r.decodedText) || '';
        }
        return (text || '').trim();
      } finally {
        try { await inst.clear(); } catch (e) { /* already gone */ }
        host.remove();
      }
    },
  };

  // Device hint for the file-input `capture` attribute. On a TOUCH device we keep
  // capture="environment" (go straight to the rear camera — the mobile behaviour we
  // want). On a desktop/laptop we DROP it so the input opens a normal file picker
  // (load from disc) instead of dead-ending on a missing camera.
  window.posIsTouchDevice = function () {
    try {
      return (navigator.maxTouchPoints || 0) > 0
        || /Mobi|Android|iPhone|iPad|iPod/i.test(navigator.userAgent || '');
    } catch (e) { return false; }
  };
  // Value to bind onto an <input type=file :capture="...">: 'environment' or false.
  window.posCaptureAttr = function () {
    return window.posIsTouchDevice() ? 'environment' : false;
  };
})();

// ---------------------------------------------------------------------------
// BL: webcam PHOTO capture (getUserMedia) — for the AI snap-fill / product photo
// on a LAPTOP, where the <input type=file capture> just opens the file dialog
// (desktop browsers ignore `capture`). Self-contained overlay, no framework.
// window.PosCameraPhoto.capture() -> Promise<File|null> (JPEG) — null on cancel/no-cam.
// ---------------------------------------------------------------------------
(function () {
  window.PosCameraPhoto = {
    async capture() {
      const md = navigator.mediaDevices;
      if (!md || !md.getUserMedia) { alert('This browser has no camera access.'); return null; }
      let stream;
      try { stream = await md.getUserMedia({ video: { facingMode: 'environment' }, audio: false }); }
      catch (e) {
        try { stream = await md.getUserMedia({ video: true, audio: false }); }
        catch (e2) { alert('No camera available (or permission denied).'); return null; }
      }
      return await new Promise((resolve) => {
        const ov = document.createElement('div');
        ov.style.cssText = 'position:fixed;inset:0;z-index:99999;background:#000;display:flex;' +
          'flex-direction:column;align-items:center;justify-content:center;gap:18px;padding:16px;';
        const video = document.createElement('video');
        video.autoplay = true; video.playsInline = true; video.muted = true; video.srcObject = stream;
        video.style.cssText = 'max-width:100%;max-height:72vh;border-radius:12px;background:#111;';
        const bar = document.createElement('div');
        bar.style.cssText = 'display:flex;gap:16px;align-items:center;';
        const snap = document.createElement('button');
        snap.textContent = '📸 Snap';
        snap.style.cssText = 'padding:15px 34px;font-size:18px;font-weight:800;border:none;border-radius:14px;' +
          'background:#10b981;color:#04231a;cursor:pointer;box-shadow:0 4px 14px rgba(0,0,0,.3);';
        const cancel = document.createElement('button');
        cancel.textContent = '✕';
        cancel.style.cssText = 'padding:15px 22px;font-size:18px;border:none;border-radius:14px;' +
          'background:rgba(255,255,255,.15);color:#fff;cursor:pointer;';
        bar.appendChild(snap); bar.appendChild(cancel);
        ov.appendChild(video); ov.appendChild(bar);
        document.body.appendChild(ov);
        const cleanup = () => { try { stream.getTracks().forEach(t => t.stop()); } catch (e) {} ov.remove(); };
        cancel.onclick = () => { cleanup(); resolve(null); };
        snap.onclick = () => {
          const c = document.createElement('canvas');
          c.width = video.videoWidth || 1280; c.height = video.videoHeight || 720;
          c.getContext('2d').drawImage(video, 0, 0, c.width, c.height);
          c.toBlob((blob) => {
            cleanup();
            resolve(blob ? new File([blob], 'webcam-' + Date.now() + '.jpg', { type: 'image/jpeg' }) : null);
          }, 'image/jpeg', 0.9);
        };
      });
    },
  };
})();
