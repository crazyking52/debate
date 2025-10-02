import os, json, random, yaml
from typing import Dict, Any, List
from openai import OpenAI

JUDGE_PROMPT = """You are a meticulous impartial judge scoring a formal debate.
Evaluate the debate overall, across ALL rounds, using the following 10 criteria:
logic, evidence, counterargument, clarity, sources, breadth, neutrality, consistency, persuasion, accuracy.
Return STRICT JSON with integer scores 0-100 for each criterion, a short 'rationale', and 'winner' among {a} or {b}.
Keep rationale under 120 words. Think step-by-step but only output JSON.
"""

def load_yaml(path="config.yaml"):
    with open(path,"r") as f:
        return yaml.safe_load(f)

def load_transcript(path="out/transcript.json") -> Dict[str, Any]:
    with open(path,"r") as f:
        return json.load(f)

def run_one_judge(client, model: str, transcript: Dict[str, Any], seed: int, persona: str) -> Dict[str, Any]:
    names = transcript["names"]
    a = names["debater_a"]
    b = names["debater_b"]
    topic = transcript["topic"]

    context = f"Topic: {topic}\\nDebaters: {a} (Pro) vs {b} (Con)\\n\\nTRANSCRIPT:\\n"
    for u in transcript["utterances"]:
        context += f"[{u['role']}|{u['speaker']}|round {u['round']}] {u['text']}\\n\\n"

    sys = "You are a fair, independent judge. " + persona

    msg = client.chat.completions.create(
        model=model,
        messages=[
            {"role":"system","content": sys},
            {"role":"user","content": JUDGE_PROMPT.format(a=a,b=b) + "\\n\\n" + context}
        ],
        temperature=0.7,
        seed=seed,
        response_format={"type":"json_object"}
    )
    out = msg.choices[0].message.content
    try:
        data = json.loads(out)
    except Exception:
        data = {"error": "invalid_json", "raw": out}
    data["_seed"] = seed
    data["_persona"] = persona
    return data

def run_judges(config_path="config.yaml", transcript_path="out/transcript.json", out_path="out/scores.json"):
    cfg = load_yaml(config_path)
    transcript = load_transcript(transcript_path)
    judges = int(cfg.get("judges",{}).get("count", 9))
    model = cfg.get("judge_model","gpt-4o-mini")
    seed_variation = bool(cfg.get("judges",{}).get("seed_variation", True))

    client = OpenAI()

    personas = [
        "Focus on logical rigor and structure.",
        "Focus on use of concrete evidence and citations.",
        "Focus on addressing opponent arguments (steelman).",
        "Focus on clarity and pedagogy.",
        "Focus on breadth and coverage of relevant angles.",
        "Focus on tone, neutrality and fairness.",
        "Focus on self-consistency and lack of contradictions.",
        "Focus on persuasiveness for an undecided audience.",
        "Focus on factuality and accuracy."
    ]

    results: List[Dict[str,Any]] = []
    for i in range(judges):
        seed = random.randint(1, 10**9) if seed_variation else 42
        persona = personas[i % len(personas)]
        res = run_one_judge(client, model, transcript, seed, persona)
        results.append(res)

    winners = [r.get("winner") for r in results if isinstance(r, dict) and "winner" in r]
    winner = max(set(winners), key=winners.count) if winners else None

    keys = ["logic","evidence","counterargument","clarity","sources","breadth","neutrality","consistency","persuasion","accuracy"]
    sums = {k:0 for k in keys}
    counts = {k:0 for k in keys}
    for r in results:
        c = r.get("criteria") if isinstance(r, dict) else None
        if not isinstance(c, dict): 
            continue
        for k in keys:
            if isinstance(c.get(k), int):
                sums[k]+=c[k]; counts[k]+=1
    avgs = {k: (sums[k]/counts[k] if counts[k] else None) for k in keys}

    out = {"judges_raw": results, "aggregate": {"winner": winner, "averages": avgs, "count": judges}}
    os.makedirs("out", exist_ok=True)
    with open(out_path,"w") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("Scores saved to", out_path)

if __name__ == "__main__":
    run_judges()
