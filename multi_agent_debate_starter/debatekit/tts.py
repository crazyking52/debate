import os, json, subprocess
from pathlib import Path
from typing import Dict, Any
import yaml
from pydub import AudioSegment
from openai import OpenAI

def load_yaml(path="config.yaml"):
    with open(path,"r") as f:
        return yaml.safe_load(f)

def load_transcript(path="out/transcript.json") -> Dict[str, Any]:
    with open(path,"r") as f:
        return json.load(f)

def tts_chunk(client, model: str, text: str, voice: str, out_path: str):
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with client.audio.speech.with_streaming_response.create(
        model=model, voice=voice, input=text, format="mp3"
    ) as response:
        response.stream_to_file(out_path)

def seconds_to_srt_time(s: float) -> str:
    hh = int(s//3600); mm = int((s%3600)//60); ss = int(s%60); ms = int((s - int(s))*1000)
    return f"{hh:02d}:{mm:02d}:{ss:02d},{ms:03d}"

def synthesize(config_path="config.yaml", transcript_path="out/transcript.json", out_dir="out"):
    cfg = load_yaml(config_path)
    tx = load_transcript(transcript_path)
    tts_model = cfg.get("tts_model","tts-1")
    voices = cfg.get("voices", {"debater_a":"alloy","debater_b":"verse","moderator":"sage"})
    client = OpenAI()

    audio_root = Path(out_dir)/"audio"/"segments"
    audio_root.mkdir(parents=True, exist_ok=True)

    for idx, u in enumerate(tx["utterances"], start=1):
        role = u["role"]; voice = voices.get(role, "alloy")
        path = audio_root / f"{idx:03d}_{role}.mp3"
        tts_chunk(client, tts_model, u["text"], voice, str(path))
        u["audio_path"] = str(path)

    concat_list = Path(out_dir)/"audio"/"list.txt"
    concat_list.parent.mkdir(parents=True, exist_ok=True)
    with open(concat_list,"w") as f:
        for u in tx["utterances"]:
            f.write(f"file '{u['audio_path']}'\n")

    final_audio = Path(out_dir)/"audio"/"debate_audio.mp3"
    cmd = ["ffmpeg","-y","-f","concat","-safe","0","-i",str(concat_list),"-c","copy",str(final_audio)]
    subprocess.run(cmd, check=True)

    current = 0.0
    for u in tx["utterances"]:
        seg = AudioSegment.from_file(u["audio_path"], format="mp3")
        dur = seg.duration_seconds
        u["start_ms"] = int(current*1000); u["end_ms"] = int((current+dur)*1000)
        current += dur

    with open(transcript_path,"w") as f:
        json.dump(tx, f, ensure_ascii=False, indent=2)

    srt_path = Path(out_dir)/"debate.srt"
    with open(srt_path,"w", encoding="utf-8") as srt:
        for i, u in enumerate(tx["utterances"], start=1):
            start = seconds_to_srt_time(u["start_ms"]/1000.0)
            end = seconds_to_srt_time(u["end_ms"]/1000.0)
            speaker = u["speaker"]; text = u["text"].replace("\n"," ").strip()
            srt.write(f"{i}\n{start} --> {end}\n[{speaker}] {text}\n\n")

    print("Audio & SRT created.", final_audio, srt_path)
    return str(final_audio), str(srt_path)

if __name__ == "__main__":
    synthesize()
