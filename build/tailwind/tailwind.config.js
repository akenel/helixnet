/** Banco POS — real Tailwind v3 build (replaces the in-browser Play CDN engine).
 *  content scans every template + JS file so the JIT-in-browser classes (incl. the
 *  literal class strings in Alpine :class="..." and JS return values) are all emitted.
 *  Broad globs on purpose: a slightly larger CSS beats a silently-purged class. */
module.exports = {
  content: [
    './src/templates/**/*.html',
    './src/static/**/*.js',
  ],
  theme: { extend: {} },   // POS uses the stock palette; custom colors are plain CSS vars
  plugins: [],
};
