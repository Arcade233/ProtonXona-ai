import gradio as gr
import os, tempfile
from gtts import gTTS
import PIL.Image
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
from huggingface_hub import InferenceClient
import textwrap

HF_TOKEN = os.getenv("HF_TOKEN", "")
client = InferenceClient(token=HF_TOKEN) if HF_TOKEN else InferenceClient()

def create_action_video(prompt, script):
    try:
        if not prompt or len(prompt) < 5:
            return None, "Type action prompt"
        if not script:
            script = prompt

        # 1. Audio
        tmp_audio = tempfile.mktemp(suffix=".mp3")
        gTTS(text=script, lang='en').save(tmp_audio)
        audio_clip = AudioFileClip(tmp_audio)
        audio_duration = audio_clip.duration

        # 2. Generate 3 ACTION images for video (to create motion)
        images = []
        for i in range(3):
            # Slight variation to create action
            p = f"{prompt}, frame {i+1}, cinematic action shot, dynamic movement"
            try:
                img = client.text_to_image(p, model="black-forest-labs/FLUX.1-schnell")
                tmp_img = tempfile.mktemp(suffix=".png")
                img.save(tmp_img)
                images.append(tmp_img)
            except Exception as e_img:
                return None, f"Image Gen Error (check HF_TOKEN): {str(e_img)[:800]}"

        # 3. Make ACTION video with zoom/pan effect
        clips = []
        clip_duration = audio_duration / 3
        for img_path in images:
            clip = ImageClip(img_path, duration=clip_duration)
            # Zoom in effect for action feel
            w, h = 720, 1280
            clip = clip.resize((w, h))
            # slight zoom
            clip = clip.resize(lambda t: 1 + 0.1*t)
            clips.append(clip)

        video = concatenate_videoclips(clips, method="compose")
        video = video.set_audio(audio_clip)
        
        tmp_final = tempfile.mktemp(suffix=".mp4")
        video.write_videofile(tmp_final, fps=24, codec='libx264', audio_codec='aac', logger=None)

        return tmp_final, f"SUCCESS! Created action video from: {prompt}"

    except Exception as e:
        return None, f"ERROR: {str(e)[:1500]}"

with gr.Blocks() as demo:
    gr.Markdown("# ProtonXona - REAL ACTION VIDEO")
    prompt_box = gr.Textbox(label="Video Action Prompt", value="Ghanaian woman walking in Accra market, cinematic tracking shot, 4k")
    script_box = gr.Textbox(label="Voiceover Script", value="Welcome to Ghana, where culture and beauty come alive. This is ProtonXona.")
    btn = gr.Button("Generate ACTION Video", variant="primary")
    out_video = gr.Video(label="Action Video Result")
    out_status = gr.Textbox(label="Status")
    btn.click(create_action_video, inputs=[prompt_box, script_box], outputs=[out_video, out_status])

demo.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", 10000)))
