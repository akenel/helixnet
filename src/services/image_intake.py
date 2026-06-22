"""
Image intake — standardize a photo someone snapped on their phone.

A phone shot is big (4-12 MP, several MB), often rotated sideways by EXIF, and
inconsistently lit. Before we store it as a product picture or hand it to the
slip-reader (the VLM), we run it through ONE pipeline so everything downstream
gets a clean, predictable image:

    orient (honor EXIF rotation)
      -> downscale (cap the long edge)
      -> enhance (autocontrast + a touch of sharpen — "make up the difference")
      -> encode JPEG, EXIF stripped
      -> (optional) a centered square thumbnail for the catalog grid

This module is a PURE transform: bytes in, bytes out. No FastAPI, no MinIO, no
DB — storage and routing are the caller's job, so this is trivially unit-tested.

Two presets cover today's needs:
  PRODUCT — catalog photo: 1024px long edge + a 256px square thumbnail.
  SLIP    — delivery note headed for the VLM: 1600px long edge, no thumbnail.
            Downscaling here also makes the Turbo read faster and cheaper.

Rule #11 (Python first) — Pillow, deterministic, no model needed.
"""
from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

from PIL import Image, ImageEnhance, ImageOps

# Pillow 10 renamed the resample enum; LANCZOS is the high-quality downsample.
_LANCZOS = Image.Resampling.LANCZOS


@dataclass(frozen=True)
class IntakePreset:
    """How hard to shrink, whether to enhance, and the thumbnail size."""
    max_edge: int           # cap the LONGER side to this many px (aspect kept)
    thumb_px: int           # square thumbnail edge in px; 0 = no thumbnail
    enhance: bool = True     # autocontrast + mild sharpen
    quality: int = 85        # JPEG quality


# Catalog product photo: a tidy main image + a square thumb for the grid.
PRODUCT = IntakePreset(max_edge=1024, thumb_px=256, enhance=True)

# Delivery slip headed for the VLM: keep more detail for OCR, no thumbnail.
SLIP = IntakePreset(max_edge=1600, thumb_px=0, enhance=True)


@dataclass(frozen=True)
class IntakeResult:
    """Standardized bytes plus the numbers worth logging."""
    main: bytes                 # the processed image (JPEG)
    thumb: bytes | None         # square thumbnail (JPEG), or None
    content_type: str           # always "image/jpeg" for now
    width: int                  # main image dimensions after processing
    height: int
    orig_bytes: int             # what came in
    out_bytes: int              # the main image after processing

    @property
    def shrunk_pct(self) -> int:
        """How much smaller the main image is than the original, as a percent."""
        if not self.orig_bytes:
            return 0
        return round(100 * (1 - self.out_bytes / self.orig_bytes))


class ImageIntakeError(ValueError):
    """The bytes weren't a decodable image (or were corrupt/truncated)."""


def _load_oriented(data: bytes) -> Image.Image:
    """Decode, then apply the EXIF rotation so the image stands upright.

    exif_transpose bakes the rotation into the pixels and drops the EXIF
    orientation tag — re-encoding later then strips remaining metadata.
    """
    if not data:
        raise ImageIntakeError("empty image upload")
    try:
        img = Image.open(BytesIO(data))
        img.load()                       # force decode now → catch truncation here
    except Exception as exc:             # noqa: BLE001 — Pillow raises a zoo of types
        raise ImageIntakeError(f"not a readable image: {exc}") from exc
    return ImageOps.exif_transpose(img)


def _flatten_to_rgb(img: Image.Image) -> Image.Image:
    """JPEG can't hold alpha — composite transparency onto white."""
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        img = img.convert("RGBA")
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[-1])
        return bg
    return img.convert("RGB")


def _downscale(img: Image.Image, max_edge: int) -> Image.Image:
    """Shrink so the longer side == max_edge. Never upscale a small photo."""
    w, h = img.size
    longest = max(w, h)
    if longest <= max_edge:
        return img
    scale = max_edge / longest
    return img.resize((max(1, round(w * scale)), max(1, round(h * scale))), _LANCZOS)


def _enhance(img: Image.Image) -> Image.Image:
    """Mild, deterministic clean-up — never an aggressive 'beautify'."""
    img = ImageOps.autocontrast(img, cutoff=1)          # fix flat/dim phone shots
    return ImageEnhance.Sharpness(img).enhance(1.15)    # a touch crisper


def _square_thumb(img: Image.Image, px: int) -> Image.Image:
    """Center-crop to a clean square thumbnail (the 'nice centered picture')."""
    return ImageOps.fit(img, (px, px), _LANCZOS, centering=(0.5, 0.5))


def _encode(img: Image.Image, quality: int) -> bytes:
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=quality, optimize=True)
    return buf.getvalue()


def process(data: bytes, preset: IntakePreset = PRODUCT) -> IntakeResult:
    """Run an uploaded photo through the full pipeline.

    Raises ImageIntakeError if the bytes aren't a decodable image.
    """
    base = _flatten_to_rgb(_load_oriented(data))
    main_img = _downscale(base, preset.max_edge)
    if preset.enhance:
        main_img = _enhance(main_img)
    main = _encode(main_img, preset.quality)

    thumb = None
    if preset.thumb_px:
        thumb = _encode(_square_thumb(main_img, preset.thumb_px), preset.quality)

    return IntakeResult(
        main=main,
        thumb=thumb,
        content_type="image/jpeg",
        width=main_img.width,
        height=main_img.height,
        orig_bytes=len(data),
        out_bytes=len(main),
    )
