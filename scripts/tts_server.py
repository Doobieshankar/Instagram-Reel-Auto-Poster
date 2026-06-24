from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from TTS.api import TTS
import uuid, os

app = FastAPI()

# Lightweight English model (can switch later for Tamil)
tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC", progress_bar=False)

output_dir = os.path.expanduser("~/insta-pipeline/output/tts")
os.makedirs(output_dir, exist_ok=True)

@app.get("/tts")
def generate(text: str, lang: str = "en"):
    file_id = str(uuid.uuid4())[:8]
    out_path = os.path.join(output_dir, f"{file_id}.wav")
    try:
        tts.tts_to_file(text=text, file_path=out_path)
        return FileResponse(out_path, media_type="audio/wav", filename=f"{file_id}.wav")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
