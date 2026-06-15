# =============================================================================
# SERVEUR PRINCIPAL — GantConnect ASL
# =============================================================================
# Framework : Flask
# Déploiement : Cloud (Heroku / VPS)
#
# Endpoints :
#   POST /start          → Démarre une nouvelle session + calibration
#   POST /data           → Reçoit les données de l'ESP32 (flex + IMU)
#   POST /end            → Termine la session
#   GET  /status         → Statut de la session en cours
#   GET  /health         → Healthcheck (pour Heroku)
#
# Format JSON attendu de l'ESP32 :
#   {
#     "session_id": "session_20240601_143022",
#     "flex1": 1800,   // pouce      (ADC 12 bits, 0-4095)
#     "flex2": 300,    // index
#     "flex3": 400,    // majeur
#     "flex4": 350,    // annulaire
#     "flex5": 320,    // auriculaire
#     "pitch": -12.5,  // MPU9250 (degrés)
#     "roll":   3.2,
#     "yaw":   87.0
#   }
# =============================================================================

import os
import logging
import uuid
from datetime import datetime, timezone

from flask import Flask, request, jsonify
from flask_cors import CORS

from calibration    import Calibration
from classifier     import Classifier
from firebase_client import init_firebase, create_session, close_session, send_letter, send_word

# ─── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s"
)
logger = logging.getLogger(__name__)

# ─── Configuration ────────────────────────────────────────────────────────────
FIREBASE_DB_URL = os.environ.get("FIREBASE_DB_URL", "https://voxmanus-f01de-default-rtdb.firebaseio.com/")

# ─── Flask ────────────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)

# ─── État global de la session (une session à la fois) ───────────────────────
# Pour multi-session simultanée, remplacer par un dict {session_id: SessionState}
class SessionState:
    def __init__(self, session_id: str):
        self.session_id  = session_id
        self.calibration = Calibration()
        self.classifier  = Classifier()
        self.created_at  = datetime.now(timezone.utc)
        self.frame_total = 0

    def to_dict(self):
        return {
            "session_id":  self.session_id,
            "calibrating": not self.calibration.is_done,
            "frame_total": self.frame_total,
            "word_buffer": "".join(self.classifier.word_buffer),
            "created_at":  self.created_at.isoformat()
        }


_session: SessionState | None = None


# =============================================================================
# ENDPOINTS
# =============================================================================

@app.route("/health", methods=["GET"])
def health():
    """Healthcheck pour Heroku / load balancer."""
    return jsonify({"status": "ok"}), 200


@app.route("/start", methods=["POST"])
def start_session():
    """
    Démarre une nouvelle session et lance la phase de calibration.
    Corps JSON optionnel : { "session_id": "..." }
    Si non fourni, un ID est généré automatiquement.
    """
    global _session

    body       = request.get_json(silent=True) or {}
    session_id = body.get("session_id") or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

    _session = SessionState(session_id)
    create_session(session_id)

    logger.info("🟢 Session démarrée : %s", session_id)
    return jsonify({
        "session_id":          session_id,
        "calibration_seconds": _session.calibration.duration,
        "message":             "Bougez tous vos doigts pendant 60 secondes pour calibrer."
    }), 200


@app.route("/data", methods=["POST"])
def receive_data():
    """
    Reçoit une trame de l'ESP32 (flex + IMU).
    Gère automatiquement la phase de calibration puis la reconnaissance.
    """
    global _session

    if _session is None:
        return jsonify({"error": "Aucune session active. Appelez /start d'abord."}), 400

    body = request.get_json(silent=True)
    if not body:
        return jsonify({"error": "Corps JSON manquant."}), 400

    # ── Extraction des données ────────────────────────────────────────────
    try:
        flex_raw = [
            int(body["flex1"]),
            int(body["flex2"]),
            int(body["flex3"]),
            int(body["flex4"]),
            int(body["flex5"]),
        ]
    except (KeyError, ValueError) as e:
        return jsonify({"error": f"Données flex manquantes ou invalides : {e}"}), 400

    imu_data = {
        "pitch": float(body.get("pitch", 0)),
        "roll":  float(body.get("roll",  0)),
        "yaw":   float(body.get("yaw",   0)),
    }

    _session.frame_total += 1

    # ── Phase de calibration ──────────────────────────────────────────────
    if not _session.calibration.is_done:
        cal_status = _session.calibration.update(flex_raw)
        return jsonify({
            "phase":     "calibration",
            "remaining": cal_status["remaining"],
            "frames":    cal_status["frame_count"],
            "message":   f"Calibration en cours... {cal_status['remaining']}s restantes."
        }), 200

    # ── Phase de reconnaissance ───────────────────────────────────────────
    normalized = _session.calibration.normalize(flex_raw)
    result     = _session.classifier.process_frame(normalized, imu_data)

    response = {
        "phase":          "signing",
        "raw_prediction": result["raw_prediction"],
        "confidence":     round(result["confidence"], 3),
        "word_buffer":    result["word_buffer"],
    }

    # ── Lettre validée → Firebase ─────────────────────────────────────────
    if result["validated"] and result["letter"]:
        send_letter(
            session_id  = _session.session_id,
            word_buffer = result["word_buffer"]
        )
        response["validated_letter"] = result["letter"]
        logger.info("🔤 Mot partiel mis à jour : %s", result["word_buffer"])

    # ── Mot complet → Firebase ────────────────────────────────────────────
    if result["word_complete"] and result["word"]:
        send_word(
            session_id   = _session.session_id,
            word         = result["word"],
            letter_count = len(result["word"])
        )
        response["word_complete"] = result["word"]
        logger.info("💬 Mot envoyé à Firebase : %s", result["word"])

    return jsonify(response), 200


@app.route("/end", methods=["POST"])
def end_session():
    """Termine la session en cours et ferme le document Firebase."""
    global _session

    if _session is None:
        return jsonify({"error": "Aucune session active."}), 400

    # Envoyer le mot en cours s'il y en a un
    if _session.classifier.word_buffer:
        remaining_word = "".join(_session.classifier.word_buffer)
        send_word(
            session_id   = _session.session_id,
            word         = remaining_word,
            letter_count = len(remaining_word)
        )
        logger.info("💬 Mot final envoyé : %s", remaining_word)

    close_session(_session.session_id)

    summary = {
        "session_id":  _session.session_id,
        "frame_total": _session.frame_total,
        "message":     "Session terminée."
    }

    _session = None
    return jsonify(summary), 200


@app.route("/status", methods=["GET"])
def status():
    """Retourne l'état complet de la session en cours."""
    if _session is None:
        return jsonify({"active": False}), 200
    return jsonify({"active": True, **_session.to_dict()}), 200


# =============================================================================
# LANCEMENT
# =============================================================================

if __name__ == "__main__":
    # Initialisation Firebase au démarrage
    init_firebase(FIREBASE_DB_URL)

    port = int(os.environ.get("PORT", 5000))
    logger.info("🚀 Serveur GantConnect démarré sur le port %d", port)
    app.run(host="0.0.0.0", port=port, debug=False)
