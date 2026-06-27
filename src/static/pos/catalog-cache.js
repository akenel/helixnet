/**
 * Banco POS — Offline Catalog Cache (P1: read-offline)
 *
 * A tiny, dependency-free IndexedDB mirror of the SELLABLE catalog so the till can
 * still scan, search and PRICE goods when the network drops. P1 is READ-only: you can
 * build the cart offline from cached prices; FINALISING the sale still needs the server
 * (that's P2, the outbox). The online path stays authoritative — the cache is only ever
 * a fallback when fetch() can't reach the server.
 *
 * Public API (all async, all safe to call even where IndexedDB is unavailable):
 *   CatalogCache.available()         -> bool
 *   CatalogCache.sync()              -> {count, at} | null   (pull /products when online)
 *   CatalogCache.put(product)        -> void                 (warm the cache with a seen item)
 *   CatalogCache.findByBarcode(code) -> product | null       (primary barcode; aliases = P1.2)
 *   CatalogCache.search(q)           -> [product]            (name / sku / category contains)
 *   CatalogCache.meta()              -> {count, at} | null   (last sync stamp)
 *
 * Bump nothing here on catalog changes — sync() always clears + reloads from the server.
 */
(function () {
  'use strict';
  var DB = 'banco-pos', STORE = 'products', META = 'meta', VER = 1;

  function available() {
    try { return typeof indexedDB !== 'undefined' && indexedDB !== null; }
    catch (e) { return false; }
  }

  function open() {
    return new Promise(function (res, rej) {
      var r = indexedDB.open(DB, VER);
      r.onupgradeneeded = function () {
        var db = r.result;
        if (!db.objectStoreNames.contains(STORE)) {
          var s = db.createObjectStore(STORE, { keyPath: 'id' });
          s.createIndex('barcode', 'barcode', { unique: false });
        }
        if (!db.objectStoreNames.contains(META)) {
          db.createObjectStore(META, { keyPath: 'k' });
        }
      };
      r.onsuccess = function () { res(r.result); };
      r.onerror = function () { rej(r.error); };
    });
  }

  function token() {
    try { return (window.AuthHelper && AuthHelper.getToken && AuthHelper.getToken()) || null; }
    catch (e) { return null; }
  }

  var CatalogCache = {
    available: available,

    // Pull the whole sellable catalog (it's small — tens to low hundreds) and replace the
    // local mirror atomically. No-op (returns null) offline / unauth / no IndexedDB.
    sync: function () {
      if (!available()) return Promise.resolve(null);
      var tok = token();
      if (!tok) return Promise.resolve(null);
      return fetch('/api/v1/pos/products?limit=1000&active_only=true', {
        headers: { 'Authorization': 'Bearer ' + tok }
      }).then(function (res) {
        if (!res.ok) throw new Error('catalog sync HTTP ' + res.status);
        return res.json();
      }).then(function (list) {
        if (!Array.isArray(list)) list = [];
        return open().then(function (db) {
          return new Promise(function (resolve, reject) {
            var t = db.transaction(STORE, 'readwrite');
            var s = t.objectStore(STORE);
            s.clear();
            list.forEach(function (p) { if (p && p.id) s.put(p); });
            t.oncomplete = function () { resolve(); };
            t.onerror = function () { reject(t.error); };
          }).then(function () {
            var at = Date.now();
            return CatalogCache._setMeta({ k: 'sync', count: list.length, at: at })
              .then(function () { return { count: list.length, at: at }; });
          });
        });
      });
    },

    // Keep the mirror warm: every product the till actually touches online gets cached, so
    // a freshly-scanned item is available offline even before the next full sync.
    put: function (p) {
      if (!available() || !p || !p.id) return Promise.resolve();
      return open().then(function (db) {
        return new Promise(function (resolve) {
          var t = db.transaction(STORE, 'readwrite');
          t.objectStore(STORE).put(p);
          t.oncomplete = function () { resolve(); };
          t.onerror = function () { resolve(); };
        });
      }).catch(function () {});
    },

    findByBarcode: function (code) {
      if (!available() || !code) return Promise.resolve(null);
      return open().then(function (db) {
        return new Promise(function (resolve) {
          var idx = db.transaction(STORE, 'readonly').objectStore(STORE).index('barcode');
          var r = idx.get(String(code));
          r.onsuccess = function () { resolve(r.result || null); };
          r.onerror = function () { resolve(null); };
        });
      }).catch(function () { return null; });
    },

    search: function (q) {
      if (!available() || !q) return Promise.resolve([]);
      var needle = String(q).trim().toLowerCase();
      if (!needle) return Promise.resolve([]);
      return open().then(function (db) {
        return new Promise(function (resolve) {
          var out = [];
          var cur = db.transaction(STORE, 'readonly').objectStore(STORE).openCursor();
          cur.onsuccess = function (e) {
            var c = e.target.result;
            if (!c) { resolve(out); return; }
            var p = c.value, hay = ((p.name || '') + ' ' + (p.sku || '') + ' ' + (p.category || '')).toLowerCase();
            if (hay.indexOf(needle) !== -1 && out.length < 50) out.push(p);
            c.continue();
          };
          cur.onerror = function () { resolve(out); };
        });
      }).catch(function () { return []; });
    },

    meta: function () {
      if (!available()) return Promise.resolve(null);
      return open().then(function (db) {
        return new Promise(function (resolve) {
          var r = db.transaction(META, 'readonly').objectStore(META).get('sync');
          r.onsuccess = function () { resolve(r.result || null); };
          r.onerror = function () { resolve(null); };
        });
      }).catch(function () { return null; });
    },

    _setMeta: function (o) {
      return open().then(function (db) {
        return new Promise(function (resolve) {
          var t = db.transaction(META, 'readwrite');
          t.objectStore(META).put(o);
          t.oncomplete = function () { resolve(); };
          t.onerror = function () { resolve(); };
        });
      }).catch(function () {});
    }
  };

  window.CatalogCache = CatalogCache;
})();
