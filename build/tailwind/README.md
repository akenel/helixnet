# Banco POS — Tailwind build

The POS used the in-browser Tailwind **Play CDN engine** (`/static/vendor/tailwind.js`, 451 KB) which
compiled CSS at runtime on every page load and printed *"cdn.tailwindcss.com should not be used in
production"*. This is the real compiled build that replaces it.

- **Input:** `build/tailwind/input.css` (`@tailwind base/components/utilities`)
- **Config:** `build/tailwind/tailwind.config.js` — `content` scans **all** templates + JS so every
  class (including the literal strings in Alpine `:class="..."` and JS return values) is emitted.
- **Output:** `src/static/pos/tailwind.css` (committed — the box deploys by git-pull, no build step).
- **Loaded by:** `src/templates/pos/base.html` → `<link ... /static/pos/tailwind.css>`.

## Rebuild (after adding/removing classes)
```
make tailwind        # or: npx tailwindcss@3.4.17 -c build/tailwind/tailwind.config.js \
                     #        -i build/tailwind/input.css -o src/static/pos/tailwind.css --minify
```
Then **bump the `?v=` on the link in pos/base.html** and the sw.js CACHE_NAME so clients refetch.

## Safety note (rule 9)
A static build only sees classes that appear as **literal tokens** in scanned files. This repo has
**zero** concatenated classes (`'bg-'+x`), so scanning is complete. If you ever add one, **safelist** it
in the config, or the class is silently purged. Verify coverage: compare class tokens in the templates
against the compiled CSS before shipping.
