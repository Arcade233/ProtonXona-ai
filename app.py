import os, tempfile, gradio as gr
from gtts import gTTS
import PIL.Image
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
from huggingface_hub import InferenceClient

HF_TOKEN = os.getenv("HF_TOKEN", "")

def generate(prompt, script):
    if not HF_TOKEN:
        return None, "Add HF_TOKEN in Render > Environment"
    if not prompt:
        return None, "Enter prompt"
    if not script:
        script = prompt

    try:
        client = InferenceClient(token=HF_TOKEN)
        # VOICE
        tmp_audio = tempfile.mktemp(suffix=".mp3")
        gTTS(text=script, lang='en').save(tmp_audio)
        audio = AudioFileClip(tmp_audio)
        
        # 5 STORY SHOTS FOR MOTION
        shots = [
            f"{prompt}, wide establishing shot, cinematic",
            f"{prompt}, medium shot walking forward, action, motion blur",
            f"{prompt}, close up face, emotional, detailed",
            f"{prompt}, side tracking shot moving, dynamic",
            f"{prompt}, final heroic pose, sunset lighting"
        ]
        
        clips = []
        clip_dur = audio.duration / len(shots)
        
        for i, shot in enumerate(shots):
            img = client.text_to_image(shot, model="black-forest-labs/FLUX.1-schnell")
            tmp_img = tempfile.mktemp(suffix=f"_{i}.jpg")
            img = img.resize((720, 1280))
            img.save(tmp_img)
            
            # REAL MOTION: Zoom + slight pan
            clip = ImageClip(tmp_img, duration=clip_dur)
            # Ken burns effect
            clip = clip.resize(lambda t: 1 + 0.15*t)  # zoom in
            if i % 2 == 0:
                clip = clip.set_position(lambda t: ('center', 50 - t*20)) # pan up
            else:
                clip = clip.set_position(lambda t: ( -t*20, 'center')) # pan left
            clips.append(clip)

        video = concatenate_videoclips(clips, method="compose")
        final = video.set_audio(audio)
        out = tempfile.mktemp(suffix=".mp4")
        final.write_videofile(out, fps=24, codec='libx264', audio_codec='aac', logger=None)

        return out, "DONE - 100% FREE Motion Video (5 AI scenes + voice + motion)"

    except Exception as e:
        return None, f"ERROR: {str(e)[:1500]}"

with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# ProtonXona - FREE AI Video (No Balance Needed)")
    p = gr.Textbox(label="What should happen (action)", value="Ghanaian young entrepreneur walking confidently through modern Accra market, cinematic", lines=2)
    s = gr.Textbox(label="Voice script", value="Welcome to ProtonXona. We turn your ideas into powerful videos in seconds.", lines=2)
    b = gr.Button("Generate FREE Video Now", variant="primary")
    v = gr.Video(label="Your Video")
    t = gr.Textbox(label="Status")
    b.click(generate, inputs=[p, s], outputs=[v, t])

demo.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", 10000)))
