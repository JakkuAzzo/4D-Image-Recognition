import re
try:
    import numpy as np
except Exception:  # pragma: no cover
    np = None
from typing import Any
Array = np.ndarray if np is not None else Any
try:
    import pytesseract
except Exception:  # pragma: no cover - optional dependency
    pytesseract = None
try:
    from PIL import Image
except Exception:  # pragma: no cover
    Image = None


def read_id_fields(id_crop: Array) -> dict:
    """Run OCR on ID crop and parse basic fields."""
    if pytesseract is None or Image is None:
        return {}
    pil = Image.fromarray(id_crop)
    raw = pytesseract.image_to_string(pil, lang='eng')
    data = {}
    m = re.search(r'DOB[: ]+(\d{2}/\d{2}/\d{4})', raw)
    if m:
        data['dob'] = m.group(1)
    return data
