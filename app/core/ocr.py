"""OCR engine wrapper.

Uses RapidOCR (ONNX runtime) for fully offline text recognition with strong
Simplified/Traditional Chinese and Latin support. The heavy model is lazily
loaded on first use so application start-up stays fast.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - typing only
    from PIL import Image


class OCREngine:
    """Lazy wrapper around RapidOCR."""

    def __init__(self) -> None:
        self._engine = None

    def _ensure_loaded(self) -> None:
        if self._engine is None:
            from rapidocr_onnxruntime import RapidOCR

            self._engine = RapidOCR()

    def is_available(self) -> bool:
        try:
            import rapidocr_onnxruntime  # noqa: F401

            return True
        except Exception:  # noqa: BLE001
            return False

    def image_to_text(self, image: "Image.Image") -> str:
        """Recognize text in a PIL image and return it joined by newlines.

        Result lines are ordered top-to-bottom based on the detected boxes so
        multi-line captures read naturally.
        """
        import numpy as np

        self._ensure_loaded()
        result, _ = self._engine(np.array(image.convert("RGB")))
        if not result:
            return ""

        # Each item: [box(4 points), text, score]. Sort by top-y of the box.
        def top_y(item) -> float:
            box = item[0]
            return min(point[1] for point in box)

        ordered = sorted(result, key=top_y)
        return "\n".join(item[1] for item in ordered).strip()
