# =============================================================================
# ASL TEMPLATES — 26 lettres + chiffres 1 à 9
# =============================================================================
# Chaque lettre est définie par un vecteur de 5 valeurs normalisées [0.0 → 1.0]
# Format : [pouce, index, majeur, annulaire, auriculaire]
#   0.0 = doigt complètement tendu
#   1.0 = doigt complètement plié
#
# IMPORTANT : ces valeurs sont des ratios normalisés — indépendantes du gant.
# La calibration au démarrage mappe les ADC bruts vers [0.0, 1.0].
#
# Source anatomique : ASL fingerspelling standard (Stokoe notation)
# Les valeurs "intermédiaires" (0.3, 0.5, 0.7) représentent les positions
# réelles des doigts qui ne sont ni tendus ni pliés complètement.
# =============================================================================

# Tolérance de matching par défaut (distance de Manhattan max acceptable)
DEFAULT_TOLERANCE = 1.5

# Tolérance IMU pour les lettres ambiguës (degrés)
IMU_TOLERANCE = 25

# =============================================================================
# TABLE DES TEMPLATES
# =============================================================================
# Clé : lettre ou chiffre (str)
# Valeur : dict avec :
#   "flex"  : [pouce, index, majeur, annulaire, auriculaire] normalisés 0.0→1.0
#   "imu"   : {"pitch": float, "roll": float} — orientation de la main (optionnel)
#   "note"  : description anatomique de la position
# =============================================================================

ASL_TEMPLATES = {

    # ─────────────────── LETTRES ───────────────────

    "A": {
        "flex": [0.5, 1.0, 1.0, 1.0, 1.0],
        "imu":  {"pitch": 0,   "roll": 0},
        "note": "Poing fermé, pouce sur le côté (semi-plié)"
    },
    "B": {
        "flex": [1.0, 0.0, 0.0, 0.0, 0.0],
        "imu":  {"pitch": 0,   "roll": 0},
        "note": "4 doigts tendus, pouce replié contre paume"
    },
    "C": {
        "flex": [0.4, 0.4, 0.4, 0.4, 0.4],
        "imu":  {"pitch": 0,   "roll": 0},
        "note": "Tous les doigts courbés en forme de C"
    },
    "D": {
        "flex": [0.6, 0.0, 1.0, 1.0, 1.0],
        "imu":  {"pitch": 0,   "roll": 0},
        "note": "Index tendu, autres pliés, pouce touche le majeur"
    },
    "E": {
        "flex": [0.7, 0.7, 0.7, 0.7, 0.7],
        "imu":  {"pitch": 0,   "roll": 0},
        "note": "Tous les doigts courbés vers la paume (E arrondi)"
    },
    "F": {
        "flex": [0.0, 0.8, 0.0, 0.0, 0.0],
        "imu":  {"pitch": 0,   "roll": 0},
        "note": "Pouce et index forment un cercle, autres tendus"
    },
    "G": {
        "flex": [0.3, 0.3, 1.0, 1.0, 1.0],
        "imu":  {"pitch": 0,   "roll": -45},
        "note": "Pouce et index pointent horizontalement (comme un pistolet)"
    },
    "H": {
        "flex": [1.0, 0.0, 0.0, 1.0, 1.0],
        "imu":  {"pitch": 0,   "roll": -45},
        "note": "Index et majeur tendus horizontalement côte à côte"
    },
    "I": {
        "flex": [1.0, 1.0, 1.0, 1.0, 0.0],
        "imu":  {"pitch": 0,   "roll": 0},
        "note": "Auriculaire tendu, les 4 autres pliés"
    },
    "J": {
        # J = I + mouvement en J — ici on capture la position de départ
        "flex": [1.0, 1.0, 1.0, 1.0, 0.0],
        "imu":  {"pitch": 20,  "roll": 0},
        "note": "Comme I mais avec inclinaison (dynamique — mouvement en J)"
    },
    "K": {
        "flex": [0.5, 0.0, 0.3, 1.0, 1.0],
        "imu":  {"pitch": 0,   "roll": 0},
        "note": "Index tendu vers le haut, majeur semi-tendu, pouce entre les deux"
    },
    "L": {
        "flex": [0.0, 0.0, 1.0, 1.0, 1.0],
        "imu":  {"pitch": 0,   "roll": 0},
        "note": "Pouce et index tendus en L, autres pliés"
    },
    "M": {
        "flex": [0.8, 1.0, 1.0, 1.0, 1.0],
        "imu":  {"pitch": 0,   "roll": 0},
        "note": "Pouce sous index+majeur+annulaire, auriculaire plié"
    },
    "N": {
        "flex": [0.8, 1.0, 1.0, 1.0, 1.0],
        "imu":  {"pitch": 10,  "roll": 0},
        "note": "Comme M mais pouce sous index+majeur seulement (IMU différent)"
    },
    "O": {
        "flex": [0.5, 0.5, 0.5, 0.5, 0.5],
        "imu":  {"pitch": 0,   "roll": 0},
        "note": "Tous les doigts forment un O avec le pouce"
    },
    "P": {
        "flex": [0.5, 0.0, 0.3, 1.0, 1.0],
        "imu":  {"pitch": -45, "roll": 0},
        "note": "Comme K mais main pointée vers le bas"
    },
    "Q": {
        "flex": [0.3, 0.3, 1.0, 1.0, 1.0],
        "imu":  {"pitch": -45, "roll": 0},
        "note": "Comme G mais pointé vers le bas"
    },
    "R": {
        "flex": [1.0, 0.0, 0.0, 1.0, 1.0],
        "imu":  {"pitch": 0,   "roll": 0},
        "note": "Index et majeur croisés et tendus"
    },
    "S": {
        "flex": [0.7, 1.0, 1.0, 1.0, 1.0],
        "imu":  {"pitch": 0,   "roll": 0},
        "note": "Poing fermé, pouce par-dessus les doigts"
    },
    "T": {
        "flex": [0.6, 1.0, 1.0, 1.0, 1.0],
        "imu":  {"pitch": 0,   "roll": 0},
        "note": "Pouce entre index et majeur, poing serré"
    },
    "U": {
        "flex": [1.0, 0.0, 0.0, 1.0, 1.0],
        "imu":  {"pitch": 15,  "roll": 0},
        "note": "Index et majeur tendus et collés (différent de R par IMU)"
    },
    "V": {
        "flex": [1.0, 0.0, 0.0, 1.0, 1.0],
        "imu":  {"pitch": 0,   "roll": 0},
        "note": "Index et majeur tendus en V (écartés — différent de U)"
    },
    "W": {
        "flex": [1.0, 0.0, 0.0, 0.0, 1.0],
        "imu":  {"pitch": 0,   "roll": 0},
        "note": "Index, majeur, annulaire tendus et écartés"
    },
    "X": {
        "flex": [1.0, 0.5, 1.0, 1.0, 1.0],
        "imu":  {"pitch": 0,   "roll": 0},
        "note": "Index croché (crochet), autres pliés"
    },
    "Y": {
        "flex": [0.0, 1.0, 1.0, 1.0, 0.0],
        "imu":  {"pitch": 0,   "roll": 0},
        "note": "Pouce et auriculaire tendus, autres pliés"
    },
    "Z": {
        # Z = mouvement dynamique en Z — position de départ
        "flex": [1.0, 0.0, 1.0, 1.0, 1.0],
        "imu":  {"pitch": 0,   "roll": 0},
        "note": "Index tendu, trace un Z dans l'air (dynamique)"
    },

    # ─────────────────── CHIFFRES ───────────────────

    "1": {
        "flex": [1.0, 0.0, 1.0, 1.0, 1.0],
        "imu":  {"pitch": 0,   "roll": 0},
        "note": "Index tendu vers le haut, autres pliés"
    },
    "2": {
        "flex": [1.0, 0.0, 0.0, 1.0, 1.0],
        "imu":  {"pitch": 0,   "roll": 0},
        "note": "Index et majeur tendus (V / peace sign)"
    },
    "3": {
        "flex": [0.0, 0.0, 0.0, 1.0, 1.0],
        "imu":  {"pitch": 0,   "roll": 0},
        "note": "Pouce, index, majeur tendus"
    },
    "4": {
        "flex": [1.0, 0.0, 0.0, 0.0, 0.0],
        "imu":  {"pitch": 0,   "roll": 0},
        "note": "4 doigts tendus, pouce plié (différent de B par IMU)"
    },
    "5": {
        "flex": [0.0, 0.0, 0.0, 0.0, 0.0],
        "imu":  {"pitch": 0,   "roll": 0},
        "note": "Tous les 5 doigts tendus et écartés"
    },
    "6": {
        "flex": [0.0, 1.0, 1.0, 1.0, 0.0],
        "imu":  {"pitch": 0,   "roll": 0},
        "note": "Pouce et auriculaire tendus et qui se touchent"
    },
    "7": {
        "flex": [0.0, 1.0, 1.0, 0.0, 1.0],
        "imu":  {"pitch": 0,   "roll": 0},
        "note": "Pouce et annulaire qui se touchent"
    },
    "8": {
        "flex": [0.0, 1.0, 0.0, 1.0, 1.0],
        "imu":  {"pitch": 0,   "roll": 0},
        "note": "Pouce et majeur qui se touchent"
    },
    "9": {
        "flex": [0.0, 0.0, 1.0, 1.0, 1.0],
        "imu":  {"pitch": 0,   "roll": 0},
        "note": "Pouce et index forment un cercle (comme F mais différent)"
    },
}

# =============================================================================
# GROUPES DE LETTRES AMBIGUËS — nécessitent l'IMU pour être distinguées
# =============================================================================
AMBIGUOUS_GROUPS = [
    {"A", "S", "E", "M", "N", "T"},   # Poings fermés avec variations
    {"G", "Q"},                         # Même flex, orientation différente
    {"H", "U", "V", "R"},              # Index+majeur tendus
    {"I", "J"},                         # Auriculaire seul
    {"D", "1"},                         # Index seul tendu
    {"B", "4"},                         # 4 doigts tendus
    {"K", "P"},                         # Même flex, pitch différent
    {"F", "9"},                         # Pouce+index cercle
]
