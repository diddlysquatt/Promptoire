from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Sequence, Tuple, Union, cast


VISUAL_REGRESSION_ENABLED_ENV = "VISUAL_REGRESSION_ENABLED"
VISUAL_REGRESSION_UPDATE_ENV = "VISUAL_REGRESSION_UPDATE"

DEFAULT_DPI = 144  # 2x @ 72dpi; stable + reasonably fast.
DEFAULT_BBOX_OUTLINE_RGB = (255, 0, 0)
DEFAULT_BBOX_LINE_WIDTH_PX = 2

TESTS_DIR = Path(__file__).resolve().parent
BASELINES_BBOX_DIR = TESTS_DIR / "visual_baselines_bbox"
DIFFS_DIR = TESTS_DIR / "visual_diffs"
BASELINE_HASHES_PATH = BASELINES_BBOX_DIR / "bbox_overlay_hashes.json"


NormalizedBBox = Tuple[float, float, float, float]  # (x0, y0, x1, y1) in [0, 1]
PDFInput = Union[str, os.PathLike, bytes, bytearray]


def _env_truthy(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def visual_regression_enabled() -> bool:
    return _env_truthy(VISUAL_REGRESSION_ENABLED_ENV)


def visual_regression_update_enabled() -> bool:
    return _env_truthy(VISUAL_REGRESSION_UPDATE_ENV)


def _import_deps():
    try:
        import fitz  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("PyMuPDF is required: `pip install pymupdf`") from exc

    try:
        from PIL import Image, ImageDraw  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("Pillow is required: `pip install pillow`") from exc

    return fitz, Image, ImageDraw


def _safe_filename(stem: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9_.-]+", "_", stem).strip("._")
    return safe or "visual_regression"


def render_pdf_page_to_pil(pdf: PDFInput, *, page_number: int = 0, dpi: int = DEFAULT_DPI):
    fitz, Image, _ImageDraw = _import_deps()

    if isinstance(pdf, (bytes, bytearray)):
        doc = fitz.open(stream=bytes(pdf), filetype="pdf")
    else:
        doc = fitz.open(cast(str, os.fspath(pdf)))

    try:
        page = doc.load_page(page_number)
        zoom = float(dpi) / 72.0
        matrix = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=matrix, colorspace=fitz.csRGB, alpha=False)
        return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    finally:
        doc.close()


def _normalized_bbox_to_pixels(bbox: NormalizedBBox, *, width_px: int, height_px: int) -> Tuple[int, int, int, int]:
    x0, y0, x1, y1 = bbox

    left_n = min(x0, x1)
    right_n = max(x0, x1)
    top_n = min(y0, y1)
    bottom_n = max(y0, y1)

    left = int(round(left_n * width_px))
    right = int(round(right_n * width_px))
    top = int(round(top_n * height_px))
    bottom = int(round(bottom_n * height_px))

    left = max(0, min(width_px, left))
    right = max(0, min(width_px, right))
    top = max(0, min(height_px, top))
    bottom = max(0, min(height_px, bottom))

    return left, top, right, bottom


def draw_normalized_bboxes_pil(
    image,
    bboxes: Sequence[NormalizedBBox],
    *,
    outline_rgb: Tuple[int, int, int] = DEFAULT_BBOX_OUTLINE_RGB,
    width_px: int = DEFAULT_BBOX_LINE_WIDTH_PX,
):
    _fitz, _Image, ImageDraw = _import_deps()

    draw = ImageDraw.Draw(image)
    width, height = image.size

    for bbox in bboxes:
        left, top, right, bottom = _normalized_bbox_to_pixels(bbox, width_px=width, height_px=height)
        draw.rectangle((left, top, right, bottom), outline=outline_rgb, width=width_px)

    return image


def hash_pil_image(image) -> str:
    _fitz, _Image, _ImageDraw = _import_deps()

    image_rgb = image.convert("RGB")
    hasher = hashlib.sha256()
    hasher.update(image_rgb.mode.encode("utf-8"))
    hasher.update(int(image_rgb.size[0]).to_bytes(8, "little", signed=False))
    hasher.update(int(image_rgb.size[1]).to_bytes(8, "little", signed=False))
    hasher.update(image_rgb.tobytes())
    return hasher.hexdigest()


def render_pdf_page_with_bbox_overlay_hash(
    pdf: PDFInput,
    *,
    page_number: int = 0,
    bboxes: Sequence[NormalizedBBox],
    dpi: int = DEFAULT_DPI,
    outline_rgb: Tuple[int, int, int] = DEFAULT_BBOX_OUTLINE_RGB,
    width_px: int = DEFAULT_BBOX_LINE_WIDTH_PX,
):
    image = render_pdf_page_to_pil(pdf, page_number=page_number, dpi=dpi)
    draw_normalized_bboxes_pil(image, bboxes, outline_rgb=outline_rgb, width_px=width_px)
    return hash_pil_image(image), image


def _load_hash_baselines(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):  # pragma: no cover
        raise TypeError(f"Expected baseline JSON object in {path}")
    return {str(k): str(v) for k, v in data.items()}


def _write_hash_baselines(path: Path, baselines: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(sorted(baselines.items())), indent=2) + "\n", encoding="utf-8")


def assert_visual_hash_matches_baseline(
    *,
    test_id: str,
    actual_hash: str,
    baseline_hashes_path: Path = BASELINE_HASHES_PATH,
    update: bool | None = None,
) -> None:
    if not visual_regression_enabled():
        return

    if update is None:
        update = visual_regression_update_enabled()

    baselines = _load_hash_baselines(baseline_hashes_path)
    expected = baselines.get(test_id)

    if expected is None:
        if update:
            baselines[test_id] = actual_hash
            _write_hash_baselines(baseline_hashes_path, baselines)
            return
        raise AssertionError(
            f"Missing baseline for {test_id} in {baseline_hashes_path}. "
            f"To record: set {VISUAL_REGRESSION_UPDATE_ENV}=1"
        )

    if expected != actual_hash:
        raise AssertionError(f"Visual hash mismatch for {test_id}: expected {expected}, got {actual_hash}")


def assert_bbox_overlay_matches_baseline(
    *,
    test_id: str,
    pdf: PDFInput,
    page_number: int = 0,
    bboxes: Sequence[NormalizedBBox],
    dpi: int = DEFAULT_DPI,
    baseline_hashes_path: Path = BASELINE_HASHES_PATH,
    diffs_dir: Path = DIFFS_DIR,
    update: bool | None = None,
) -> None:
    if not visual_regression_enabled():
        return

    actual_hash, image = render_pdf_page_with_bbox_overlay_hash(
        pdf,
        page_number=page_number,
        bboxes=bboxes,
        dpi=dpi,
    )

    if update is None:
        update = visual_regression_update_enabled()

    baselines = _load_hash_baselines(baseline_hashes_path)
    expected = baselines.get(test_id)

    if expected is None and update:
        baselines[test_id] = actual_hash
        _write_hash_baselines(baseline_hashes_path, baselines)
        return

    if expected == actual_hash:
        return

    diffs_dir.mkdir(parents=True, exist_ok=True)
    diff_path = diffs_dir / f"{_safe_filename(test_id)}.png"
    image.save(diff_path)

    if expected is None:
        raise AssertionError(
            f"Missing baseline for {test_id} in {baseline_hashes_path}. "
            f"Wrote current render to {diff_path}. "
            f"To record: set {VISUAL_REGRESSION_UPDATE_ENV}=1"
        )

    raise AssertionError(
        f"Visual regression mismatch for {test_id}: expected {expected}, got {actual_hash}. "
        f"Wrote current render to {diff_path}"
    )


def _demo_pdf_bytes() -> bytes:
    fitz, _Image, _ImageDraw = _import_deps()

    doc = fitz.open()
    try:
        page = doc.new_page(width=400, height=300)
        page.insert_text((72, 72), "BBox Overlay", fontsize=24, fontname="helv")
        page.draw_rect(fitz.Rect(40, 40, 360, 260), color=(0, 0, 0), width=1)
        page.draw_line((40, 260), (360, 40), color=(0, 0, 0), width=1)
        return doc.tobytes()
    finally:
        doc.close()


def test_visual_regression_bbox_overlay_hash_matches_baseline():
    import pytest

    if not visual_regression_enabled():
        pytest.skip(f"Set {VISUAL_REGRESSION_ENABLED_ENV}=1 to enable visual regression tests.")

    pdf_bytes = _demo_pdf_bytes()
    bboxes: Sequence[NormalizedBBox] = [
        (0.10, 0.12, 0.45, 0.30),
        (0.55, 0.55, 0.90, 0.88),
    ]

    assert_bbox_overlay_matches_baseline(
        test_id="demo_bbox_overlay_v1",
        pdf=pdf_bytes,
        page_number=0,
        bboxes=bboxes,
        dpi=DEFAULT_DPI,
        baseline_hashes_path=BASELINE_HASHES_PATH,
        diffs_dir=DIFFS_DIR,
    )
