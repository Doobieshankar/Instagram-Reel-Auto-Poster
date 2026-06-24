(If you want a faster caption model, later you can replace "tiny" with "base" or "small" in render_video.py – but tiny is fine for now.)

# 1. Check services auto-started
systemctl is-active comfyui tts video-server

# 2. Start tunnel (only manual step)
bash ~/insta-pipeline/start.sh

# 3. Run pipeline
bash ~/insta-pipeline/scripts/run_pipeline.sh