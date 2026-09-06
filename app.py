import os, tempfile, gradio as gr
from gtts import gTTS
import PIL.Image
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS
from moviepy.editor import VideoFileClip, AudioFileClip
import fal_client

FAL_KEY = os.getenv("FAL_KEY", "")
if FAL_KEY:
    os.environ["FAL_KEY"] = FAL_KEY

def generate(prompt, script):
    if not FAL_KEY:
        return None, "Add FAL_KEY in Render Environment Variables - get free at fal.ai/dashboard/keys"
    if not prompt:
        return None, "Enter prompt"
    if not script:
        script = prompt

    try:
        # 1. REAL AI VIDEO from fal.ai - Wan 2.1 - TRUE MOTION
        result = fal_client.subscribe(
            "fal-ai/wan/v2.1/1.3b/text-to-video",
            arguments={
                "prompt": prompt,
                "negative_prompt": "blurry, low quality, distorted",
                "num_frames": 81,
                "frames_per_second": 16,
                "aspect_ratio": "9:16"
            }
        )
        
        video_url = result["video"]["url"]
        
        # Download real video
        import requests
        raw_video = tempfile.mktemp(suffix=".mp4")
        with open(raw_video, "wb") as f:
            f.write(requests.get(video_url).content)

        # 2. Voice
        tmp_audio = tempfile.mktemp(suffix=".mp3")
        gTTS(text=script, lang='en').save(tmp_audio)
        audio = AudioFileClip(tmp_audio)

        # 3. Merge
        video_clip = VideoFileClip(raw_video)
        if video_clip.duration < audio.duration:
            video_clip = video_clip.loop(duration=audio.duration)
        else:
            video_clip = video_clip.subclip(0, audio.duration)

        final = video_clip.set_audio(audio)
        out = tempfile.mktemp(suffix=".mp4")
        final.write_videofile(out, fps=16, codec='libx264', audio_codec='aac', logger=None)

        return out, f"REAL FAL VIDEO SUCCESS - True motion video!"

    except Exception as e:
        return None, f"FAL ERROR: {str(e)[:1500]}"

with gr.Blocks() as demo:
    gr.Markdown("# ProtonXona - REAL AI VIDEO with Fal.ai (No Queue)")
    p = gr.Textbox(label="Video prompt - what moves", value="Ghanaian woman walking through vibrant Accra market, cinematic tracking shot, 4k, natural motion", lines=3)
    s = gr.Textbox(label="Voice script", value="Welcome to ProtonXona, where your ideas become real videos", lines=2)
    b = gr.Button("Generate REAL Moving Video (Fal.ai)", variant="primary")
    v = gr.Video(label="True Motion Video")
    t = gr.Textbox(label="Status")
    b.click(generate, inputs=[p, s], outputs=[v, t])

demo.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", 10000)))
