import gradio as gr
import os
import tempfile
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
import textwrap

def create_video(script):
    try:
        if not script or len(script) < 5:
            return None, "Type longer script"
        
        # 1. Make audio
        tmp_audio = tempfile.mktemp(suffix=".mp3")
        tts = gTTS(text=script, lang='en', slow=False)
        tts.save(tmp_audio)
        
        audio_clip = AudioFileClip(tmp_audio)
        duration = audio_clip.duration
        
        # 2. Make image with text
        W, H = 720, 1280
        img = Image.new('RGB', (W, H), color=(10,10,20))
        draw = ImageDraw.Draw(img)
        
        # Wrap text
        wrapped = textwrap.fill(script, width=28)
        try:
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", 42)
        except:
            font = ImageFont.load_default()
            
        draw.multiline_text((50, 400), wrapped, fill=(255,255,255), font=font, spacing=15, align="center")
        
        tmp_img = tempfile.mktemp(suffix=".png")
        img.save(tmp_img)
        
        # 3. Make video
        image_clip = ImageClip(tmp_img, duration=duration)
        image_clip = image_clip.set_audio(audio_clip)
        image_clip = image_clip.resize((W, H))
        
        tmp_video = tempfile.mktemp(suffix=".mp4")
        image_clip.write_videofile(tmp_video, fps=24, codec='libx264', audio_codec='aac', logger=None)
        
        return tmp_video, f"Video created! Duration: {duration:.1f}s"
        
    except Exception as e:
        return None, f"ERROR: {str(e)[:1000]}"

with gr.Blocks() as demo:
    gr.Markdown("# ProtonXona - Script to VIDEO + AUDIO")
    script_box = gr.Textbox(label="Enter Your Script", lines=5, value="Beautiful Ghanaian woman in studio, telling a powerful story about success.")
    btn = gr.Button("Generate Video with Audio")
    out_video = gr.Video(label="Your Video Result")
    out_status = gr.Textbox(label="Status")
    btn.click(create_video, inputs=script_box, outputs=[out_video, out_status])

demo.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", 10000)))
