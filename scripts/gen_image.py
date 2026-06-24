#!/usr/bin/env python3
"""
gen_image.py <prompt>

Submits a ComfyUI workflow and prints ONLY the final image path to stdout.
All debug/status goes to stderr so the shell can safely capture the path.
"""
import requests, json, sys, time, os

prompt_text = sys.argv[1]
COMFYUI_URL = "http://localhost:8188"

# Portrait crop for Reels (ComfyUI will generate 512x512, we upscale in render)
workflow = {
    "3": {
        "class_type": "KSampler",
        "inputs": {
            "seed": int(time.time()) % 2**32,   # randomise seed each run
            "steps": 4,
            "cfg": 1.8,
            "sampler_name": "lcm",
            "scheduler": "normal",
            "denoise": 1,
            "model": ["4", 0],
            "positive": ["6", 0],
            "negative": ["7", 0],
            "latent_image": ["5", 0],
        },
    },
    "4": {
        "class_type": "CheckpointLoaderSimple",
        "inputs": {"ckpt_name": "dreamshaper_8LCM.safetensors"},
    },
    "5": {
        "class_type": "EmptyLatentImage",
        "inputs": {"width": 512, "height": 512, "batch_size": 1},
    },
    "6": {
        "class_type": "CLIPTextEncode",
        "inputs": {
            "text": f"{prompt_text}, vibrant colors, instagram style, vertical portrait",
            "clip": ["4", 1],
        },
    },
    "7": {
        "class_type": "CLIPTextEncode",
        "inputs": {"text": "bad quality, blurry, watermark, text", "clip": ["4", 1]},
    },
    "8": {
        "class_type": "VAEDecode",
        "inputs": {"samples": ["3", 0], "vae": ["4", 2]},
    },
    "9": {
        "class_type": "SaveImage",
        "inputs": {"filename_prefix": "insta", "images": ["8", 0]},
    },
}

print(f"Submitting prompt to ComfyUI...", file=sys.stderr)
resp = requests.post(f"{COMFYUI_URL}/prompt", json={"prompt": workflow})
resp.raise_for_status()
data = resp.json()

if "prompt_id" not in data:
    print(f"ComfyUI error: {data}", file=sys.stderr)
    sys.exit(1)

prompt_id = data["prompt_id"]
print(f"Prompt ID: {prompt_id}", file=sys.stderr)

# Poll until done
for attempt in range(60):
    time.sleep(2)
    r = requests.get(f"{COMFYUI_URL}/history/{prompt_id}").json()
    if prompt_id in r:
        outputs = r[prompt_id]["outputs"]
        break
    if attempt == 59:
        print("Timeout waiting for ComfyUI", file=sys.stderr)
        sys.exit(1)

image_filename = None
for node_output in outputs.values():
    if "images" in node_output:
        image_filename = node_output["images"][0]["filename"]
        break

if not image_filename:
    print("Error: no image generated", file=sys.stderr)
    sys.exit(1)

dest_dir = os.path.expanduser("~/insta-pipeline/output/images")
os.makedirs(dest_dir, exist_ok=True)
dest = os.path.join(dest_dir, image_filename)
src  = os.path.join(os.path.expanduser("~/ComfyUI/output"), image_filename)
os.replace(src, dest)

print(dest)   # ONLY this goes to stdout
