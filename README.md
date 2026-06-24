# Instagram Reel Auto-Poster Pipeline

Fully local AI pipeline that generates, renders, and posts Instagram Reels automatically.
Runs on Ubuntu 24.04. No cloud AI APIs needed — everything runs on your machine.

---

## How It Works

```
Ollama (LLM) → script + image prompt
      ↓
ComfyUI (Stable Diffusion) → image
      ↓
Coqui TTS → voiceover audio
      ↓
MoviePy → rendered 1080x1920 video with captions
      ↓
Cloudflare Tunnel → public URL
      ↓
Instagram Graph API → posted Reel
```

---

## Directory Structure

```
~/insta-pipeline/
├── .env                        # Instagram credentials (never commit this)
├── tunnel_url.txt              # Cloudflare public URL (auto-updated by start.sh)
├── start.sh                    # Run this after every boot
├── venv/                       # Main Python environment
├── tts_venv/                   # Separate TTS environment (numpy pinned to 1.22.0)
├── scripts/
│   ├── run_pipeline.sh         # Master script — runs everything in order
│   ├── generate_script.py      # LLM generates script + image prompt + hashtags
│   ├── moderate_script.py      # Safety check via LLM
│   ├── gen_image.py            # Sends image prompt to ComfyUI
│   ├── tts_client.py           # Calls TTS server, saves audio
│   ├── render_video.py         # Combines image + audio + captions → mp4
│   ├── upload_to_instagram.py  # Posts to Instagram via Graph API
│   └── tts_server.py           # FastAPI TTS server (run by systemd)
└── output/
    ├── images/                 # Generated images from ComfyUI
    ├── tts/                    # Generated audio files
    └── *.mp4                   # Final rendered videos
```

---

## Prerequisites

### System packages
```bash
sudo apt update
sudo apt install -y ffmpeg imagemagick jq python3-pip python3-venv git curl
```

### Fix ImageMagick security policy (required for video captions)
```bash
sudo sed -i 's/rights="none" pattern="@\*"/rights="read|write" pattern="@*"/' /etc/ImageMagick-6/policy.xml
```

### Cloudflared
```bash
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb
```

### Ollama
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull openbmb/minicpm-v4.6
```

### ComfyUI
```bash
cd ~
git clone https://github.com/comfyanonymous/ComfyUI
cd ComfyUI
python3 -m venv venv
source venv/bin/activate
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

Download model:
```bash
mkdir -p ~/ComfyUI/models/checkpoints
cd ~/ComfyUI/models/checkpoints
wget https://huggingface.co/Lykon/dreamshaper-8/resolve/main/dreamshaper_8LCM.safetensors
```

---

## Python Environments

### Main venv (used by run_pipeline.sh)
```bash
cd ~/insta-pipeline
python3 -m venv venv
source venv/bin/activate
pip install moviepy==1.0.3 Pillow numpy requests fastapi==0.111.1 \
            imageio imageio-ffmpeg openai-whisper torch torchaudio TTS
```

### TTS venv (used only by tts_server.py via systemd)
```bash
cd ~/insta-pipeline
python3 -m venv tts_venv
source tts_venv/bin/activate
pip install numpy==1.22.0  # must stay at 1.22.0 — TTS breaks with higher
pip install torch torchaudio TTS fastapi uvicorn
```

> **Warning:** Never upgrade numpy in `tts_venv`. Coqui TTS 0.22.0 is incompatible with numpy 1.24+.

---

## Systemd Services

Three services run in the background and auto-start on boot.

### 1. ComfyUI (image generation)
```bash
sudo tee /etc/systemd/system/comfyui.service << 'EOF'
[Unit]
Description=ComfyUI Stable Diffusion
After=network.target

[Service]
User=gotoz
WorkingDirectory=/home/gotoz/ComfyUI
ExecStart=/home/gotoz/insta-pipeline/venv/bin/python main.py --cpu --listen 0.0.0.0 --port 8188
Restart=always
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl enable --now comfyui
```

> Note: ComfyUI uses the main `insta-pipeline/venv`, not a separate ComfyUI venv.

### 2. TTS Server (voiceover)
```bash
sudo tee /etc/systemd/system/tts.service << 'EOF'
[Unit]
Description=TTS Server
After=network.target

[Service]
User=gotoz
WorkingDirectory=/home/gotoz/insta-pipeline/scripts
ExecStart=/home/gotoz/insta-pipeline/tts_venv/bin/uvicorn tts_server:app --host 0.0.0.0 --port 5002
Restart=always

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl enable --now tts
```

### 3. Video Server (serves mp4 to Instagram)
```bash
sudo tee /etc/systemd/system/video-server.service << 'EOF'
[Unit]
Description=Simple HTTP Server for Output Folder
After=network.target

[Service]
User=gotoz
WorkingDirectory=/home/gotoz/insta-pipeline/output
ExecStart=/usr/bin/python3 -m http.server 8080
Restart=always

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl enable --now video-server
```

### Check all services
```bash
systemctl is-active comfyui tts video-server
```

---

## Instagram Setup

### Requirements
- Facebook Developer account at https://developers.facebook.com
- App with `instagram_basic`, `instagram_content_publish`, `pages_read_engagement` permissions
- Instagram Business or Creator account connected to a Facebook Page

### Get credentials
1. Go to https://developers.facebook.com → your app → Tools → Graph API Explorer
2. Generate a User Access Token with the permissions above
3. Exchange for a long-lived token (valid 60 days):

```bash
curl "https://graph.facebook.com/v20.0/oauth/access_token\
?grant_type=fb_exchange_token\
&client_id=YOUR_APP_ID\
&client_secret=YOUR_APP_SECRET\
&fb_exchange_token=YOUR_SHORT_TOKEN"
```

4. Get your Instagram User ID:
```bash
curl "https://graph.facebook.com/v20.0/me/accounts?access_token=YOUR_LONG_TOKEN"
# Use the id from the response that corresponds to your Instagram page
```

### Set credentials
```bash
cat > ~/insta-pipeline/.env << 'EOF'
export IG_ACCESS_TOKEN="your_long_lived_token_here"
export IG_USER_ID="your_instagram_user_id_here"
EOF
```

### Token refresh (every ~50 days)
```bash
curl "https://graph.facebook.com/v20.0/oauth/access_token\
?grant_type=fb_exchange_token\
&client_id=YOUR_APP_ID\
&client_secret=YOUR_APP_SECRET\
&fb_exchange_token=$(grep IG_ACCESS_TOKEN ~/insta-pipeline/.env | cut -d= -f2 | tr -d '"')"
```

---

## First Boot Setup

Create `start.sh` in `~/insta-pipeline/`:

```bash
cat > ~/insta-pipeline/start.sh << 'EOF'
#!/bin/bash
# Run this once after every boot before running the pipeline

# 1. Ensure services are running
sudo systemctl restart comfyui tts video-server

# 2. Start Cloudflare tunnel and capture new URL
pkill cloudflared 2>/dev/null; sleep 2
cloudflared tunnel --url http://localhost:8080 2>&1 | tee /tmp/cf.log &
sleep 8
grep -o "https://[a-z0-9-]*\.trycloudflare\.com" /tmp/cf.log | head -1 > ~/insta-pipeline/tunnel_url.txt
echo "Tunnel URL: $(cat ~/insta-pipeline/tunnel_url.txt)"
echo "Ready. Run: bash ~/insta-pipeline/scripts/run_pipeline.sh"
EOF
chmod +x ~/insta-pipeline/start.sh
```

---

## Every Boot Procedure

```bash
# Step 1 — start tunnel and verify services
bash ~/insta-pipeline/start.sh

# Step 2 — run the pipeline
bash ~/insta-pipeline/scripts/run_pipeline.sh
```

---

## Running the Pipeline

```bash
bash ~/insta-pipeline/scripts/run_pipeline.sh
```

Expected output:
```
[HH:MM:SS] Checking services...
[HH:MM:SS] All services up.
[HH:MM:SS] Generating script...
[HH:MM:SS] Topic: motivation
[HH:MM:SS] Script: Most people quit right before the breakthrough...
[HH:MM:SS] Image prompt: golden hour sunlight through forest, cinematic...
[HH:MM:SS] Moderating...
[HH:MM:SS] Generating image...
[HH:MM:SS] Image: /home/gotoz/insta-pipeline/output/images/insta_00001_.png
[HH:MM:SS] Generating TTS audio...
[HH:MM:SS] Audio: /home/gotoz/insta-pipeline/output/tts/tts_xxxxxxxx.wav
[HH:MM:SS] Rendering video...
[HH:MM:SS] Video: /home/gotoz/insta-pipeline/output/1234567890.mp4
[HH:MM:SS] Public URL: https://xxxx.trycloudflare.com/1234567890.mp4
[HH:MM:SS] Uploading to Instagram...
[HH:MM:SS] Pipeline complete in 210s 🎉
```

---

## Schedule Automatic Posts (Optional)

Post daily at 9am:
```bash
crontab -e
# Add this line:
0 9 * * * bash /home/gotoz/insta-pipeline/scripts/run_pipeline.sh >> /home/gotoz/insta-pipeline/pipeline.log 2>&1
```

---

## Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: moviepy.editor` | moviepy v2 installed | `pip install moviepy==1.0.3` |
| `No module named pkg_resources` | Old pip/setuptools | `pip install --upgrade pip setuptools` |
| `IG_ACCESS_TOKEN KeyError` | .env not exporting vars | Add `export` prefix to vars in `.env`, use `set -a` before source |
| `Error code 2207077` | Instagram can't fetch video | Check tunnel is alive: `curl -I $(cat tunnel_url.txt)/video.mp4` |
| `Session has expired` | Instagram token expired | Refresh token (see Instagram Setup above) |
| `TextClip failed` — ImageMagick policy | Security policy blocks text files | `sudo sed -i 's/rights="none" pattern="@\*"/rights="read\|write" pattern="@*"/' /etc/ImageMagick-6/policy.xml` |
| `Could not resolve host: *.trycloudflare.com` | Tunnel died | Run `bash ~/insta-pipeline/start.sh` again |
| ComfyUI slow | CPU mode, no GPU | Normal — takes ~60-90s per image on i7-8550U |

---

## Hardware Used

- **CPU:** Intel Core i7-8550U (no dedicated GPU — ComfyUI runs in CPU mode)
- **RAM:** 16GB
- **OS:** Ubuntu 24.04.4 LTS
- **Storage:** 467GB SSD

---

## Services & Ports

| Service | Port | Venv |
|---|---|---|
| Ollama | 11434 | system |
| ComfyUI | 8188 | `~/insta-pipeline/venv` |
| TTS Server | 5002 | `~/insta-pipeline/tts_venv` |
| Video File Server | 8080 | system python3 |
| Cloudflare Tunnel | — | system binary |
