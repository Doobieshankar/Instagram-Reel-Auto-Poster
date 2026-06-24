#!/bin/bash
# run_pipeline.sh — Instagram Reel auto-poster
set -euo pipefail
set -a
source ~/insta-pipeline/.env
set +a
source ~/insta-pipeline/venv/bin/activate
cd ~/insta-pipeline/scripts

START_TIME=$(date +%s)
log() { echo "[$(date '+%H:%M:%S')] $*"; }

# ── Health checks ─────────────────────────────────────────────────────────────
log "Checking services..."
curl -sf http://localhost:11434/api/tags     >/dev/null || { log "ERROR: Ollama not running";    exit 1; }
curl -sf http://localhost:8188/system_stats  >/dev/null || { log "ERROR: ComfyUI not running";   exit 1; }
curl -sf "http://localhost:5002/tts?text=test" >/dev/null || { log "ERROR: TTS server not running"; exit 1; }
log "All services up."

# ── 1. Generate script + image prompt ────────────────────────────────────────
log "Generating script..."
JSON_OUT=$(python3 generate_script.py)
SCRIPT=$(echo "$JSON_OUT"        | jq -r '.script')
TOPIC=$(echo "$JSON_OUT"         | jq -r '.topic')
HASHTAGS=$(echo "$JSON_OUT"      | jq -r '.hashtags')
IMAGE_PROMPT=$(echo "$JSON_OUT"  | jq -r '.image_prompt')
log "Topic:        $TOPIC"
log "Script:       $SCRIPT"
log "Image prompt: $IMAGE_PROMPT"

# ── 2. Moderate ───────────────────────────────────────────────────────────────
log "Moderating..."
MOD=$(python3 moderate_script.py "$SCRIPT")
if [ "$MOD" = "UNSAFE" ]; then
    log "WARN: Unsafe script, using fallback."
    SCRIPT="Believe in yourself. Every day is a new opportunity. Keep pushing forward."
    HASHTAGS="#motivation #inspiration #mindset"
    IMAGE_PROMPT="golden hour sunlight through forest, lone figure on mountain peak, cinematic, photorealistic, 4k"
fi

# ── 3. Generate image (uses dedicated image prompt, not the script) ───────────
log "Generating image..."
IMAGE_PATH=$(python3 gen_image.py "$IMAGE_PROMPT")
log "Image: $IMAGE_PATH"

# ── 4. Generate voice (retry once) ───────────────────────────────────────────
log "Generating TTS audio..."
AUDIO_PATH=$(python3 tts_client.py "$SCRIPT") || {
    log "TTS failed, retrying in 5s..."
    sleep 5
    AUDIO_PATH=$(python3 tts_client.py "$SCRIPT")
}
log "Audio: $AUDIO_PATH"

# ── 5. Render video ───────────────────────────────────────────────────────────
log "Rendering video..."
OUTPUT_DIR=~/insta-pipeline/output
mkdir -p "$OUTPUT_DIR"
TIMESTAMP=$(date +%s)
VIDEO_PATH="$OUTPUT_DIR/$TIMESTAMP.mp4"
python3 render_video.py "$IMAGE_PATH" "$AUDIO_PATH" "$VIDEO_PATH" "$SCRIPT"
log "Video: $VIDEO_PATH"

# ── 6. Get public URL ─────────────────────────────────────────────────────────
TUNNEL_BASE=$(cat ~/insta-pipeline/tunnel_url.txt)
PUBLIC_URL="$TUNNEL_BASE/$TIMESTAMP.mp4"
log "Public URL: $PUBLIC_URL"

# ── 7. Upload to Instagram ────────────────────────────────────────────────────
log "Uploading to Instagram..."
python3 upload_to_instagram.py "$PUBLIC_URL" "$SCRIPT" "$HASHTAGS"

# ── Done ──────────────────────────────────────────────────────────────────────
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
log "Pipeline complete in ${ELAPSED}s 🎉"
