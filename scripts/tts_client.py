#!/usr/bin/env python3
import requests, sys, os, uuid

text = sys.argv[1]
url = f"http://localhost:5002/tts?text={requests.utils.quote(text)}&lang=en"

resp = requests.get(url)
if resp.status_code == 200:
    output_dir = os.path.expanduser("~/insta-pipeline/output/tts")
    os.makedirs(output_dir, exist_ok=True)
    filename = f"tts_{uuid.uuid4().hex[:8]}.wav"
    filepath = os.path.join(output_dir, filename)
    with open(filepath, "wb") as f:
        f.write(resp.content)
    print(filepath)
else:
    print(f"Error generating TTS, status {resp.status_code}", file=sys.stderr)
    sys.exit(1)
