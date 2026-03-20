

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