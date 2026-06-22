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
  };
})();
