# =============================================================================
# CLASSIFIER — Reconnaissance ASL multi-niveaux avec IMU
# =============================================================================
# Algorithme :
#   1. Normalisation des valeurs ADC (via Calibration)
#   2. Calcul de la distance de Manhattan entre les valeurs normalisées
#      et chaque template ASL
#   3. Si plusieurs candidats sont trop proches (ambiguïté),
#      on utilise le pitch/roll du MPU9250 pour trancher
#   4. Stabilisation : même lettre N fois de suite avant validation
#   5. Cooldown entre deux validations de la même lettre
# =============================================================================

import time
import logging
from asl_templates import ASL_TEMPLATES, AMBIGUOUS_GROUPS, DEFAULT_TOLERANCE, IMU_TOLERANCE

logger = logging.getLogger(__name__)

# ─── Paramètres de stabilisation ───────────────────────────────────────────
STABILITY_FRAMES   = 6      # Nombre de trames identiques avant validation
COOLDOWN_SECONDS   = 0.8    # Délai min entre deux lettres validées
WORD_PAUSE_SECONDS = 1.5    # Pause sans lettre → mot terminé
FLEX_TOLERANCE     = DEFAULT_TOLERANCE
# ────────────────────────────────────────────────────────────────────────────


def _manhattan(vec_a: list, vec_b: list) -> float:
    """Distance de Manhattan entre deux vecteurs de même longueur."""
    return sum(abs(a - b) for a, b in zip(vec_a, vec_b))


def _imu_distance(imu_data: dict, template_imu: dict) -> float:
    """Distance angulaire simplifiée (pitch + roll)."""
    dp = abs(imu_data.get("pitch", 0) - template_imu.get("pitch", 0))
    dr = abs(imu_data.get("roll",  0) - template_imu.get("roll",  0))
    return dp + dr


def _in_same_ambiguous_group(letter_a: str, letter_b: str) -> bool:
    """Vérifie si deux lettres appartiennent au même groupe ambigu."""
    for group in AMBIGUOUS_GROUPS:
        if letter_a in group and letter_b in group:
            return True
    return False


class Classifier:
    def __init__(self):
        self.history        = []          # Fenêtre glissante des dernières prédictions
        self.last_validated = None        # Dernière lettre validée
        self.last_valid_time = 0.0        # Timestamp de la dernière validation
        self.last_letter_time = 0.0       # Timestamp de la dernière lettre reçue (pour pause mot)
        self.word_buffer    = []          # Lettres en cours d'assemblage en mot

    # ─────────────────────────────────────────────────────────────────────────
    # 1. PRÉDICTION INSTANTANÉE
    # ─────────────────────────────────────────────────────────────────────────

    def predict(self, normalized_flex: list, imu_data: dict) -> dict:
        """
        Retourne la lettre la plus probable pour une trame donnée.

        Args:
            normalized_flex : liste de 5 floats [0.0, 1.0]
            imu_data        : dict {"pitch": float, "roll": float, "yaw": float}

        Returns:
            dict {
                "letter"    : str ou None,
                "confidence": float (distance → plus bas = mieux),
                "candidates": list de (lettre, distance)
            }
        """
        scores = []
        for letter, template in ASL_TEMPLATES.items():
            dist = _manhattan(normalized_flex, template["flex"])
            scores.append((letter, dist))

        # Trier par distance croissante
        scores.sort(key=lambda x: x[1])
        best_letter, best_dist = scores[0]
        second_letter, second_dist = scores[1]

        # ── Rejet si trop loin de tout template ──────────────────────────
        if best_dist > FLEX_TOLERANCE:
            return {"letter": None, "confidence": best_dist, "candidates": scores[:3]}

        # ── Ambiguïté : les deux meilleurs sont très proches ─────────────
        gap = second_dist - best_dist
        if gap < 0.4 and _in_same_ambiguous_group(best_letter, second_letter):
            # Utiliser l'IMU pour trancher
            best_letter = self._resolve_with_imu(
                [best_letter, second_letter], imu_data
            )
            logger.debug(
                "🔀 Ambiguïté %s/%s résolue par IMU → %s",
                scores[0][0], scores[1][0], best_letter
            )

        return {
            "letter":     best_letter,
            "confidence": best_dist,
            "candidates": scores[:3]
        }

    def _resolve_with_imu(self, candidates: list, imu_data: dict) -> str:
        """Parmi une liste de candidats ambigus, choisit via l'IMU."""
        best = candidates[0]
        best_imu_dist = float("inf")
        for letter in candidates:
            d = _imu_distance(imu_data, ASL_TEMPLATES[letter]["imu"])
            if d < best_imu_dist:
                best_imu_dist = d
                best = letter
        return best

    # ─────────────────────────────────────────────────────────────────────────
    # 2. STABILISATION + VALIDATION
    # ─────────────────────────────────────────────────────────────────────────

    def process_frame(self, normalized_flex: list, imu_data: dict) -> dict:
        """
        Pipeline complet pour une trame :
          predict → stabiliser → valider → assembler mot

        Returns:
            dict {
                "raw_prediction" : str ou None,
                "validated"      : bool,
                "letter"         : str ou None  (si validée),
                "word_complete"  : bool,
                "word"           : str ou None  (si mot terminé),
                "word_buffer"    : str           (mot en cours)
            }
        """
        now = time.time()

        # ── Prédiction instantanée ────────────────────────────────────────
        pred = self.predict(normalized_flex, imu_data)
        raw = pred["letter"]

        # ── Fenêtre de stabilisation ──────────────────────────────────────
        self.history.append(raw)
        if len(self.history) > STABILITY_FRAMES:
            self.history.pop(0)

        validated        = False
        validated_letter = None
        word_complete    = False
        word             = None

        # ── Vérifier si on a N frames identiques ─────────────────────────
        stable = (
            len(self.history) == STABILITY_FRAMES
            and len(set(self.history)) == 1
            and raw is not None
        )

        if stable:
            # ── Cooldown entre deux mêmes lettres ─────────────────────────
            cooldown_ok = (
                raw != self.last_validated
                or (now - self.last_valid_time) > COOLDOWN_SECONDS
            )

            if cooldown_ok:
                validated        = True
                validated_letter = raw
                self.last_validated  = raw
                self.last_valid_time = now
                self.last_letter_time = now

                self.word_buffer.append(raw)
                logger.info("✅ Lettre validée : %s  (buffer: %s)", raw, "".join(self.word_buffer))

        # ── Détection de fin de mot (pause > WORD_PAUSE_SECONDS) ─────────
        if (
            self.last_letter_time > 0
            and (now - self.last_letter_time) > WORD_PAUSE_SECONDS
            and len(self.word_buffer) > 0
        ):
            word = "".join(self.word_buffer)
            logger.info("📝 Mot complet : %s", word)
            word_complete = True
            self.word_buffer = []
            self.last_letter_time = 0.0

        return {
            "raw_prediction": raw,
            "confidence":     pred["confidence"],
            "candidates":     pred["candidates"],
            "validated":      validated,
            "letter":         validated_letter,
            "word_complete":  word_complete,
            "word":           word,
            "word_buffer":    "".join(self.word_buffer),
        }
