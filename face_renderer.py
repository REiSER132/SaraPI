import math

def rotate_point(p, cx, cy, angle_deg):
    rad = math.radians(angle_deg)
    cos_a, sin_a = math.cos(rad), math.sin(rad)
    return (
        (p[0] - cx) * cos_a - (p[1] - cy) * sin_a + cx,
        (p[0] - cx) * sin_a + (p[1] - cy) * cos_a + cy
    )

def bezier(p0, p1, p2):
    pts = []
    for i in range(11):
        t = i / 10.0
        mt = 1 - t
        bx = mt**2 * p0[0] + 2*mt*t * p1[0] + t**2 * p2[0]
        by = mt**2 * p0[1] + 2*mt*t * p1[1] + t**2 * p2[1]
        pts.append((bx, by))
    return pts

def _draw_eye(draw, cx, cy, openness, angle, p_size, px, py, is_left=True, error_mode=0.0):
    s = -1 if is_left else 1
    mh = 9 * openness

    # Контрольные точки
    pts = {
        "nt": (cx - 15*s, cy - mh*0.6), "nb": (cx - 13*s, cy + mh*0.4),
        "tm": (cx - 2*s, cy - mh*1.3), "wit": (cx + 12*s, cy - mh*0.3),
        "wt": (cx + 22*s, cy), "wib": (cx + 10*s, cy + mh*0.5),
        "bm": (cx - 2*s, cy + mh*0.9)
    }
    # Вращение
    rot = lambda p: rotate_point(p, cx, cy, angle * s)
    for k in pts: pts[k] = rot(pts[k])

    top_arc = bezier(pts["nt"], pts["tm"], pts["wit"])
    bot_arc = bezier(pts["nb"], pts["bm"], pts["wib"])

    # Маски обрезают зрачок за пределами век
    draw.polygon(top_arc + [(cx+30*s, cy-30), (cx-30*s, cy-30)], fill="black")
    draw.polygon(bot_arc + [(cx+30*s, cy+30), (cx-30*s, cy+30)], fill="black")
    draw.polygon([pts["nt"], pts["nb"], (cx-30*s, cy+30), (cx-30*s, cy-30)], fill="black")

    # Контуры
    draw.line([pts["nt"], pts["nb"]], fill="white", width=2)
    draw.line(top_arc, fill="white", width=2)
    draw.line(bot_arc, fill="white", width=1)
    draw.polygon([pts["wit"], pts["wt"], pts["wib"]], fill="white")

    # Зрачок (синхронный взгляд + компенсация косоглазия)
    offset = -3 * s
    pcx = cx + (6*s if error_mode > 0.5 else px + offset)
    pcy = cy - mh*0.1 + py
    pw, ph = p_size * 0.6, p_size * 0.9
    draw.ellipse((pcx - pw, pcy - ph, pcx + pw, pcy + ph), fill="white")
    if p_size > 2.0:
        draw.ellipse((pcx - 1, pcy - 1, pcx + 1, pcy + 1), fill="black")

def render_face(draw, state, breath, eye_op_l, eye_op_r):
    lx, rx = 28, 100
    
    # Брови (Y берётся из пресета напрямую + дыхание)
    by = state["brow_y"] + breath
    for x, left in zip([lx, rx], [True, False]):
        s = -1 if left else 1
        rad = math.radians(state["brow_angle"] * s)
        dx, dy = (state["brow_thick"] * 0.5) * math.cos(rad), (state["brow_thick"] * 0.5) * math.sin(rad)
        p0 = (x - dx*s, by - dy*s)
        p2 = (x + dx*s, by + dy*s)
        p1 = (x, by - 3 - abs(dy))
        draw.line(bezier(p0, p1, p2), fill="white", width=max(1, int(state["brow_thick"])))

    # Глаза
    _draw_eye(draw, lx, 30, eye_op_l, state["eye_angle"], state["pupil_size"], state["pupil_x"], state["pupil_y"], True, state["error_mode"])
    _draw_eye(draw, rx, 30, eye_op_r, state["eye_angle"], state["pupil_size"], state["pupil_x"], state["pupil_y"], False, state["error_mode"])

    # Нос
    ns = 2
    draw.line([(64 - ns, 42 + breath), (64, 42 + ns + breath), (64 + ns, 42 + breath)], fill="white", width=1)

    # Рот
    mx, my = 64, 50 + breath
    mw = 12
    p0 = (mx - mw, my)
    p2 = (mx + mw, my)
    p1 = (mx, my + (state["mouth_smile"] * -5.0))
    draw.line(bezier(p0, p1, p2), fill="white", width=2)

    if state["mouth_fang"] > 0.5:
        fx, fy = mx - 6, my + (state["mouth_smile"] * -2.5)
        draw.polygon([(fx-3, fy), (fx+3, fy), (fx, fy+6)], fill="white")

    if state["mouth_open"] > 0.1:
        p1_low = (mx, p1[1] + state["mouth_open"])
        draw.line(bezier(p0, p1_low, p2), fill="white", width=1)

    if state["error_mode"] > 0.5:
        draw.text((48, 52), "ERROR", fill="white")