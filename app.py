import os
import tempfile
import gradio as gr
from gtts import gTTS
import PIL.Image
# Fix for Pillow 10
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

from moviepy.editor import VideoFileClip, AudioFileClip
from huggingface_hub import InferenceClient

HF_TOKEN = os.getenv("HF_TOKEN")

if not HF_TOKEN:
    print("WARNING: HF_TOKEN not set!")

client = InferenceClient(token=HF_TOKEN)

def generate_real_video(prompt, voice_script):
    try:
        if not HF_TOKEN:
            return None, "FAIL: You must add HF_TOKEN in Render -> Environment Variables. Get free at https://huggingface.co/settings/tokens"
        
        if not prompt or len(prompt.strip()) < 5:
            return None, "Enter video prompt"
        
        if not voice_script or len(voice_script.strip()) < 3:
            voice_script = prompt

        # 1. REAL AI VIDEO - actual motion
        # Model: Wan 1.3B - real text to video
        video_path = client.text_to_video(
            prompt=prompt,
            model="Wan-AI/Wan2.1-T2V-1.3B-Diffusers"
        )
        # video_path is a temp mp4 file from HF

        # 2. REAL VOICE from script
        tmp_audio = tempfile.mktemp(suffix=".mp3")
        gTTS(text=voice_script, lang='en', slow=False).save(tmp_audio)
        audio_clip = AudioFileClip(tmp_audio)

        # 3. Merge video + voice
        video_clip = VideoFileClip(video_path)
        
        # Loop or cut to match voice length
        if video_clip.duration < audio_clip.duration:
            video_clip = video_clip.loop(duration=audio_clip.duration)
        else:
            video_clip = video_clip.subclip(0, audio_clip.duration)

        final_clip = video_clip.set_audio(audio_clip)
        tmp_final = tempfile.mktemp(suffix=".mp4")
        final_clip.write_videofile(tmp_final, fps=16, codec='libx264', audio_codec='aac', logger=None)

        return tmp_final, f"SUCCESS: Real video generated for '{prompt}'"

    except Exception as e:
        return None, f"ERROR: {str(e)}"

with gr.Blocks(title="ProtonXona Real Video") as demo:
    gr.Markdown("# ProtonXona - Real AI Text to Video + Voice")
    gr.Markdown("This generates REAL moving video, not image.")
    
    with gr.Row():
        prompt = gr.Textbox(label="Video Action (what moves)", lines=3, placeholder="Ghanaian woman walking in Accra market, cinematic tracking shot", value="Ghanaian woman walking in Accra market, cinematic tracking shot, 4k")
        voice = gr.Textbox(label="Voiceover Script (what she says)", lines=3, placeholder="Welcome to ProtonXona", value="Welcome to ProtonXona, where stories come alive")
    
    btn = gr.Button("GENERATE REAL VIDEO", variant="primary")
    out_video = gr.Video(label="Real AI Video Result")
    out_status = gr.Textbox(label="Status")
    
    btn.click(fn=generate_real_video, inputs=[prompt, voice], outputs=[out_video, out_status])

demo.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", 10000)))
