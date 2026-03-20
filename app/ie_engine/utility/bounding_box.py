import math


def _center(b):
    x0,y0,x1,y1 = b
    return ((x0+x1)/2.0, (y0+y1)/2.0)

def _height(b):
    return abs(b[3]-b[1])

def _vertical_overlap_ratio(a, b):
    # poměr překryvu ve svislém směru vůči min výšce
    ay0, ay1 = a[1], a[3]
    by0, by1 = b[1], b[3]
    overlap = max(0, min(ay1, by1) - max(ay0, by0))
    return overlap / max(1.0, min(_height(a), _height(b)))

def _same_line(a, b, overlap_thr=0.55, dy_factor=0.6):
    # „stejná řádka“, když je slušný vertikální překryv NEBO
    # rozdíl středů y je menší než dy_factor * průměrná výška
    ov = _vertical_overlap_ratio(a, b)
    if ov >= overlap_thr:
        return True
    _, ay = _center(a)
    _, by = _center(b)
    avg_h = (_height(a)+_height(b))/2.0
    return abs(ay-by) <= dy_factor * avg_h

def _weighted_distance(bbox_b, bbox_i, lambda_dy=12.0, same_line_boost=0.15, left_penalty=300.0):
    # anizotropní L2 + bonus za stejnou řádku + penalizace, když je I_ vlevo od B_
    cx_b, cy_b = _center(bbox_b)
    cx_i, cy_i = _center(bbox_i)
    dx = cx_i - cx_b
    dy = cy_i - cy_b

    base = math.sqrt(dx*dx + (lambda_dy*dy)*(lambda_dy*dy))

    # velká výhoda pro stejnou řádku
    if _same_line(bbox_b, bbox_i):
        base *= same_line_boost  # výrazně zlevním kandidáty na stejné řádce

    # čtecí směr: pokud je I_ vlevo (dx<0), brutálně potrestat
    if dx < -0.25 * max(1.0, _height(bbox_b)):
        base += left_penalty

    return base