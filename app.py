import os, tempfile, requests, gradio as gr
from gtts import gTTS
import PIL.Image
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS
from moviepy.editor import VideoFileClip, AudioFileClip

HF_TOKEN = os.getenv("HF_TOKEN", "")

def generate(prompt, script):
    if not HF_TOKEN:
        return None, "Add HF_TOKEN in Render > Environment > Add Variable"
    if not prompt:
        return None, "Enter prompt"
    if not script:
        script = prompt

    try:
        # 1. Real video via new HF Router
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        url = "https://router.huggingface.co/hf-inference/models/damo-vilab/modelscope-text-to-video-synthesis"
        
        r = requests.post(url, headers=headers, json={"inputs": prompt}, timeout=180)
        
        if r.status_code != 200:
            return None, f"HF Error {r.status_code}: {r.text[:800]}"

        raw_video = tempfile.mktemp(suffix=".mp4")
        with open(raw_video, "wb") as f:
            f.write(r.content)

        # 2. Voice
        tmp_audio = tempfile.mktemp(suffix=".mp3")
        gTTS(text=script, lang='en').save(tmp_audio)
        audio = AudioFileClip(tmp_audio)

        # 3. Merge
        video = VideoFileClip(raw_video)
        if video.duration < audio.duration:
            video = video.loop(duration=audio.duration)
        else:
            video = video.subclip(0, audio.duration)
        
        final = video.set_audio(audio)
        out = tempfile.mktemp(suffix=".mp4")
        final.write_videofile(out, fps=8, codec='libx264', audio_codec='aac', logger=None)
        
        return out, "REAL VIDEO SUCCESS"

    except Exception as e:
        return None, f"ERROR: {str(e)[:1200]}"

with gr.Blocks() as demo:
    gr.Markdown("# ProtonXona REAL VIDEO")
    p = gr.Textbox(label="Action prompt", value="Ghanaian woman walking in market, cinematic")
    s = gr.Textbox(label="Voice script", value="Welcome to ProtonXona")
    b = gr.Button("Generate REAL Video", variant="primary")
    v = gr.Video()
    t = gr.Textbox(label="Status")
    b.click(generate, inputs=[p, s], outputs=[v, t])

demo.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", 10000)))
