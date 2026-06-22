"""
Pure unit tests for the image intake pipeline. No DB, no HTTP, no network --
builds images in memory with Pillow and checks the transform, so these run on
the host .venv in milliseconds.

LOCKS the promises we make about a phone photo before it's stored or read:
  - rotated (EXIF) photos come out upright
  - oversized photos are downscaled to the preset's long edge (never upscaled)
  - the thumbnail is a centered square
  - transparency is flattened onto white (JPEG has no alpha)
  - output carries no EXIF, and is smaller than a big original
  - junk bytes raise ImageIntakeError, not a 500
"""
import sys
from io import BytesIO
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.services.image_intake import (  # noqa: E402
    PRODUCT, SLIP, IntakePreset, ImageIntakeError, process,
)


def _png_bytes(w, h, color=(120, 30, 30)):
    buf = BytesIO()
    Image.new("RGB", (w, h), color).save(buf, format="PNG")
    return buf.getvalue()


def _decode(b):
    return Image.open(BytesIO(b))


def test_downscales_oversized_to_long_edge():
    out = process(_png_bytes(4000, 3000), PRODUCT)  # 12 MP phone shot
    assert max(out.width, out.height) == PRODUCT.max_edge == 1024
    assert out.height == 768                          # 4:3 aspect preserved
    img = _decode(out.main)
    assert img.format == "JPEG"


def test_never_upscales_small_image():
    small = _png_bytes(300, 200)
    out = process(small, PRODUCT)
    assert (out.width, out.height) == (300, 200)      # left as-is, not blown up


def test_thumbnail_is_centered_square():
    out = process(_png_bytes(4000, 1000), PRODUCT)    # very wide → must crop, not squash
    assert out.thumb is not None
    thumb = _decode(out.thumb)
    assert thumb.size == (PRODUCT.thumb_px, PRODUCT.thumb_px) == (256, 256)


def test_slip_preset_has_no_thumbnail_and_bigger_edge():
    out = process(_png_bytes(4000, 3000), SLIP)
    assert out.thumb is None
    assert max(out.width, out.height) == SLIP.max_edge == 1600


def test_exif_rotation_is_baked_in_upright():
    # A 200x100 landscape image tagged "rotate 90° CW" should emerge 100x200.
    base = Image.new("RGB", (200, 100), (10, 80, 10))
    exif = base.getexif()
    exif[0x0112] = 6                                   # Orientation = 6 (rotate 90° CW)
    buf = BytesIO()
    base.save(buf, format="JPEG", exif=exif)

    out = process(buf.getvalue(), IntakePreset(max_edge=4000, thumb_px=0))
    assert (out.width, out.height) == (100, 200)       # transposed upright
    # ...and the orientation tag is gone (EXIF stripped on re-encode).
    assert 0x0112 not in _decode(out.main).getexif()


def test_transparency_flattened_to_white():
    buf = BytesIO()
    Image.new("RGBA", (100, 100), (0, 0, 0, 0)).save(buf, format="PNG")  # fully transparent
    out = process(buf.getvalue(), IntakePreset(max_edge=100, thumb_px=0, enhance=False))
    img = _decode(out.main).convert("RGB")
    assert img.mode == "RGB"
    assert img.getpixel((50, 50)) == (255, 255, 255)   # composited onto white


def test_shrinks_a_big_original():
    big = _png_bytes(4000, 3000)
    out = process(big, PRODUCT)
    assert out.out_bytes < out.orig_bytes
    assert out.shrunk_pct > 0


def test_bad_bytes_raise_intake_error():
    for junk in (b"", b"not an image at all", b"\x89PNG\r\n\x1a\n broken"):
        try:
            process(junk, PRODUCT)
            assert False, f"expected ImageIntakeError for {junk!r}"
        except ImageIntakeError:
            pass
