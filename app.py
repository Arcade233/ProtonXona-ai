import gradio as gr
import os
import tempfile
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont
import PIL.Image
# FIX for Pillow 10+ error
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS
from moviepy.editor import ImageClip, AudioFileClip
import textwrap

def create_video(script):
    try:
        if not script or len(script) < 5:
            return None, "Type longer script"
        
        # 1. Make audio from script
        tmp_audio = tempfile.mktemp(suffix=".mp3")
        tts = gTTS(text=script, lang='en', slow=False)
        tts.save(tmp_audio)
        
        audio_clip = AudioFileClip(tmp_audio)
        duration = audio_clip.duration
        
        # 2. Make image with text (720x1280)
        W, H = 720, 1280
        img = Image.new('RGB', (W, H), color=(15, 15, 25))
        draw = ImageDraw.Draw(img)
        
        # Wrap text to fit screen
        wrapped = textwrap.fill(script, width=30)
        try:
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", 40)
        except:
            font = ImageFont.load_default()
            
        # Center text
        draw.multiline_text((40, 450), wrapped, fill=(255,255,255), font=font, spacing=12, align="left")
        draw.text((40, 100), "PROTONXONA", fill=(0, 255, 200), font=font)
        
        tmp_img = tempfile.mktemp(suffix=".png")
        img.save(tmp_img)
        
        # 3. Combine image + audio to video
        image_clip = ImageClip(tmp_img, duration=duration)
        image_clip = image_clip.set_audio(audio_clip)
        
        tmp_video = tempfile.mktemp(suffix=".mp4")
        image_clip.write_videofile(tmp_video, fps=24, codec='libx264', audio_codec='aac', logger=None)
        
        return tmp_video, f"SUCCESS! Video duration: {duration:.1f}s"
        
    except Exception as e:
        return None, f"ERROR: {str(e)[:1200]}"

with gr.Blocks() as demo:
    gr.Markdown("# ProtonXona - Script to VIDEO + AUDIO")
    gr.Markdown("Type your script below and get video with voice")
    script_box = gr.Textbox(label="Enter Your Script", lines=6, value="Welcome to ProtonXona. Today we will create amazing videos from text with AI voice.")
    btn = gr.Button("Generate Video with Audio", variant="primary")
    out_video = gr.Video(label="Your Video Result")
    out_status = gr.Textbox(label="Status")
    btn.click(create_video, inputs=script_box, outputs=[out_video, out_status])

demo.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", 10000)))
