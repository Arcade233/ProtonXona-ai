import gradio as gr
import os, tempfile, requests
from gtts import gTTS
import PIL.Image
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS
from moviepy.editor import VideoFileClip, AudioFileClip

HF_TOKEN = os.getenv("HF_TOKEN", "")

def create_action_video(prompt, script):
    try:
        if not prompt or len(prompt) < 5:
            return None, "Type prompt for video action"
        if not script:
            script = prompt

        headers = {"Authorization": f"Bearer {HF_TOKEN}"} if HF_TOKEN else {}
        
        # 1. Generate REAL AI video with action using HF video model
        # Using ModelScope Text-to-Video - works and fast
        API_URL = "https://api-inference.huggingface.co/models/damo-vilab/modelscope-text-to-video-synthesis"
        
        response = requests.post(API_URL, headers=headers, json={"inputs": prompt}, timeout=120)
        
        if response.status_code != 200:
            return None, f"Video Model Error {response.status_code}: {response.text[:800]}. Make sure HF_TOKEN is set in Render Environment!"

        tmp_video_raw = tempfile.mktemp(suffix=".mp4")
        with open(tmp_video_raw, "wb") as f:
            f.write(response.content)

        # 2. Generate voice audio from script
        tmp_audio = tempfile.mktemp(suffix=".mp3")
        tts = gTTS(text=script, lang='en', slow=False)
        tts.save(tmp_audio)
        
        # 3. Merge AI action video + AI voice
        video_clip = VideoFileClip(tmp_video_raw)
        audio_clip = AudioFileClip(tmp_audio)
        
        # Make video length = audio length (loop video if needed)
        if video_clip.duration < audio_clip.duration:
            video_clip = video_clip.loop(duration=audio_clip.duration)
        else:
            video_clip = video_clip.subclip(0, audio_clip.duration)
            
        final_video = video_clip.set_audio(audio_clip)
        tmp_final = tempfile.mktemp(suffix=".mp4")
        final_video.write_videofile(tmp_final, fps=8, codec='libx264', audio_codec='aac', logger=None)
        
        return tmp_final, f"SUCCESS! Action prompt: {prompt}"

    except Exception as e:
        return None, f"ERROR: {str(e)[:1500]}"

with gr.Blocks() as demo:
    gr.Markdown("# ProtonXona - REAL AI ACTION VIDEO + AUDIO")
    prompt_box = gr.Textbox(label="Video Action Prompt (what should happen)", value="Ghanaian woman walking in Accra market, cinematic, 4k, moving camera")
    script_box = gr.Textbox(label="Voiceover Script (what she says)", lines=3, value="Welcome to Ghana, where beauty meets culture. This is ProtonXona.")
    btn = gr.Button("Generate ACTION Video", variant="primary")
    out_video = gr.Video(label="Action Video Result")
    out_status = gr.Textbox(label="Status")
    btn.click(create_action_video, inputs=[prompt_box, script_box], outputs=[out_video, out_status])

demo.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", 10000)))
