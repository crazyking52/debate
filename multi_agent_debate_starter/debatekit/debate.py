import os, json, time, random, yaml
from dataclasses import dataclass, asdict
from typing import List, Dict, Any

from openai import OpenAI

@dataclass
class Utterance:
    speaker: str
    role: str
    text: str
    round: int
    approx_words: int | None = None
    audio_path: str | None = None
    start_ms: int | None = None
    end_ms: int | None = None

@dataclass
class DebateTranscript:
    topic: str
    rounds: int
    names: Dict[str, str]
    utterances: List[Utterance]

SYSTEM_MODERATOR = "You are a strict debate moderator. Enforce turn-taking, keep answers concise, and avoid repetition. Each debater response should be around {words} words. Keep debate civil and on-topic, and do not invent facts."
SYSTEM_DEBATER_A = "You are Debater A. You strongly advocate FOR the topic. Be persuasive and structured. Cite examples where possible. Avoid repeating yourself. Aim for ~{words} words per turn."
SYSTEM_DEBATER_B = "You are Debater B. You strongly argue AGAINST the topic. Be persuasive and structured. Address the opponent's strongest points (steelman). Avoid repetition. Aim for ~{words} words per turn."
MODERATOR_OPEN = "Open the debate with a 2–3 sentence overview of the topic and the rules (4-5 rounds). Announce each speaker's name. Keep it under {words} words."
MODERATOR_CROSS = "Briefly transition to the cross-examination phase for this round. Ask one pointed question to each side, no more than {words} words total."
MODERATOR_CLOSE = "Close the debate in 2–3 sentences. Summarize the main clash without picking a winner. Stay under {words} words."

def load_config(path: str) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)

def _chat(client: OpenAI, model: str, sys_prompt: str, user_prompt: str, seed: int | None = None) -> str:
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role":"system","content":sys_prompt},{"role":"user","content":user_prompt}],
        temperature=0.8,
        seed=seed
    )
    return resp.choices[0].message.content.strip()

def generate_debate(config_path="config.yaml", topic_arg: str | None = None, rounds_arg: int | None = None) -> DebateTranscript:
    cfg = load_config(config_path)
    topic = topic_arg or cfg.get("topic")
    rounds = rounds_arg or int(cfg.get("rounds", 5))
    words = int(cfg.get("words_per_turn", 180))
    model = cfg.get("model", "gpt-4o-mini")
    names = cfg.get("names", {"debater_a":"A","debater_b":"B","moderator":"Moderator"})

    client = OpenAI()
    A, B, M = names["debater_a"], names["debater_b"], names["moderator"]
    utters: list[Utterance] = []

    mod_open = _chat(client, model, SYSTEM_MODERATOR.format(words=words),
                     MODERATOR_OPEN.format(words=words)+f"\\n\\nTopic: {topic}\\nDebaters: {A} (Pro) vs {B} (Con)")
    utters.append(Utterance(speaker=M, role="moderator", text=mod_open, round=0))

    for r in range(1, rounds+1):
        a_text = _chat(client, model, SYSTEM_DEBATER_A.format(words=words),
                       f"Round {r}. Topic: {topic}. Approximately {words} words.", seed=random.randint(1,10**9))
        utters.append(Utterance(speaker=A, role="debater_a", text=a_text, round=r, approx_words=words))

        b_text = _chat(client, model, SYSTEM_DEBATER_B.format(words=words),
                       f"Round {r}. Topic: {topic}. Respond to Debater A. Approximately {words} words.", seed=random.randint(1,10**9))
        utters.append(Utterance(speaker=B, role="debater_b", text=b_text, round=r, approx_words=words))

        mod_cross = _chat(client, model, SYSTEM_MODERATOR.format(words=words),
                          MODERATOR_CROSS.format(words=words)+f"\\nRound {r}. Keep it short.")
        utters.append(Utterance(speaker=M, role="moderator", text=mod_cross, round=r))

    mod_close = _chat(client, model, SYSTEM_MODERATOR.format(words=words),
                      MODERATOR_CLOSE.format(words=words)+f"\\nThank {A} and {B}.")
    utters.append(Utterance(speaker=M, role="moderator", text=mod_close, round=rounds+1))

    return DebateTranscript(topic=topic, rounds=rounds, names=names, utterances=utters)

def save_transcript(obj: DebateTranscript, path: str):
    payload = {
        "topic": obj.topic,
        "rounds": obj.rounds,
        "names": obj.names,
        "utterances": [asdict(u) for u in obj.utterances],
        "created_at": int(time.time())
    }
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--topic", default=None)
    ap.add_argument("--rounds", type=int, default=None)
    ap.add_argument("--out", default="out/transcript.json")
    args = ap.parse_args()
    tx = generate_debate(args.config, args.topic, args.rounds)
    save_transcript(tx, args.out)
    print("Transcript saved to", args.out)
