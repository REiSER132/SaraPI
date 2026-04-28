from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from luma.core.render import canvas
from signal import signal, SIGINT
import time
import math
import sys

def handler(signal_received, frame):
    print('\n[-] Выключаем движок Сары.')
    device.cleanup()
    sys.exit(0)
signal(SIGINT, handler)

try:
    serial = i2c(port=1, address=0x3C)
    device = ssd1306(serial)
except Exception as e:
    print(f"[!] Ошибка: {e}")
    sys.exit(1)

# --- ПАРАМЕТРИЧЕСКИЙ ДВИЖОК ЛИЦА v7.2 (Visual Center Fix) ---

state = {
    "eye_openness": 1.0, "eye_angle": 0,
    "pupil_size": 3.5, "pupil_x": 0, "pupil_y": 0,
    "brow_y": 18, "brow_angle": 0, "brow_thick": 2,
    "mouth_smile": 0.0, "mouth_open": 0.0, "mouth_fang": 0.0,
    "error_mode": 0.0 
}
target = state.copy()

emotions = {
    "idle": { 
        "eye_openness": 0.9, "eye_angle": 0, "pupil_size": 4.0, "pupil_x": 0, "pupil_y": 0,
        "brow_y": 18, "brow_angle": 0, "brow_thick": 2,
        "mouth_smile": 0.1, "mouth_open": 0.0, "mouth_fang": 0.0,
        "error_mode": 0.0
    },
    "smug": { 
        "eye_openness": 0.45, "eye_angle": 5, "pupil_size": 3.0, "pupil_x": -4, "pupil_y": 1,
        "brow_y": 14, "brow_angle": 15, "brow_thick": 3,
        "mouth_smile": 0.9, "mouth_open": 0.2, "mouth_fang": 1.0,
        "error_mode": 0.0
    },
    "yandere": { 
        "eye_openness": 1.3, "eye_angle": -5, "pupil_size": 1.5, "pupil_x": 0, "pupil_y": -2,
        "brow_y": 22, "brow_angle": -15, "brow_thick": 1,
        "mouth_smile": -0.8, "mouth_open": 2.0, "mouth_fang": 0.0,
        "error_mode": 0.0
    },
    "error": { # Derp-mode
        "eye_openness": 1.2, "eye_angle": 15, "pupil_size": 3.0, "pupil_x": 0, "pupil_y": -1,
        "brow_y": 10, "brow_angle": -30, "brow_thick": 2,
        "mouth_smile": -1.0, "mouth_open": 0.0, "mouth_fang": 0.0,
        "error_mode": 1.0 
    }
}

emo_names = list(emotions.keys())
current_emo_idx = 0
last_switch = time.time()

def lerp(a, b, t): return a + (b - a) * t

def rotate_point(p, cx, cy, angle_deg):
    x, y = p
    rad = math.radians(angle_deg)
    nx = (x - cx) * math.cos(rad) - (y - cy) * math.sin(rad) + cx
    ny = (x - cx) * math.sin(rad) + (y - cy) * math.cos(rad) + cy
    return (nx, ny)

def bezier(p0, p1, p2):
    pts = []
    for i in range(11):
        t = i / 10.0
        bx = (1-t)**2 * p0[0] + 2*(1-t)*t * p1[0] + t**2 * p2[0]
        by = (1-t)**2 * p0[1] + 2*(1-t)*t * p1[1] + t**2 * p2[1]
        pts.append((bx, by))
    return pts

def draw_v7_anime_eye(draw, cx, cy, openness, angle, p_size, px, py, is_left=True, error_mode=0.0):
    side_mult = -1 if is_left else 1
    mh = 9 * openness 

    # --- ИСПРАВЛЕНИЕ ОПТИЧЕСКОЙ ИЛЛЮЗИИ ---
    # Смещаем зрачок на 4 пикселя ближе к носу (-side_mult - это направление к носу)
    visual_center_offset = -4 * side_mult 

    if error_mode > 0.5:
        # В режиме ERROR отменяем центровку и разводим глаза к ушам
        p_cx = cx + (6 * side_mult)
    else:
        # Нормальный режим: базовое смещение + синхронный взгляд px
        p_cx = cx + px + visual_center_offset
        
    p_cy = cy - mh*0.1 + py
    
    # Рисуем зрачок (узкий анимешный овал)
    p_w = p_size * 0.6
    p_h = p_size * 0.9
    draw.ellipse((p_cx - p_w, p_cy - p_h, p_cx + p_w, p_cy + p_h), fill="white")
    if p_size > 2.0: 
        draw.ellipse((p_cx - 1, p_cy - 1, p_cx + 1, p_cy + 1), fill="black")

    # Контур
    p_nose_top = (cx - 15 * side_mult, cy - mh * 0.6)
    p_nose_bot = (cx - 13 * side_mult, cy + mh * 0.4)
    p_top_mid = (cx - 2 * side_mult, cy - mh * 1.3)
    p_wing_in_top = (cx + 12 * side_mult, cy - mh * 0.3)
    p_wing_tip = (cx + 22 * side_mult, cy - mh * 0.0) 
    p_wing_in_bot = (cx + 10 * side_mult, cy + mh * 0.5)
    p_bot_mid = (cx - 2 * side_mult, cy + mh * 0.9)

    def rot(p): return rotate_point(p, cx, cy, angle * side_mult)
    p_nose_top, p_nose_bot, p_top_mid = rot(p_nose_top), rot(p_nose_bot), rot(p_top_mid)
    p_wing_in_top, p_wing_tip, p_wing_in_bot, p_bot_mid = rot(p_wing_in_top), rot(p_wing_tip), rot(p_wing_in_bot), rot(p_bot_mid)

    top_arc = bezier(p_nose_top, p_top_mid, p_wing_in_top)
    bot_arc = bezier(p_nose_bot, p_bot_mid, p_wing_in_bot)

    # Маски (строго снаружи!)
    draw.polygon(top_arc + [(cx+30*side_mult, cy-30), (cx-30*side_mult, cy-30)], fill="black")
    draw.polygon(bot_arc + [(cx+30*side_mult, cy+30), (cx-30*side_mult, cy+30)], fill="black")
    draw.polygon([p_nose_top, p_nose_bot, (cx-30*side_mult, cy+30), (cx-30*side_mult, cy-30)], fill="black")

    # Векa
    draw.line([p_nose_top, p_nose_bot], fill="white", width=2)
    draw.line(top_arc, fill="white", width=2)
    draw.line(bot_arc, fill="white", width=1)
    draw.polygon([p_wing_in_top, p_wing_tip, p_wing_in_bot], fill="white")

def draw_brow(draw, cx, cy, width, angle_deg, thickness, is_left=True):
    side_mult = -1 if is_left else 1
    rad = math.radians(angle_deg * side_mult)
    dx = (width / 2) * math.cos(rad)
    dy = (width / 2) * math.sin(rad)
    P0 = (cx - dx * side_mult, cy - dy * side_mult)
    P2 = (cx + dx * side_mult, cy + dy * side_mult)
    P1 = (cx, cy - 3 - abs(dy))
    draw.line(bezier(P0, P1, P2), fill="white", width=int(thickness))

def draw_nose(draw, cx, cy):
    size = 2
    draw.line([(cx - size, cy), (cx, cy + size), (cx + size, cy)], fill="white", width=1)

print("=== [ SARA FLAWLESS V7.2 + VISUAL CENTER ] ===")
frame_count = 0
fps_start = time.time()

while True:
    t = time.time()
    
    if t - last_switch > 5.0:
        current_emo_idx = (current_emo_idx + 1) % len(emo_names)
        target = emotions[emo_names[current_emo_idx]]
        last_switch = t

    for key in state:
        state[key] = lerp(state[key], target[key], 0.15)

    breath = math.sin(t * 1.5) * 1.0
    eye_op_l = state["eye_openness"] + (math.sin(t*2.1)*0.03)
    eye_op_r = state["eye_openness"] + (math.sin(t*1.9)*0.03)

    is_blinking = (t % 4.0) > 3.8
    eye_op_l_final = 0.05 if is_blinking else eye_op_l
    eye_op_r_final = 0.05 if is_blinking else eye_op_r

    with canvas(device) as draw:
        # Глаза остаются широко расставленными (28 и 100)
        lx, rx, y = 28, 100, 30
        
        draw_brow(draw, lx, 30 - state["brow_y"] + breath, 22, state["brow_angle"], state["brow_thick"], is_left=True)
        draw_brow(draw, rx, 30 - state["brow_y"] + breath, 22, state["brow_angle"], state["brow_thick"], is_left=False)

        draw_v7_anime_eye(draw, lx, y, eye_op_l_final, state["eye_angle"], state["pupil_size"], state["pupil_x"], state["pupil_y"], is_left=True, error_mode=state["error_mode"])
        draw_v7_anime_eye(draw, rx, y, eye_op_r_final, state["eye_angle"], state["pupil_size"], state["pupil_x"], state["pupil_y"], is_left=False, error_mode=state["error_mode"])

        draw_nose(draw, 64, 45 + breath)

        if state["error_mode"] > 0.5:
            draw.text((48, 52), "ERROR", fill="white")
        else:
            mx, my = 64, 53 + breath
            mw = 12
            P0 = (mx - mw, my)
            P1 = (mx, my + (state["mouth_smile"] * -5.0)) 
            P2 = (mx + mw, my)
            
            pts_mouth = bezier(P0, P1, P2)
            draw.line(pts_mouth, fill="white", width=2)
            
            if state["mouth_fang"] > 0.5:
                fang_x = mx - 6
                fang_y = my + (state["mouth_smile"] * -2.5) 
                draw.polygon([(fang_x - 3, fang_y), (fang_x + 3, fang_y), (fang_x, fang_y + 6)], fill="white")

            if state["mouth_open"] > 0.1:
                P1_low = (mx, P1[1] + state["mouth_open"])
                pts_mouth_low = bezier(P0, P1_low, P2)
                draw.line(pts_mouth_low, fill="white", width=1)

        frame_count += 1
        fps = frame_count / (t - fps_start)
        draw.text((0, 0), f"FPS:{fps:.0f}", fill="white")

    time.sleep(0.005)