// Reusable single-shot barcode scanner for Banco POS (BL-89).
// Wraps the vendored html5-qrcode so multiple screens (counter sale, catalog
// create/edit, future receiving) share ONE scanner implementation instead of
// each copying ~50 lines. Retail 1D formats only, rear camera, single-shot.
//
// Usage:
//   PosScanner.start('reader-id', text => { ... }, err => { ... })
//   PosScanner.stop()          // always release on close/cancel/decode
//   PosScanner.beep()          // short audible confirm
(function () {
  const RETAIL_FORMATS = () => {
    const F = window.Html5QrcodeSupportedFormats;
    return [F.EAN_13, F.EAN_8, F.UPC_A, F.UPC_E, F.CODE_128, F.CODE_39, F.ITF];
  };

  window.PosScanner = {
    _scanner: null,
    _busy: false,

    async start(readerId, onDecode, onError) {
      if (typeof window.Html5Qrcode === 'undefined') {
        onError && onError(new Error('scanner-not-loaded'));
        return;
      }
      this._busy = false;
      try {
        this._scanner = new window.Html5Qrcode(readerId, {
          formatsToSupport: RETAIL_FORMATS(), verbose: false,
        });
        await this._scanner.start(
          { facingMode: 'environment' },                 // rear camera
          { fps: 10, qrbox: (vw) => {                     // wide box suits 1D codes
              const w = Math.max(160, Math.min(300, vw - 40));
              return { width: w, height: Math.floor(w * 0.55) };
          } },
          (text) => {
            if (this._busy) return;                       // single-shot
            this._busy = true;
            this.stop().then(() => onDecode && onDecode((text || '').trim()));
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
