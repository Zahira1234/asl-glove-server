# =============================================================================
# CALIBRATION — Phase d'1 minute au démarrage
# =============================================================================
# L'utilisateur bouge librement ses doigts pendant 60 secondes.
# Le système capture les valeurs ADC min/max réelles pour CETTE main.
# Ensuite, toutes les valeurs brutes sont normalisées vers [0.0, 1.0].
# =============================================================================

import time
import logging

logger = logging.getLogger(__name__)

CALIBRATION_DURATION = 60  # secondes


class Calibration:
    def __init__(self, duration=CALIBRATION_DURATION):
        self.duration = duration
        self.start_time = None
        self.is_done = False

        # Valeurs extrêmes observées par capteur [pouce, index, majeur, annulaire, auriculaire]
        self.flex_min = [4095] * 5
        self.flex_max = [0]    * 5

        # Nombre de trames reçues (pour vérifier que l'ESP envoie bien)
        self.frame_count = 0

    def start(self):
        self.start_time = time.time()
        logger.info("🖐️  Calibration démarrée — bougez tous vos doigts pendant %ds", self.duration)

    def update(self, flex_raw: list) -> dict:
        """
        Appeler à chaque trame reçue pendant la phase de calibration.
        Retourne un dict avec le statut et le temps restant.
        """
        if self.is_done:
            return {"done": True, "remaining": 0}

        if self.start_time is None:
            self.start()

        # Mise à jour des extremes
        for i in range(5):
            val = flex_raw[i]
            if val < self.flex_min[i]:
                self.flex_min[i] = val
            if val > self.flex_max[i]:
                self.flex_max[i] = val

        self.frame_count += 1
        elapsed = time.time() - self.start_time
        remaining = max(0, self.duration - elapsed)

        if remaining == 0:
            self._finalize()

        return {
            "done": self.is_done,
            "remaining": int(remaining),
            "frame_count": self.frame_count
        }

    def _finalize(self):
        self.is_done = True
        logger.info("✅ Calibration terminée après %d trames.", self.frame_count)
        logger.info("   flex_min = %s", self.flex_min)
        logger.info("   flex_max = %s", self.flex_max)

        # Vérifier que chaque capteur a bien bougé
        for i, (mn, mx) in enumerate(zip(self.flex_min, self.flex_max)):
            span = mx - mn
            finger = ["Pouce", "Index", "Majeur", "Annulaire", "Auriculaire"][i]
            if span < 200:
                logger.warning(
                    "⚠️  %s : plage trop faible (%d ADC). "
                    "Le doigt n'a peut-être pas été bougé.", finger, span
                )
            else:
                logger.info("   ✔ %s : plage OK (%d ADC)", finger, span)

    def normalize(self, flex_raw: list) -> list:
        """
        Convertit les 5 valeurs ADC brutes en valeurs normalisées [0.0, 1.0].
        0.0 = doigt complètement tendu
        1.0 = doigt complètement plié

        Si le span d'un capteur est trop faible (< 200 ADC), on retourne 0.5
        (position neutre) pour ne pas fausser la reconnaissance.
        """
        normalized = []
        for i in range(5):
            span = self.flex_max[i] - self.flex_min[i]
            if span < 200:
                normalized.append(0.5)  # Données insuffisantes → neutre
            else:
                val = (flex_raw[i] - self.flex_min[i]) / span
                normalized.append(max(0.0, min(1.0, val)))
        return normalized

    def to_dict(self) -> dict:
        """Sérialisation pour sauvegarde / debug."""
        return {
            "flex_min": self.flex_min,
            "flex_max": self.flex_max,
            "frame_count": self.frame_count,
            "is_done": self.is_done
        }
