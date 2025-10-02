# Multi‑Agent Debate Video Starter (Minimal)

Bu depo, **2 tartışmacı + 1 moderatör** ile 4–5 turluk bir tartışmayı üretir,
**9 hakem** ile puanlar, **OpenAI TTS** ile seslendirme yapar, **SRT** altyazı
oluşturur ve **FFmpeg** ile tek bir MP4 videoya dönüştürür. Avatar yok — *minimal* üretim.

## 1) Ön Koşullar
- macOS (Apple Silicon uyumlu)
- **Python 3.10+**
- **FFmpeg** (`brew install ffmpeg`)
- **OpenAI API anahtarı** (ChatGPT Business olsa da **API ayrı** faturalıdır).
  - `export OPENAI_API_KEY="...your key..."`

## 2) Kurulum
```bash
python -m venv .venv && source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

## 3) Hızlı Çalıştırma
```bash
cp config.example.yaml config.yaml
python make_video.py --topic "Should we adopt universal basic income?" --rounds 5 --target-min 13
# veya sadece:
python make_video.py
```
Çıktılar `out/` klasöründe: `final.mp4`, `transcript.json`, `scores.json`, `debate.srt`, `audio/`

## Kaynaklar
- OpenAI **Text‑to‑Speech** rehberi.
- OpenAI **Chat/Responses** API rehberi.
- FFmpeg altyazı yakma rehberi (SRT).
