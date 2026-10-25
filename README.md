# AI Suspicious Activity Detection

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A real‑time computer‑vision system that monitors video streams and automatically detects **suspicious activities** such as **theft**, **fights**, and **weapon appearances**. It leverages a YOLOv8 (or YOLOv6) object detector, a lightweight face recognizer, multi‑object tracking, and Telegram alerts to provide fast, actionable incident reporting.

---

## 📖 Overview

- **Video input** – RTSP camera stream or local video file.
- **Object detection** – YOLO model (`models/yolov26n.pt`).
- **Activity logic** – Threshold‑based heuristics for theft, fights and weapons.
- **Tracking** – Deep SORT style tracker that keeps stable person IDs.
- **Face recognition** – Optional recogniser to attach names to tracked people.
- **Event recording** – Clips are saved with pre‑ and post‑event padding.
- **Telegram alerts** – Immediate notification with a snapshot and video clip.

The pipeline runs on a single thread for video capture and a thread‑pool for sending alerts, keeping CPU usage low while maintaining near‑real‑time performance.

---

## ✨ Features

- **Multi‑class activity detection** (theft, fight, weapon).
- **Speed‑based fight detection** using movement tracking.
- **IOU‑based theft detection** with configurable thresholds.
- **Dynamic event smoothing** to bridge short detection gaps.
- **Stable identity handling** via a short‑term voting memory.
- **Configurable confidence & IOU thresholds**.
- **Graceful handling of RTSP reconnection**.
- **Extensible architecture** – add new activities by extending `src/activity`.

---

## 🏗️ Architecture

```mermaid
graph TD;
    VideoSource[Video Source] -->|frames| VideoReader;
    VideoReader -->|frame| ObjectDetector;
    ObjectDetector --> Tracker;
    Tracker --> TrackingUtils;
    TrackingUtils -->|persons, objects, weapons| SuspiciousActivityDetector;
    VideoReader --> FaceRecognizer (every 3 frames);
    FaceRecognizer --> IdentityMemory;
    IdentityMemory -->|stable names| Overlay;
    SuspiciousActivityDetector --> EventRecorder;
    EventRecorder --> TelegramAlert;
    classDef python fill:#f9f9f9,stroke:#333,stroke-width:1px;
    class VideoReader,ObjectDetector,Tracker,FaceRecognizer,SuspiciousActivityDetector,EventRecorder,TelegramAlert python;
```

---

## 🛠️ Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/ai-suspicious-activity-detection.git
cd ai-suspicious-activity-detection

# Set up a virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Required environment variables
Create a `.env` file in the project root:

```dotenv
# RTSP URL or local video path (fallback to webcam index 0)
EZVIZ_RTSP_URL=rtsp://username:password@camera-ip:554/ch1/main

# Telegram bot configuration (optional – alerts are disabled if missing)
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

---

## ▶️ Running the Application

```bash
# Activate the virtual environment if not already active
source .venv/bin/activate

# Start detection (uses video source from .env or defaults to webcam)
python main.py
```

Press **`q`** in the display window to stop.

### Command‑line options (future extension)
- `--config path/to/config.yaml` – load a custom configuration file.
- `--no‑display` – run headless (useful on servers).

---

## 📤 Telegram Alerts

If `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are set, the system will send:
1. A text message indicating the activity type.
2. A short video clip of the incident.

The alerts are dispatched via a `ThreadPoolExecutor` to avoid blocking the detection loop.

---

## 📂 Project Structure

```
AI Suspicious Activity Detection/
├─ src/                     # Source package
│   ├─ activity/            # Activity detectors (theft, fight, weapon)
│   ├─ alerts/              # TelegramAlert implementation
│   ├─ config/              # Settings (settings.py)
│   ├─ detection/           # YOLO wrapper
│   ├─ events/              # EventRecorder for video clips
│   ├─ recognition/         # Face recogniser
│   ├─ tracking/            # Object and movement tracking
│   ├─ utils/               # Helper utilities
│   └─ video/               # VideoReader abstraction
├─ tests/                   # Unit / integration tests
├─ requirements.txt         # Python dependencies
├─ .env                     # Environment variables (not tracked)
├─ main.py                  # Entry point
└─ README.md                # This file
```

---

## 🤝 Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

1. Fork the repository.
2. Create a feature branch (`git checkout -b feat/your-feature`).
3. Write tests for any new functionality.
4. Ensure the existing test suite passes (`pytest`).
5. Submit a pull request with a clear description.

---

## 📄 License

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.
