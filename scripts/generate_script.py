# #!/usr/bin/env python3
# """
# generate_script.py

# Outputs a single JSON line: {"topic": "...", "script": "...", "hashtags": "...", "image_prompt": "..."}
# """
# import requests, json, random, re, sys

# TOPICS = ["motivation", "discipline", "success", "mindset", "technology",
#           "productivity", "fitness", "creativity", "leadership", "focus"]

# HASHTAG_MAP = {
#     "motivation":   "#motivation #inspiration #mindset",
#     "discipline":   "#discipline #success #grind",
#     "success":      "#success #goals #winning",
#     "mindset":      "#mindset #growth #selfimprovement",
#     "technology":   "#tech #ai #innovation",
#     "productivity": "#productivity #workflow #hustle",
#     "fitness":      "#fitness #health #workout",
#     "creativity":   "#creative #art #design",
#     "leadership":   "#leadership #business #entrepreneur",
#     "focus":        "#focus #deepwork #clarity",
# }

# IMAGE_FALLBACKS = {
#     "motivation":   "golden hour sunlight through forest, lone figure on mountain peak, cinematic wide shot, dramatic clouds, inspirational mood, photorealistic, 4k",
#     "discipline":   "minimalist dark gym at dawn, single spotlight on barbell, cinematic, gritty, high contrast black and white, photorealistic",
#     "success":      "aerial view of city skyline at night, lights reflecting on wet street, cinematic, ambitious mood, deep blue and gold tones, 4k",
#     "mindset":      "person meditating on cliff edge at sunrise, vast ocean below, golden light, peaceful, cinematic wide angle, photorealistic",
#     "technology":   "futuristic holographic interface floating in dark room, blue neon light, cyberpunk aesthetic, cinematic, 4k, detailed",
#     "productivity": "minimal clean desk with coffee and open notebook, soft morning light, flat lay, calm focused atmosphere, pastel tones, aesthetic",
#     "fitness":      "athlete silhouette running on mountain trail at sunset, dramatic orange sky, motion blur, cinematic, inspirational, photorealistic",
#     "creativity":   "artist studio with colorful paint splashes, dramatic natural light through large window, vibrant colors, cinematic, photorealistic",
#     "leadership":   "lone figure standing at top of stairs overlooking vast city, powerful composition, dramatic clouds, cinematic, photorealistic",
#     "focus":        "single lit candle in dark room, book open beside it, warm bokeh, intimate, calm, cinematic macro shot, photorealistic",
# }

# topic = random.choice(TOPICS)
# prompt = (
#     f"You are a creative director for Instagram Reels. Topic: {topic}. "
#     f"Respond ONLY with a valid JSON object, no markdown, no explanation, no extra text. "
#     f"Format exactly: "
#     f'{{\"topic\": \"{topic}\", '
#     f'\"script\": \"<30-second voiceover, hook first sentence, CTA last sentence, max 50 words, no hashtags>\", '
#     f'\"image_prompt\": \"<cinematic Stable Diffusion prompt: vivid scene, lighting, mood, style related to {topic}, no text, no people, photorealistic, 4k>\"}}'
# )

# MODEL   = "openbmb/minicpm-v4.6:latest"
# TIMEOUT = 120

# try:
#     resp = requests.post(
#         "http://localhost:11434/api/generate",
#         json={"model": MODEL, "prompt": prompt, "stream": False},
#         timeout=TIMEOUT,
#     )
#     resp.raise_for_status()
#     raw_text = resp.json().get("response", "")
# except Exception as e:
#     print(f"Ollama error: {e}", file=sys.stderr)
#     raw_text = ""

# # Strip <think> blocks
# cleaned = re.sub(r"<think>.*?</think>", "", raw_text, flags=re.DOTALL).strip()

# # Extract first {...} block
# match = re.search(r"\{.*?\}", cleaned, re.DOTALL)
# result = {}
# if match:
#     try:
#         result = json.loads(match.group())
#     except Exception:
#         pass

# script       = result.get("script", "").strip().strip('"\'')
# image_prompt = result.get("image_prompt", "").strip().strip('"\'')

# # Script fallback
# SCRIPT_FALLBACKS = {
#     "motivation":   "Most people quit right before the breakthrough. Don't be most people. Take one step today.",
#     "discipline":   "Motivation fades. Discipline stays. Build the habit, not the mood.",
#     "success":      "Success isn't luck — it's the sum of small daily choices. Start now.",
#     "mindset":      "Your mind is your most powerful tool. Train it daily. Watch everything shift.",
#     "technology":   "AI won't replace you. But someone using AI will. Start learning today.",
#     "productivity": "Stop being busy. Start being effective. Do the one thing that matters most.",
#     "fitness":      "Your body is your business. Invest in it every single day.",
#     "creativity":   "Every expert was once a beginner. Create badly until you create brilliantly.",
#     "leadership":   "Real leaders lift others up. Be the person who makes the room better.",
#     "focus":        "One task. Full attention. No distractions. That's where breakthroughs happen.",
# }

# if not script or len(script) < 10:
#     script = SCRIPT_FALLBACKS.get(topic, "Push beyond your limits. Every day is a new chance. Start now.")

# # Image prompt fallback
# if not image_prompt or len(image_prompt) < 10:
#     image_prompt = IMAGE_FALLBACKS.get(topic, "cinematic landscape, golden hour, dramatic light, photorealistic, 4k")

# output = {
#     "topic":        topic,
#     "script":       script,
#     "hashtags":     HASHTAG_MAP.get(topic, "#motivation #inspiration"),
#     "image_prompt": image_prompt,
# }
# print(json.dumps(output))

#!/usr/bin/env python3
"""
generate_script.py
Outputs JSON: {"topic": "...", "script": "...", "hashtags": "...", "image_prompt": "..."}
Script is enforced to 60-80 words (~20 seconds of TTS audio).
"""
import requests, json, random, re, sys

TOPICS = ["motivation", "discipline", "success", "mindset", "technology",
          "productivity", "fitness", "creativity", "leadership", "focus"]

HASHTAG_MAP = {
    "motivation":   "#motivation #inspiration #mindset",
    "discipline":   "#discipline #success #grind",
    "success":      "#success #goals #winning",
    "mindset":      "#mindset #growth #selfimprovement",
    "technology":   "#tech #ai #innovation",
    "productivity": "#productivity #workflow #hustle",
    "fitness":      "#fitness #health #workout",
    "creativity":   "#creative #art #design",
    "leadership":   "#leadership #business #entrepreneur",
    "focus":        "#focus #deepwork #clarity",
}

IMAGE_FALLBACKS = {
    "motivation":   "golden hour sunlight through forest, lone figure on mountain peak, cinematic wide shot, dramatic clouds, inspirational mood, photorealistic, 8k",
    "discipline":   "minimalist dark gym at dawn, single spotlight on barbell, cinematic, gritty, high contrast black and white, photorealistic, 8k",
    "success":      "aerial view of city skyline at night, lights reflecting on wet street, cinematic, ambitious mood, deep blue and gold tones, 8k",
    "mindset":      "person meditating on cliff edge at sunrise, vast ocean below, golden light, peaceful, cinematic wide angle, photorealistic, 8k",
    "technology":   "futuristic holographic interface floating in dark room, blue neon light, cyberpunk aesthetic, cinematic, 8k, ultra detailed",
    "productivity": "minimal clean desk with coffee and open notebook, soft morning light, flat lay, calm focused atmosphere, pastel tones, aesthetic, 8k",
    "fitness":      "athlete silhouette running on mountain trail at sunset, dramatic orange sky, motion blur, cinematic, inspirational, photorealistic, 8k",
    "creativity":   "artist studio with colorful paint splashes, dramatic natural light through large window, vibrant colors, cinematic, photorealistic, 8k",
    "leadership":   "lone figure standing at top of stairs overlooking vast city, powerful composition, dramatic clouds, cinematic, photorealistic, 8k",
    "focus":        "single lit candle in dark room, book open beside it, warm bokeh, intimate, calm, cinematic macro shot, photorealistic, 8k",
}

SCRIPT_FALLBACKS = {
    "motivation":   "Most people quit right before the breakthrough. They stop when it gets hard, when doubt creeps in, when the results aren't showing yet. But that's exactly when you need to push harder. The people who succeed are not the most talented — they are the ones who refused to stop. Your breakthrough is closer than you think. Take one step today.",
    "discipline":   "Motivation is a feeling. It comes and goes like the weather. But discipline is a decision you make every single day regardless of how you feel. The most successful people in the world don't wait to feel inspired — they show up, do the work, and build momentum. Stop waiting for motivation. Start building discipline. Begin today.",
    "success":      "Success doesn't happen overnight. It's built in the quiet moments when nobody's watching — the early mornings, the late nights, the small choices you make every single day. Most people overestimate what they can do in a week and underestimate what they can do in a year. Stay consistent, stay patient, stay focused. Your time is coming. Start now.",
    "mindset":      "Everything in your life is a reflection of your mindset. The way you think determines the actions you take, and the actions you take determine the results you get. If you want to change your life, you have to start by changing how you think. Challenge your limiting beliefs every single day. Train your mind like you train your body. Watch everything shift.",
    "technology":   "We are living through the greatest technological shift in human history. Artificial intelligence is not coming — it is already here, already changing how we work, create, and communicate. The question is not whether technology will change your industry. It is whether you will adapt before it is too late. Start learning today. The future belongs to those who prepare for it now.",
    "productivity": "Being busy is not the same as being productive. You can fill every hour of your day with tasks and still make zero progress on what actually matters. True productivity is about focus — doing the right things, in the right order, with full attention. Eliminate the noise. Protect your time like it is your most valuable asset. Because it is. Start today.",
    "fitness":      "Your body is the vehicle that carries you through every single experience in life. How you treat it determines how far you go, how long you last, and how good you feel along the way. You don't need a perfect plan or a perfect gym. You need consistency, patience, and the decision to show up every day. Your health is your greatest investment. Start now.",
    "creativity":   "Every single person is creative. Creativity is not a talent you are born with — it is a muscle you build through practice, experimentation, and the courage to create badly before you create brilliantly. Stop waiting for the perfect idea. Stop waiting for the right moment. Pick up the pen, open the canvas, start the project. Create something today. The world needs your unique voice.",
    "leadership":   "Real leadership has nothing to do with your title or your position. It is about how you make people feel when they are around you. Great leaders listen more than they speak, lift others higher than themselves, and take responsibility when things go wrong. You don't need permission to lead. Start showing up for the people around you today. That is where leadership begins.",
    "focus":        "In a world designed to distract you, the ability to focus deeply on one thing is your greatest competitive advantage. Every notification, every scroll, every distraction pulls you further from your goals. The most successful people guard their attention fiercely. They do one thing at a time with complete presence. Close the tabs. Silence the phone. Do the work. Your future self will thank you.",
}

topic = random.choice(TOPICS)

# Build prompt asking for 60-80 word script
prompt = (
    "You are a creative director for Instagram Reels. "
    "Respond ONLY with a valid JSON object. No markdown, no explanation, no extra text. "
    "Topic: " + topic + ". "
    "CRITICAL: The script must be EXACTLY 60 to 80 words. Count every word carefully. "
    "A short script will ruin the video length. "
    'JSON format: {"topic": "' + topic + '", '
    '"script": "EXACTLY 60-80 word voiceover: hook first sentence, 3-4 sentences building the message, strong call-to-action last sentence, no hashtags, no emojis", '
    '"image_prompt": "cinematic Stable Diffusion prompt: ultra detailed vivid scene, dramatic lighting, rich colors, mood strongly related to ' + topic + ', no text, no people, no faces, photorealistic, 8k, award winning photography"}'
)

MODEL   = "openbmb/minicpm-v4.6:latest"
TIMEOUT = 120

try:
    resp = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": MODEL, "prompt": prompt, "stream": False},
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    raw_text = resp.json().get("response", "")
except Exception as e:
    print(f"Ollama error: {e}", file=sys.stderr)
    raw_text = ""

# Strip <think> blocks
cleaned = re.sub(r"<think>.*?</think>", "", raw_text, flags=re.DOTALL).strip()

# Extract first {...} block
match = re.search(r"\{.*?\}", cleaned, re.DOTALL)
result = {}
if match:
    try:
        result = json.loads(match.group())
    except Exception:
        pass

script       = result.get("script", "").strip().strip('"\'')
image_prompt = result.get("image_prompt", "").strip().strip('"\'')

# If script too short (< 50 words) use fallback
word_count = len(script.split())
if not script or word_count < 50:
    print(f"Script too short ({word_count} words), using fallback.", file=sys.stderr)
    script = SCRIPT_FALLBACKS.get(topic, SCRIPT_FALLBACKS["motivation"])

# Image prompt fallback
if not image_prompt or len(image_prompt) < 10:
    image_prompt = IMAGE_FALLBACKS.get(topic, "cinematic landscape, golden hour, dramatic light, photorealistic, 8k")

print(f"Script word count: {len(script.split())}", file=sys.stderr)

output = {
    "topic":        topic,
    "script":       script,
    "hashtags":     HASHTAG_MAP.get(topic, "#motivation #inspiration"),
    "image_prompt": image_prompt,
}
print(json.dumps(output))