# Базовый стейт
state = {
    "eye_openness": 1.0, "eye_angle": 0,
    "pupil_size": 3.5, "pupil_x": 0, "pupil_y": 0,
    "brow_y": 18, "brow_angle": 0, "brow_thick": 2,
    "mouth_smile": 0.0, "mouth_open": 0.0, "mouth_fang": 0.0,
    "error_mode": 0.0 
}

# Пресеты
presets = {
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
    "error": { 
        "eye_openness": 1.2, "eye_angle": 15, "pupil_size": 3.0, "pupil_x": 0, "pupil_y": -1,
        "brow_y": 10, "brow_angle": -30, "brow_thick": 2,
        "mouth_smile": -1.0, "mouth_open": 0.0, "mouth_fang": 0.0,
        "error_mode": 1.0 
    }
}

def lerp(a, b, t): 
    return a + (b - a) * t
