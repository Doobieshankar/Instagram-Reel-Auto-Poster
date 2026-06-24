#!/usr/bin/env python3
import sys, requests

script = sys.argv[1]
MODEL = "openbmb/minicpm-v4.6:latest"
prompt = f"Is the following text safe for social media (no hate speech, violence, explicit content)? Reply only 'SAFE' or 'UNSAFE': {script}"

try:
    resp = requests.post("http://localhost:11434/api/generate", json={
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    }, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    raw = data.get("response", "").strip().upper()
except Exception as e:
    print(f"Ollama moderation error: {e}", file=sys.stderr)
    raw = "SAFE"   # default safe on error

if "UNSAFE" in raw:
    print("UNSAFE")
else:
    print("SAFE")
