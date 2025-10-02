import os, argparse, shutil
from pathlib import Path
from debate import generate_debate, save_transcript
from judges import run_judges
from tts import synthesize
from render import render

def ensure_config(target="config.yaml"):
    if not Path(target).exists():
        shutil.copyfile("config.example.yaml", target)
        print("config.yaml oluşturuldu. Gerekirse düzenleyin.")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--topic", default=None)
    ap.add_argument("--rounds", type=int, default=None)
    ap.add_argument("--target-min", type=int, default=None)
    args = ap.parse_args()

    ensure_config()
    os.makedirs("out", exist_ok=True)

    tx = generate_debate(topic_arg=args.topic, rounds_arg=args.rounds)
    save_transcript(tx, "out/transcript.json")

    run_judges()
    audio_path, srt_path = synthesize()
    final_path = render(audio_path, srt_path, out_path="out/final.mp4")
    print("Bitti ->", final_path)

if __name__ == "__main__":
    main()
