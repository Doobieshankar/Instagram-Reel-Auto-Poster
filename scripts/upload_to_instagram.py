#!/usr/bin/env python3
"""
upload_to_instagram.py <video_url> <caption> [<hashtags>]

Uses Graph API v20.0.
Polls container status before publishing (required for video).
"""
import requests, sys, os, time

video_url  = sys.argv[1]
caption    = sys.argv[2]
hashtags   = sys.argv[3] if len(sys.argv) > 3 else ""
full_caption = f"{caption}\n\n{hashtags}".strip()

ACCESS_TOKEN = os.environ["IG_ACCESS_TOKEN"]
IG_USER_ID   = os.environ["IG_USER_ID"]
API_BASE     = f"https://graph.facebook.com/v20.0/{IG_USER_ID}"

# 1. Create media container
print("Creating media container...", flush=True)
resp = requests.post(
    f"{API_BASE}/media",
    params={
        "media_type":   "REELS",
        "video_url":    video_url,
        "caption":      full_caption,
        "share_to_feed": "true",
        "access_token": ACCESS_TOKEN,
    },
)
if resp.status_code != 200:
    print(f"Container creation failed ({resp.status_code}): {resp.text}", file=sys.stderr)
    sys.exit(1)

container_id = resp.json()["id"]
print(f"Container ID: {container_id}")

# 2. Poll until FINISHED (video processing takes 10-60s)
print("Waiting for video processing...", flush=True)
for attempt in range(30):
    time.sleep(5)
    status_resp = requests.get(
        f"https://graph.facebook.com/v20.0/{container_id}",
        params={"fields": "status_code,status", "access_token": ACCESS_TOKEN},
    )
    status_data = status_resp.json()
    status_code = status_data.get("status_code", "")
    print(f"  [{attempt+1}] status: {status_code}", flush=True)
    if status_code == "FINISHED":
        break
    if status_code == "ERROR":
        print(f"Processing error: {status_data}", file=sys.stderr)
        sys.exit(1)
else:
    print("Timeout: container never reached FINISHED state", file=sys.stderr)
    sys.exit(1)

# 3. Publish
print("Publishing...", flush=True)
pub_resp = requests.post(
    f"{API_BASE}/media_publish",
    params={"creation_id": container_id, "access_token": ACCESS_TOKEN},
)
result = pub_resp.json()
if "id" in result:
    print(f"Published! Post ID: {result['id']}")
else:
    print(f"Publish response: {result}", file=sys.stderr)
    sys.exit(1)
