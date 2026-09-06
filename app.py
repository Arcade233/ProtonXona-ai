import os, tempfile, requests, gradio as gr, time
from gtts import gTTS
import PIL.Image
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS
from moviepy.editor import VideoFileClip, AudioFileClip

HF_TOKEN = os.getenv("HF_TOKEN", "")

def generate(prompt, script):
    if not HF_TOKEN:
        return None, "Add HF_TOKEN in Render"
    if not prompt:
        return None, "Enter prompt"
    if not script:
        script = prompt

    try:
        headers = {"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"}
        
        # REAL VIDEO MODEL - Supported provider fal-ai
        # Try 1: Wan 1.3B via fal-ai (WORKS)
        urls_to_try = [
            "https://router.huggingface.co/fal-ai/Wan-AI/Wan2.1-T2V-1.3B-Diffusers",
            "https://router.huggingface.co/replicate/Wan-AI/Wan2.1-T2V-14B-Diffusers"
        ]
        
        r = None
        last_error = ""
        for url in urls_to_try:
            try:
                print(f"Trying {url}")
                r = requests.post(url, headers=headers, json={"inputs": prompt, "parameters": {"num_frames": 33}}, timeout=180)
                if r.status_code == 200:
                    break
                else:
                    last_error = f"{r.status_code}: {r.text[:500]}"
                    print(last_error)
            except Exception as e2:
                last_error = str(e2)
                continue

        if r is None or r.status_code != 200:
            return None, f"All video models busy. Last: {last_error}. Try again in 1 min. This happens because free HF is queued."

        raw_video = tempfile.mktemp(suffix=".mp4")
        with open(raw_video, "wb") as f:
            f.write(r.content)

        # Voice
        tmp_audio = tempfile.mktemp(suffix=".mp3")
        gTTS(text=script, lang='en').save(tmp_audio)
        audio = AudioFileClip(tmp_audio)

        # Merge
        video = VideoFileClip(raw_video)
        if video.duration < audio.duration:
            video = video.loop(duration=audio.duration)
        else:
            video = video.subclip(0, audio.duration)
        
        final = video.set_audio(audio)
        out = tempfile.mktemp(suffix=".mp4")
        final.write_videofile(out, fps=8, codec='libx264', audio_codec='aac', logger=None)
        
        return out, f"REAL VIDEO SUCCESS - {prompt}"

    except Exception as e:
        return None, f"ERROR: {str(e)[:1500]}"

with gr.Blocks() as demo:
    gr.Markdown("# ProtonXona REAL VIDEO - Wan Model")
    p = gr.Textbox(label="What should happen? (real motion)", value="African woman walking in busy market, camera follows, cinematic")
    s = gr.Textbox(label="Voice script", value="Welcome to ProtonXona")
    b = gr.Button("Generate REAL Moving Video", variant="primary")
    v = gr.Video(label="Real Motion Video")
    t = gr.Textbox(label="Status - if busy wait 1 min and retry")
    b.click(generate, inputs=[p, s], outputs=[v, t])

demo.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", 10000)))
