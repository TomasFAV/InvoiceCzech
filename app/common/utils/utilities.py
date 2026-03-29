

import re


def union_bbox(bboxes):
    """
    bboxes: iterable 4-tic (x1, y1, x2, y2)
    vrací:  (x1, y1, x2, y2) – nejmenší bbox, který všechny obsahne
    """
    
    if not bboxes:
        raise ValueError("union_bbox: prázdný seznam bboxů")

    x1 = min(bb[0] for bb in bboxes)
    y1 = min(bb[1] for bb in bboxes)
    x2 = max(bb[2] for bb in bboxes)
    y2 = max(bb[3] for bb in bboxes)
    return (x1, y1, x2, y2)

def normalize_text(x):
    if x is None:
        return ""

    if not isinstance(x, str):
        x = str(x)

    x = x.strip().lower()

    if not x:
        return ""

    x = x.replace("\u00a0", " ")
    x = re.sub(r"\s+", " ", x)

    # fix "4. 80" -> "4.80", "4 , 80" -> "4,80"
    x = re.sub(r"(\d)\s*([.,])\s*(\d)", r"\1\2\3", x)

    return x