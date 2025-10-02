import subprocess
from pathlib import Path

def _probe_duration(path:str) -> float:
    cmd = ["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1", path]
    out = subprocess.check_output(cmd).decode().strip()
    return float(out)

def render(final_audio: str, srt_path: str, out_path="out/final.mp4", resolution="1280x720", bg_color="black"):
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    dur = _probe_duration(final_audio)
    cmd = [
        "ffmpeg","-y",
        "-f","lavfi","-i", f"color=c={bg_color}:s={resolution}:d={dur}",
        "-i", final_audio,
        "-vf", f"subtitles={srt_path}",
        "-c:v","libx264","-pix_fmt","yuv420p",
        "-c:a","aac","-shortest",
        out_path
    ]
    subprocess.run(cmd, check=True)
    print("Rendered:", out_path)
    return out_path

if __name__ == "__main__":
    import sys
    render(sys.argv[1], sys.argv[2])
