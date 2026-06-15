# GantConnect — Serveur ASL

Serveur Flask de reconnaissance de la langue des signes américaine (ASL)
à partir des données brutes d'un gant ESP32 (5 capteurs flex + MPU9250).

---

## Architecture

```
ESP32 (flex + IMU)
      │
      │  POST /data  (JSON toutes les 100ms)
      ▼
┌─────────────────────────────────────────┐
│              server.py                  │
│                                         │
│  ┌──────────────┐  ┌─────────────────┐  │
│  │ calibration  │  │   classifier    │  │
│  │   .py        │  │      .py        │  │
│  │              │  │                 │  │
│  │ min/max ADC  │  │ normalize →     │  │
│  │ par capteur  │  │ distance →      │  │
│  └──────────────┘  │ stabilisation → │  │
│                    │ mot complet     │  │
│                    └─────────────────┘  │
│                           │             │
│                    firebase_client.py   │
└─────────────────────────────────────────┘
                            │
                            ▼
                       Firestore
              sessions/{id}/letters/
              sessions/{id}/words/
```

---

## Installation

```bash
pip install -r requirements.txt
```

---

## Configuration Firebase

1. Dans la console Firebase → Paramètres du projet → Comptes de service
2. Télécharger `serviceAccountKey.json`
3. Définir la variable d'environnement :

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/chemin/vers/serviceAccountKey.json"
```

Sur Heroku :
```bash
heroku config:set GOOGLE_APPLICATION_CREDENTIALS="$(cat serviceAccountKey.json)"
```
> ⚠️ Sur Heroku, il vaut mieux stocker le JSON entier comme variable d'env
> et adapter `firebase_client.py` pour le lire depuis `os.environ.get("FIREBASE_KEY")`.

---

## Lancement local

```bash
python server.py
```

## Déploiement Heroku

```bash
heroku create gantconnect-server
git push heroku main
heroku config:set GOOGLE_APPLICATION_CREDENTIALS=...
```

---

## Endpoints

| Méthode | URL       | Description                          |
|---------|-----------|--------------------------------------|
| GET     | /health   | Healthcheck                          |
| POST    | /start    | Démarre session + calibration 60s    |
| POST    | /data     | Trame ESP32 (flex + IMU)             |
| POST    | /end      | Termine la session                   |
| GET     | /status   | Statut de la session en cours        |

---

## Format JSON — ESP32 → Serveur

```json
{
  "session_id": "session_20240601_143022",
  "flex1": 1800,
  "flex2": 300,
  "flex3": 400,
  "flex4": 350,
  "flex5": 320,
  "pitch": -12.5,
  "roll": 3.2,
  "yaw": 87.0
}
```

**Ordre des capteurs flex :**
- flex1 → Pouce
- flex2 → Index
- flex3 → Majeur
- flex4 → Annulaire
- flex5 → Auriculaire

---

## Pipeline complet d'une trame

```
ESP32 envoie POST /data
         │
         ▼
[Calibration terminée ?]
    Non → Mise à jour min/max ADC, retourne remaining_seconds
    Oui ↓
         ▼
Normalisation : ADC brut → [0.0, 1.0] selon min/max calibrés
         │
         ▼
Prédiction : distance de Manhattan vs 35 templates (26 lettres + 9 chiffres)
         │
         ▼
[Ambiguïté entre 2 lettres proches ?]
    Oui → Résolution par pitch/roll du MPU9250
    Non ↓
         │
         ▼
Stabilisation : même lettre 6 trames de suite → validée
         │
         ▼
[Lettre validée ?]
    Oui → Firebase /letters + retour dans réponse JSON
         │
         ▼
[Pause > 1.5s sans lettre ?]
    Oui → Mot complet → Firebase /words
```

---

## Calibration

Au démarrage (`POST /start`), le serveur entre en phase de calibration.
L'utilisateur bouge librement ses 5 doigts pendant **60 secondes**.
Le serveur enregistre les valeurs ADC min et max pour chaque capteur.

Ensuite toutes les valeurs sont normalisées :
```
valeur_normalisée = (ADC_brut - ADC_min) / (ADC_max - ADC_min)
```

Résultat : 0.0 = doigt tendu, 1.0 = doigt plié — **indépendant du gant et de la main**.

---

## Structure Firestore

```
sessions/
  └── session_20240601_143022/
        ├── created_at: timestamp
        ├── status: "active" | "closed"
        ├── letters/
        │     ├── {auto} → { letter: "H", confidence: 0.42, timestamp }
        │     └── {auto} → { letter: "I", confidence: 0.31, timestamp }
        └── words/
              └── {auto} → { word: "HI", letter_count: 2, timestamp }
```
