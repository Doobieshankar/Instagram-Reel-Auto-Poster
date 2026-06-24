#!/bin/bash
# Run this once after every boot before running the pipeline

# 1. Restart services if needed
sudo systemctl restart comfyui tts video-server

# 2. Kill old tunnel, start fresh
pkill cloudflared 2>/dev/null; sleep 2
cloudflared tunnel --url http://localhost:8080 2>&1 | tee /tmp/cf.log &
sleep 8
grep -o "https://[a-z0-9-]*\.trycloudflare\.com" /tmp/cf.log | head -1 > ~/insta-pipeline/tunnel_url.txt
echo "Tunnel URL: $(cat ~/insta-pipeline/tunnel_url.txt)"
echo "Ready. Run: bash ~/insta-pipeline/scripts/run_pipeline.sh"
