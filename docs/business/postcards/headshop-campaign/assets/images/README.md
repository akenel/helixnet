# Card images

Drop your card artwork here (PNG/JPG/SVG). Idea: each card in the sequence can carry
its own picture — a strong visual on the front that fits the head-shop, rebel aesthetic.

Naming: `card-<n>-<shortname>.<ext>`  e.g. `card-1-tiger.png`

Once the images are in, we wire an `{{IMG_SRC}}` field into the templates (same pattern
as `{{QR_SRC}}`) so each card renders with its picture. SVG prints razor-sharp; raster is
fine at 300dpi+ for the print size (A6, 148×105 mm).
