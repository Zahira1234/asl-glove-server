# =============================================================================
# FIREBASE CLIENT — Envoi des lettres et mots reconnus (Realtime Database)
# =============================================================================

import os
import logging
from datetime import datetime, timezone

import firebase_admin
from firebase_admin import credentials, db

logger = logging.getLogger(__name__)

_db_initialized = False

def init_firebase(db_url: str = "https://voxmanus-f01de-default-rtdb.firebaseio.com/"):
    """
    Initialise la connexion Firebase Realtime Database.
    Cherche les credentials dans la variable d'env GOOGLE_APPLICATION_CREDENTIALS
    (chemin vers le fichier serviceAccountKey.json).
    """
    global _db_initialized
    if _db_initialized:
        return  # Déjà initialisé

    key_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not key_path:
        raise EnvironmentError(
            "Variable d'environnement GOOGLE_APPLICATION_CREDENTIALS manquante. "
            "Mets le chemin vers ton serviceAccountKey.json."
        )

    cred = credentials.Certificate(key_path)
    firebase_admin.initialize_app(cred, {
        "databaseURL": db_url
    })
    _db_initialized = True
    logger.info("🔥 Firebase Realtime DB connecté.")


# =============================================================================
# FONCTIONS D'ENVOI
# =============================================================================

def send_letter(session_id: str, word_buffer: str):
    """
    Enregistre un mot partiel dans Firebase Realtime Database (isFinal=False).
    """
    try:
        ref = db.reference(f"rencontreSessions/{session_id}/glove")
        ref.update({
            "text": word_buffer,
            "isFinal": False,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        logger.debug("🔤 Firebase ← mot partiel '%s'", word_buffer)
    except Exception as e:
        logger.error("❌ Erreur Firebase (send_letter) : %s", e)


def send_word(session_id: str, word: str, letter_count: int = 0):
    """
    Enregistre un mot complet dans Firebase Realtime Database (isFinal=True).
    """
    try:
        ref = db.reference(f"rencontreSessions/{session_id}/glove")
        ref.update({
            "text": word,
            "isFinal": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        logger.info("💬 Firebase ← mot complet '%s'", word)
    except Exception as e:
        logger.error("❌ Erreur Firebase (send_word) : %s", e)


def create_session(session_id: str) -> str:
    """
    Initialise le chemin dans Realtime Database pour la nouvelle session.
    """
    try:
        ref = db.reference(f"rencontreSessions/{session_id}/glove")
        ref.set({
            "text": "",
            "isFinal": False,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        logger.info("📋 Session Firebase créée : %s", session_id)
    except Exception as e:
        logger.error("❌ Erreur Firebase (create_session) : %s", e)
    return session_id


def close_session(session_id: str):
    """Marque la session comme terminée."""
    try:
        ref = db.reference(f"rencontreSessions/{session_id}/glove")
        ref.update({
            "status": "closed",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        logger.info("🔒 Session Firebase fermée : %s", session_id)
    except Exception as e:
        logger.error("❌ Erreur Firebase (close_session) : %s", e)

